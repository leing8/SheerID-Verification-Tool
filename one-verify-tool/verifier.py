"""
GeminiVerifier - 增强版 Gemini 学生验证器
"""

import re
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

# 添加 common 公共模块路径 (device_fingerprint_factory, proxy_checker, student_document_factory)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))
try:
    from device_fingerprint_factory import DeviceIdentityFactory
except ImportError:
    print("❌ 致命错误: device_fingerprint_factory 模块未找到")
    print("请确保 common/device_fingerprint_factory/ 目录存在")
    sys.exit(1)

from config import PROGRAM_ID, SHEERID_API_URL
from anti_detect.session import random_delay
from student_document_factory import StudentInfoFactory

# ── 官方定义的所有步骤 (https://developer.sheerid.com/concepts#steps) ──────────
# collectStudentPersonalInfo : 填写个人信息（第一步）
# docUpload                  : 上传证明文件（即时失败后触发）
# sso                        : SSO 登录（部分 Program 启用，非所有流程有此步骤）
# pending                    : 文档提交成功，等待人工/自动审核
# success                    : 验证通过
# error                      : 数据错误（可恢复，可重试当前步骤）
# attemptsExhausted          : 文档连续拒绝 3 次，验证彻底失败（不可恢复）
KNOWN_STEPS = frozenset({
    "collectStudentPersonalInfo",
    "docUpload",
    "sso",
    "pending",
    "success",
    "error",
    "attemptsExhausted",
})


