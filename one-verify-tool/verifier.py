"""
Gemini 验证器核心模块
执行 SheerID 学生身份验证流程
"""

import re
from typing import Dict, Optional, Tuple

# 强制导入反检测模块（无降级方案）
from anti_detect import (
    get_headers,
    get_fingerprint,
    create_session,
    random_delay,
    handle_fraud_rejection,
)
from anti_detect.fingerprint.base import get_seeded_random
from anti_detect.session import warm_session, make_request
from config import SHEERID_API_URL, PROGRAM_ID
from doc_generator import generate_documents, get_mime_type
from stats import stats
from universities import select_university
from utils import generate_name, generate_email, generate_birth_date


class GeminiVerifier:
    """Gemini 学生验证器 - 增强功能版"""

    def __init__(self, url: str, proxy: str = None):
        self.url = url
        self.vid = self._parse_id(url)
        
        # 强制要求 verificationId
        if not self.vid:
            raise ValueError(
                "[验证错误] 无法从 URL 中提取 verificationId。"
                "\n请确保 URL 格式正确，包含 verificationId 参数。"
                "\n示例: https://services.sheerid.com/verify/xxx?verificationId=abc123"
            )
        
        # 使用 verificationId 作为指纹种子，确保同一验证会话中指纹一致
        self.fingerprint = get_fingerprint(self.vid)

        # 使用 curl_cffi 反检测会话（强制要求）
        self.client, self.lib_name, self.impersonate_target = create_session(proxy)
        print(
            f"[信息] 会话已创建，使用 {self.lib_name}（伪装为: {self.impersonate_target}）"
        )

        # 预热会话（模拟真实浏览器在验证前的页面加载行为）
        print("[信息] 预热会话中...")
        warm_session(self.client, program_id=PROGRAM_ID, headers=get_headers())

        self.org = None

    def __del__(self):
        if hasattr(self, "client"):
            self.client.close()

    @staticmethod
    def _parse_id(url: str) -> Optional[str]:
        match = re.search(r"verificationId=([a-f0-9]+)", url, re.IGNORECASE)
        return match.group(1) if match else None

    def _random_delay(self):
        """请求间延迟"""
        random_delay()

    def _request(
        self, method: str, endpoint: str, body: Dict = None
    ) -> Tuple[Dict, int]:
        self._random_delay()
        try:
            headers = get_headers()
            resp = make_request(
                self.client, method, f"{SHEERID_API_URL}{endpoint}",
                json=body, headers=headers
            )
            try:
                parsed = resp.json() if resp.text else {}
            except Exception:
                parsed = {"_text": resp.text}
            return parsed, resp.status_code
        except Exception as e:
            raise Exception(f"请求失败: {e}")

    def _upload_s3(self, url: str, data: bytes, content_type: str = "image/png") -> bool:
        """上传文件到 S3（强制使用 curl_cffi）"""
        resp = self.client.put(
            url, data=data, headers={"Content-Type": content_type}, timeout=60
        )
        if 200 <= resp.status_code < 300:
            return True
        try:
            body = resp.json()
        except Exception:
            body = getattr(resp, "text", str(resp))
        raise Exception(f"S3上传失败: HTTP {resp.status_code} | {body}")

    def check_link(self) -> Dict:
        """检查验证链接是否有效"""
        if not self.vid:
            return {"valid": False, "error": "无效的URL"}

        data, status = self._request("GET", f"/verification/{self.vid}")
        if status != 200:
            return {"valid": False, "error": f"HTTP {status}"}

        step = data.get("currentStep", "")
        # 接受多个有效步骤 - 处理拒绝后的重新上传
        valid_steps = ["collectStudentPersonalInfo", "docUpload", "sso"]
        if step in valid_steps:
            return {"valid": True, "step": step}
        elif step == "success":
            return {"valid": False, "error": "已经验证过了"}
        elif step == "pending":
            return {"valid": False, "error": "已在等待审核中"}
        return {"valid": False, "error": f"无效的步骤: {step}"}

    def verify(self) -> Dict:
        """执行完整验证流程"""
        if not self.vid:
            return {"success": False, "error": "无效的验证URL"}

        try:
            # 首先检查当前步骤
            check_data, check_status = self._request("GET", f"/verification/{self.vid}")
            current_step = (
                check_data.get("currentStep", "") if check_status == 200 else ""
            )

            # 使用 verificationId 作为种子生成一致的学生信息
            rng = get_seeded_random(self.vid)
            
            # 生成学生信息（使用种子随机数确保一致性）
            first, last = generate_name(rng)
            self.org = select_university(rng=rng)
            email = generate_email(first, last, self.org["domain"], rng)
            dob = generate_birth_date(rng)

            print(f"\n   🎓 学生: {first} {last}")
            print(f"   📧 邮箱: {email}")
            print(f"   🏫 学校: {self.org['name']}")
            print(f"   🎂 生日: {dob}")
            print(f"   🔑 验证ID: {self.vid[:20]}...")
            print(f"   📍 起始步骤: {current_step}")

            # 步骤1: 根据大学配置生成所有支持的文档
            doc_types = self.org.get("docs", ["transcript"])
            template = self.org.get("template", "generic")
            print(f"\n   ▶ 步骤 1/5: 生成文档（模板: {template}，类型: {doc_types}）...")
            
            generated_docs = generate_documents(
                doc_types, template, first, last,
                self.org["name"], dob, seed=self.vid
            )
            for fname, doc_data in generated_docs:
                print(f"     📄 {fname}: {len(doc_data) / 1024:.1f} KB")

            # 步骤2: 提交信息（如果已过此步骤则跳过）
            if current_step == "collectStudentPersonalInfo":
                print("   ▶ 步骤 2/5: 提交学生信息...")
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
                    "deviceFingerprintHash": self.fingerprint,
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
                    stats.record(self.org["name"], False)
                    print(f"     ❗ 提交失败: HTTP {status}")
                    print(f"     ❗ 响应内容: {data}")
                    return {
                        "success": False,
                        "error": f"提交失败: {status} - {data}",
                    }

                if data.get("currentStep") == "error":
                    error_ids = data.get("errorIds", [])
                    # 检查欺诈拒绝
                    if "fraudRulesReject" in str(error_ids):
                        handle_fraud_rejection(
                            retry_count=0,
                            error_payload=data,
                            message=f"学校: {self.org['name']}",
                        )
                    stats.record(self.org["name"], False)
                    return {
                        "success": False,
                        "error": f"错误: {error_ids}",
                        "is_fraud_reject": "fraudRulesReject" in str(error_ids),
                    }

                print(f"     📍 当前步骤: {data.get('currentStep')}")
                current_step = data.get("currentStep", "")
            elif current_step in ["docUpload", "sso"]:
                print("   ▶ 步骤 2/5: 跳过（已通过信息提交步骤）...")
            else:
                print(
                    f"   ▶ 步骤 2/5: 未知步骤 '{current_step}'，尝试继续..."
                )

            # 步骤3: 如需要则跳过SSO
            if current_step in ["sso", "collectStudentPersonalInfo"]:
                print("   ▶ 步骤 3/5: 跳过SSO...")
                sso_resp, sso_status = self._request("DELETE", f"/verification/{self.vid}/step/sso")
                if sso_status != 200:
                    raise RuntimeError(f"SSO 跳过失败: HTTP {sso_status}")
                current_step = sso_resp.get("currentStep", "")

            # 步骤4: 批量上传文档（SheerID API 支持 files 数组多文档上传）
            print(f"   ▶ 步骤 4/5: 上传 {len(generated_docs)} 个文档...")
            files_meta = []
            for fname, doc_data in generated_docs:
                mime = get_mime_type(fname)
                files_meta.append({
                    "fileName": fname,
                    "mimeType": mime,
                    "fileSize": len(doc_data),
                })

            data, status = self._request(
                "POST", f"/verification/{self.vid}/step/docUpload", {"files": files_meta}
            )

            # 关键字段为空直接报错
            if not data.get("documents"):
                raise RuntimeError("未获取到文档上传信息")
            
            # 逐个上传到对应的 uploadUrl
            for i, doc_info in enumerate(data["documents"]):
                upload_url = doc_info.get("uploadUrl")
                if not upload_url:
                    raise RuntimeError(f"未获取到第 {i + 1} 个文档的上传URL")
                mime = doc_info.get("mimeType", "image/png")
                self._upload_s3(upload_url, generated_docs[i][1], content_type=mime)
                print(f"     ✅ 文档 {i + 1}/{len(generated_docs)} 上传成功: {generated_docs[i][0]}")

            # 步骤5: 完成文档上传
            print("   ▶ 步骤 5/5: 完成上传...")
            data, status = self._request(
                "POST", f"/verification/{self.vid}/step/completeDocUpload"
            )
            final_step = data.get("currentStep", "unknown")
            print(f"     📍 最终步骤: {final_step}")

            if final_step == "success":
                stats.record(self.org["name"], True)
                return {
                    "success": True,
                    "message": "即时验证成功！无需人工审核。",
                    "student": f"{first} {last}",
                    "email": email,
                    "school": self.org["name"],
                    "redirectUrl": data.get("redirectUrl"),
                }
            elif final_step == "pending":
                # pending 状态不记录为失败（等待人工审核）
                return {
                    "success": False,
                    "pending": True,
                    "message": "文档已提交等待审核。请等待24-48小时获取结果。",
                    "student": f"{first} {last}",
                    "email": email,
                    "school": self.org["name"],
                }
            elif final_step in ["rejected", "error"]:
                stats.record(self.org["name"], False)
                error_ids = data.get("errorIds", [])
                return {
                    "success": False,
                    "error": f"被拒绝: {error_ids}"
                    if error_ids
                    else "文档被拒绝",
                }
            else:
                return {
                    "success": False,
                    "pending": True,
                    "message": f"未知状态: {final_step}。请手动检查。",
                    "student": f"{first} {last}",
                    "email": email,
                    "school": self.org["name"],
                }

        except Exception as e:
            if self.org:
                stats.record(self.org["name"], False)
            return {"success": False, "error": str(e)}