class GeminiVerifier:
    """增强版 Gemini 学生验证器"""

    def __init__(self, url: str, proxy: str = None):
        self.url = url
        self.vid = self._parse_id(url)

        if not self.vid:
            print("❌ 无法解析 verificationId")
            sys.exit(1)

        # 1. 创建 DeviceIdentity
        factory = DeviceIdentityFactory()
        self.identity = factory.create(self.vid)
        print(f"[信息] 设备身份: {self.identity.device.brand} {self.identity.device.model}")

        # 2. 基于 DeviceIdentity 的 impersonate_key 创建 TLS 会话
        #    确保 JA3/JA4 指纹 ↔ HTTP 请求头 ↔ sec-ch-ua 版本三者一致
        from anti_detect import create_session
        from anti_detect.session import warm_session
        from proxy_checker import ProxyChecker

        self.client, self.lib_name, self.impersonate_target = create_session(
            proxy, impersonate=self.identity.impersonate_key
        )
        print(f"[信息] TLS 模拟: {self.impersonate_target} (Chrome {self.identity.chrome_version})")

        # 3. 异步代理 IP 地理检测 (不阻塞主线程)
        if proxy:
            ProxyChecker().check_async(self.client, expected_country="US")

        # 4. 会话预热 (官方文档序列: theme → verification → org search)
        warm_session(
            self.client,
            program_id=PROGRAM_ID,
            verification_id=self.vid,
            headers=self.identity.get_headers(for_sheerid=True),
        )
        print("[信息] 会话已预热 (theme → verification → organization)")

        self.org = None

    def __del__(self):
        if hasattr(self, "client"):
            self.client.close()

    @staticmethod
    def _parse_id(url: str) -> Optional[str]:
        match = re.search(r"verificationId=([a-f0-9]+)", url, re.IGNORECASE)
        return match.group(1) if match else None

    def _request(
        self, method: str, endpoint: str, body: Dict = None
    ) -> Tuple[Dict, int]:
        random_delay()
        try:
            # 使用 DeviceIdentity 生成一致请求头
            headers = self.identity.get_headers(for_sheerid=True)
            resp = self.client.request(
                method, f"{SHEERID_API_URL}{endpoint}", json=body, headers=headers
            )
            try:
                parsed = resp.json() if resp.text else {}
            except Exception:
                parsed = {"_text": resp.text}
            return parsed, resp.status_code
        except Exception as e:
            raise Exception(f"请求失败: {e}")

    def _upload_s3(self, url: str, data: bytes, mime_type: str = "image/png") -> bool:
        """S3 文档上传 (curl_cffi)

        官方文档要求同时发送 Content-Type 和 Content-Length，
        缺少 Content-Length 可能导致 S3 预签名 URL 返回 403。
        参考: https://developer.sheerid.com/rest-api#operation/submitDocumentReviewFilesWithoutToken
        """
        try:
            resp = self.client.put(
                url,
                data=data,
                headers={
                    "Content-Type": mime_type,
                    "Content-Length": str(len(data)),
                },
                timeout=60,
            )
            if 200 <= resp.status_code < 300:
                return True
            print(f"     ❗ S3 上传失败: HTTP {resp.status_code}")
            return False
        except Exception as e:
            print(f"     ❗ S3 上传失败: {e}")
            return False

    def _poll_result(
        self,
        status_url: Optional[str] = None,
        max_wait_minutes: int = 60,
        interval_seconds: int = 30,
    ) -> Dict:
        """轮询文档审查结果

        官方文档说明:
          - pending 状态期间，使用 GET /verification/{id} 查询 currentStep
          - 响应中的 statusUrl 字段即为轮询 URL
          - 直到 currentStep 不再是 pending 为止
        参考: https://developer.sheerid.com/tutorials/apis/api-walkthrough#get-verification-details

        Args:
            status_url:          优先使用官方 statusUrl，否则自动构造
            max_wait_minutes:    最长等待时间（默认 60 分钟）
            interval_seconds:    每次轮询间隔秒数（默认 30 秒）

        Returns:
            与 verify() 格式一致的结果字典
        """
        # 优先使用官方返回的 statusUrl，否则构造标准 GET 端点
        poll_endpoint = f"/verification/{self.vid}"

        max_attempts = int((max_wait_minutes * 60) / interval_seconds)
        print(f"\n   🔄 开始轮询文档审查结果 (最长 {max_wait_minutes} 分钟, 间隔 {interval_seconds} 秒)")
        print(f"   📡 轮询端点: {SHEERID_API_URL}{poll_endpoint}")

        for attempt in range(1, max_attempts + 1):
            time.sleep(interval_seconds)

            try:
                data, status = self._request("GET", poll_endpoint)
            except Exception as e:
                print(f"   ⚠️  [{attempt}/{max_attempts}] 轮询请求失败: {e}, 继续等待...")
                continue

            current_step = data.get("currentStep", "pending")
            print(f"   ⏳ [{attempt}/{max_attempts}] currentStep: {current_step}")

            if current_step == "pending":
                # 审核尚未完成，继续等待
                continue

            # ── 审核完成，返回最终结果 ──────────────────────────────────────
            if current_step == "success":
                return {
                    "success": True,
                    "message": "文档审查通过! 验证成功。",
                    "redirectUrl": data.get("redirectUrl"),
                    "rewardCode": data.get("rewardCode"),
                }
            elif current_step == "docUpload":
                # 极少数情况: 审核后要求重新上传（首次拒绝，尚有剩余机会）
                error_ids = data.get("errorIds", [])
                return {
                    "success": False,
                    "needs_reupload": True,
                    "error": f"文档被拒绝，请重新上传。错误: {error_ids}",
                }
            elif current_step == "attemptsExhausted":
                # 官方定义: 3 次文档拒绝后触发，不可恢复
                return {
                    "success": False,
                    "attempts_exhausted": True,
                    "error": "文档连续被拒绝 3 次，验证彻底失败 (attemptsExhausted)。需重新开始新的验证。",
                }
            elif current_step == "error":
                error_ids = data.get("errorIds", [])
                system_msg = data.get("systemErrorMessage", "")
                return {
                    "success": False,
                    "error": f"验证出错: {error_ids}",
                    "system_message": system_msg,
                }
            else:
                # 未知步骤，记录但也停止轮询
                return {
                    "success": False,
                    "unknown": True,
                    "message": f"轮询结束，未知状态: {current_step}",
                }

        # 超时退出
        return {
            "success": False,
            "pending": True,
            "timed_out": True,
            "message": f"轮询已超时 ({max_wait_minutes} 分钟)，审核仍在进行中。请稍后手动查看邮件确认结果。",
        }

    def check_link(self) -> Dict:
        """检查验证链接是否有效"""
        if not self.vid:
            return {"valid": False, "error": "无效的 URL"}

        data, status = self._request("GET", f"/verification/{self.vid}")
        if status != 200:
            return {"valid": False, "error": f"HTTP {status}"}

        step = data.get("currentStep", "")
        # 接受多个有效步骤 - 处理拒绝后重新上传
        valid_steps = ["collectStudentPersonalInfo", "docUpload", "sso"]
        if step in valid_steps:
            return {"valid": True, "step": step}
        elif step == "success":
            return {"valid": False, "error": "已验证通过"}
        elif step == "pending":
            return {"valid": False, "error": "已在审核中"}
        elif step == "attemptsExhausted":
            return {"valid": False, "error": "文档已被拒绝 3 次，验证彻底失败，需重新开始"}
        elif step == "error":
            error_ids = data.get("errorIds", [])
            return {"valid": False, "error": f"验证出错: {error_ids}"}
        return {"valid": False, "error": f"无效步骤: {step}"}

    def verify(self) -> Dict:
        """运行完整验证流程

        官方文档定义的标准流程:
          1. GET /verification/{id}           → 获取 currentStep
          2. POST /step/collectStudentPersonalInfo → 提交个人信息
             → 返回 currentStep: success (即时通过) 或 docUpload (需上传)
          3. DELETE /step/sso                 → 可选，跳过 SSO
          4. POST /step/docUpload             → 提交文件信息，S3 上传文件
             → 直接返回 currentStep: pending 或 success
             ⚠️  官方文档中 **不存在** completeDocUpload 步骤
        """
        if not self.vid:
            return {"success": False, "error": "无效的验证 URL"}

        try:
            # 先检查当前步骤
            check_data, check_status = self._request("GET", f"/verification/{self.vid}")
            current_step = (
                check_data.get("currentStep", "") if check_status == 200 else ""
            )

            # 生成信息（基于 verificationId 确定性生成）
            factory = StudentInfoFactory()
            student_info = factory.create(self.vid)
            first = student_info.first_name
            last  = student_info.last_name
            self.org = student_info.university
            email = student_info.email
            dob   = student_info.birth_date

            print(f"\n   🎓 学生: {first} {last}")
            print(f"   📧 邮箱: {email}")
            print(f"   🏫 学校: {self.org['name']}")
            print(f"   📚 专业: {student_info.program}")
            print(f"   🎂 出生日期: {dob}")
            print(f"   🔑 ID: {self.vid[:20]}...")
            print(f"   📍 当前步骤: {current_step}")

            # 步骤1: 生成文档（工厂按 vid 确定性选好文档类型和数量，2–3 份）
            documents = student_info.documents
            print(f"\n   ▶ 步骤 1/4: 生成文档 ({len(documents)} 份)...")
            for doc_name, doc_bytes in documents:
                print(f"     📄 {doc_name}: {len(doc_bytes) / 1024:.1f} KB")

            # 模拟用户填写表单 (人类在这里会花 2-5 秒)
            random_delay(2000, 5000)

            # 步骤2: 提交信息 (已过此步骤则跳过)
            if current_step == "collectStudentPersonalInfo":
                print("   ▶ 步骤 2/4: 提交学生信息...")
                body = {
                    "firstName": first,
                    "lastName": last,
                    "birthDate": dob,
                    "email": email,
                    "phoneNumber": "",
                    "organization": {
                        "id": self.org["id"],
                        "idExtended": self.org["idExtended"],
                        "name": self.org["name"],
                    },
                    "deviceFingerprintHash": self.identity.fingerprint_hash,
                    "locale": "en-US",
                    "metadata": {
                        "marketConsentValue": False,
                        "verificationId": self.vid,
                        "refererUrl": f"https://services.sheerid.com/verify/{PROGRAM_ID}/?verificationId={self.vid}",
                        "flags": '{"collect-info-step-email-first":"default","doc-upload-considerations":"default","doc-upload-may24":"default","doc-upload-redesign-use-legacy-message-keys":false,"docUpload-assertion-checklist":"default","font-size":"default","include-cvec-field-france-student":"not-labeled-optional"}',
                        "submissionOptIn": "By submitting the personal information above, I acknowledge that my personal information is being collected under the privacy policy of the business from which I am seeking a discount",
                    },
                }

                data, status = self._request(
                    "POST",
                    f"/verification/{self.vid}/step/collectStudentPersonalInfo",
                    body,
                )

                if status != 200:
                    print(f"     ❗ 提交失败: HTTP {status}")
                    print(f"     ❗ 响应内容: {data}")
                    return {
                        "success": False,
                        "error": f"提交失败: {status} - {data}",
                    }

                if data.get("currentStep") == "error":
                    error_ids = data.get("errorIds", [])
                    system_msg = data.get("systemErrorMessage", "")
                    if system_msg:
                        print(f"     ❗ SheerID systemErrorMessage: {system_msg}")
                    # fraudRulesReject 是 SheerID 官方定义的不可恢复错误，
                    # 不得对同一 verificationId 重试。
                    if "fraudRulesReject" in str(error_ids):
                        from anti_detect import handle_fraud_rejection
                        handle_fraud_rejection(
                            error_payload=data,
                            message=f"Stage: collectStudentPersonalInfo | University: {self.org['name']}",
                        )
                    return {
                        "success": False,
                        "error": f"Error: {error_ids}",
                        "system_message": system_msg,
                    }

                if data.get("currentStep") == "success":
                    # 即时验证通过 (无需文档上传)
                    return {
                        "success": True,
                        "message": "即时验证通过! 无需文档审核。",
                        "student": f"{first} {last}",
                        "email": email,
                        "school": self.org["name"],
                        "redirectUrl": data.get("redirectUrl"),
                        "rewardCode": data.get("rewardCode"),
                    }

                # 使用提交后返回的最新步骤，决定是否需要跳过 SSO
                current_step = data.get("currentStep", "")
                print(f"     📍 当前步骤: {current_step}")

            elif current_step in ["docUpload", "sso"]:
                print("   ▶ 步骤 2/4: 跳过 (已过信息提交)...")
            elif current_step == "attemptsExhausted":
                return {
                    "success": False,
                    "attempts_exhausted": True,
                    "error": "文档连续被拒绝 3 次，验证彻底失败 (attemptsExhausted)。需重新开始新的验证。",
                }
            else:
                # 记录未知步骤，但尝试继续（避免因步骤名变更而中断）
                if current_step and current_step not in KNOWN_STEPS:
                    print(f"   ⚠️  步骤 2/4: 未知步骤 '{current_step}'，尝试继续...")
                else:
                    print(f"   ▶ 步骤 2/4: 跳过 (当前步骤: {current_step})")

            # 步骤3: 跳过 SSO (仅当服务端明确返回 sso 步骤时才执行)
            if current_step == "sso":
                print("   ▶ 步骤 3/4: 跳过 SSO...")
                random_delay(500, 1500)  # 短暂停顿，模拟点击"跳过"
                sso_data, _ = self._request("DELETE", f"/verification/{self.vid}/step/sso")
                current_step = sso_data.get("currentStep", current_step)
                print(f"     📍 SSO 后步骤: {current_step}")
            else:
                print("   ▶ 步骤 3/4: 无需跳过 SSO")

            # 模拟用户选择文件 (1.5-4 秒)
            random_delay(1500, 4000)

            # 步骤4: 上传文档
            # 官方 API 流程 (https://developer.sheerid.com/tutorials/apis/api-walkthrough#doc-upload):
            #   步骤 4a: POST /step/docUpload  → 返回 documents[].uploadUrl 和 submissionUrl
            #   步骤 4b: PUT  <uploadUrl>      → 将文件内容上传到 S3
            #   步骤 4c: POST <submissionUrl>  → 通知 SheerID 所有文件已传完
            #              服务端返回最终 currentStep: pending 或 success
            print(f"   ▶ 步骤 4/4: 上传文档 ({len(documents)} 份)...")
            upload_body = {
                "files": [
                    {
                        "fileName": doc_name,
                        "mimeType": "image/png",
                        "fileSize": len(doc_bytes),
                    }
                    for doc_name, doc_bytes in documents
                ]
            }
            data, status = self._request(
                "POST", f"/verification/{self.vid}/step/docUpload", upload_body
            )

            if status != 200:
                return {"success": False, "error": f"docUpload 请求失败: HTTP {status} - {data}"}

            if not data.get("documents"):
                return {"success": False, "error": "没有上传 URL (documents 字段为空)"}

            # 提取 submissionUrl（步骤 4c 需要用到）和各文档的 uploadUrl
            # 官方文档: docUpload 响应中同时包含 documents[].uploadUrl 和 submissionUrl
            submission_url = data.get("submissionUrl", "")

            # 步骤 4b: 逐一上传每份文档到对应的 S3 预签名 URL
            # 官方文档: response.documents 顺序与 request.files 一致
            upload_slots = data["documents"]
            for i, ((doc_name, doc_bytes), slot) in enumerate(zip(documents, upload_slots)):
                upload_url = slot.get("uploadUrl")
                if not upload_url:
                    return {"success": False, "error": f"文档 {i + 1} ({doc_name}) 缺少上传 URL"}
                print(f"     📤 上传文档 {i + 1}/{len(documents)}: {doc_name}")
                if not self._upload_s3(upload_url, doc_bytes):
                    return {"success": False, "error": f"文档 {i + 1} ({doc_name}) 上传失败"}
                print(f"     ✅ 文档 {i + 1} 已上传!")
                if i < len(documents) - 1:
                    random_delay(800, 2000)  # 模拟用户逐个选择文件的间隔

            # 步骤 4c: 通知 SheerID 所有文件已上传完毕，获取最终审核状态
            # 官方文档: "The response will also contain a submission URL,
            #            to be used after all files have been uploaded."
            # submissionUrl 由 SheerID 动态返回，通常是 /step/completeDocUpload 或同等端点
            random_delay(1000, 2000)  # 模拟用户点击提交按钮
            print(f"     📬 通知 SheerID 上传完成...")

            if submission_url:
                # 使用官方返回的完整 submissionUrl（直接调用，不走 _request 的端点前缀）
                try:
                    headers = self.identity.get_headers(for_sheerid=True)
                    resp = self.client.request(
                        "POST", submission_url, json=None, headers=headers
                    )
                    try:
                        submit_data = resp.json() if resp.text else {}
                    except Exception:
                        submit_data = {"_text": resp.text}
                    data = submit_data  # 用最终响应覆盖
                    print(f"     📡 submissionUrl 状态: HTTP {resp.status_code}")
                except Exception as e:
                    print(f"     ⚠️  submissionUrl 请求失败: {e}, 使用 docUpload 响应作为结果")
            else:
                # 无 submissionUrl 时：回退到 GET 当前状态（避免停在 docUpload）
                print(f"     ⚠️  响应中无 submissionUrl，查询当前状态...")
                fallback_data, _ = self._request("GET", f"/verification/{self.vid}")
                if fallback_data.get("currentStep"):
                    data = fallback_data

            # ── 解析最终状态 ────────────────────────────────────────────────────
            final_step = data.get("currentStep", "unknown")
            status_url = data.get("statusUrl")
            print(f"     📍 最终步骤: {final_step}")

            if final_step == "success":
                return {
                    "success": True,
                    "message": "即时验证通过! 无需审核。",
                    "student": f"{first} {last}",
                    "email": email,
                    "school": self.org["name"],
                    "redirectUrl": data.get("redirectUrl"),
                    "rewardCode": data.get("rewardCode"),
                }
            elif final_step == "pending":
                return {
                    "success": False,
                    "pending": True,
                    "message": "文档已提交审核，等待结果。",
                    "student": f"{first} {last}",
                    "email": email,
                    "school": self.org["name"],
                    "status_url": status_url,
                }
            elif final_step == "attemptsExhausted":
                # 官方定义: 3 次文档拒绝后触发，不可恢复
                return {
                    "success": False,
                    "attempts_exhausted": True,
                    "error": "文档连续被拒绝 3 次，验证彻底失败 (attemptsExhausted)。需重新开始新的验证。",
                    "student": f"{first} {last}",
                    "email": email,
                    "school": self.org["name"],
                }
            elif final_step in ["rejected", "error"]:
                error_ids = data.get("errorIds", [])
                system_msg = data.get("systemErrorMessage", "")
                if system_msg:
                    print(f"     ❗ SheerID systemErrorMessage: {system_msg}")
                # fraudRulesReject 可能在文档提交后返回，同样为不可恢复错误
                if "fraudRulesReject" in str(error_ids):
                    from anti_detect import handle_fraud_rejection
                    handle_fraud_rejection(
                        error_payload=data,
                        message=f"Stage: docUpload | University: {self.org['name']}",
                    )
                return {
                    "success": False,
                    "error": f"被拒绝: {error_ids}" if error_ids else "文档被拒绝",
                    "system_message": system_msg,
                }
            else:
                return {
                    "success": False,
                    "unknown": True,
                    "message": f"未知状态: {final_step}，请手动检查。",
                    "student": f"{first} {last}",
                    "email": email,
                    "school": self.org["name"],
                }

        except Exception as e:
            return {"success": False, "error": str(e)}
