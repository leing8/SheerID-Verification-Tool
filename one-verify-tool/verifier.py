"""
GeminiVerifier - 增强版 Gemini 学生验证器
"""

import random
import re
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

# 添加 device_fingerprint 模块路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    from device_fingerprint import DeviceIdentityFactory
except ImportError:
    print("❌ 致命错误: device_fingerprint 模块未找到")
    print("请确保 device_fingerprint/ 目录与 one-verify-tool/ 同级")
    sys.exit(1)

from config import PROGRAM_ID, SHEERID_API_URL
from documents import generate_student_id, generate_transcript
from generators import (
    generate_birth_date,
    generate_email,
    generate_name,
    random_delay,
)
from stats import stats
from universities import select_university


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
        self.identity = factory.create(self.vid, device_type="desktop")
        print(f"[信息] 设备身份: {self.identity.device.brand} {self.identity.device.model}")

        # 2. 基于 DeviceIdentity 的 Chrome 版本创建 TLS 会话
        #    确保 JA3/JA4 指纹 ↔ HTTP 请求头 版本一致
        chrome_major = self.identity.chrome_version.split(".")[0]
        impersonate_ver = f"chrome{chrome_major}"

        from anti_detect import create_session
        self.client, self.lib_name, self.impersonate_target = create_session(
            proxy, impersonate=impersonate_ver
        )
        print(f"[信息] TLS 模拟: {self.impersonate_target} (JA3/JA4 = Chrome {chrome_major})")

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

    def _upload_s3(self, url: str, data: bytes) -> bool:
        # 不同 HTTP 库接受不同的参数名，尝试多种方式以最大化兼容性 (curl_cffi, httpx, requests)
        attempts = []
        # 第一种: httpx 签名
        attempts.append(
            lambda: self.client.put(
                url, content=data, headers={"Content-Type": "image/png"}, timeout=60
            )
        )
        # 第二种: requests 签名
        attempts.append(
            lambda: self.client.put(
                url, data=data, headers={"Content-Type": "image/png"}, timeout=60
            )
        )
        # 第三种: 通用 request 方法
        attempts.append(
            lambda: self.client.request(
                "PUT", url, data=data, headers={"Content-Type": "image/png"}, timeout=60
            )
        )

        last_exc = None
        for fn in attempts:
            try:
                resp = fn()
                if hasattr(resp, "status_code"):
                    if 200 <= resp.status_code < 300:
                        return True
                    try:
                        body = resp.json()
                    except Exception:
                        body = getattr(resp, "text", str(resp))
                    print(f"     ❗ S3 上传失败: HTTP {resp.status_code} | {body}")
                    return False
                else:
                    # 响应非标准对象，有值则视为成功
                    if resp:
                        return True
                    return False
            except TypeError as e:
                last_exc = e
                continue
            except Exception as e:
                last_exc = e
                continue

        print(f"     ❗ S3 上传失败，最后错误: {last_exc}")
        return False

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
        return {"valid": False, "error": f"无效步骤: {step}"}

    def verify(self) -> Dict:
        """运行完整验证流程"""
        if not self.vid:
            return {"success": False, "error": "无效的验证 URL"}

        try:
            # 先检查当前步骤
            check_data, check_status = self._request("GET", f"/verification/{self.vid}")
            current_step = (
                check_data.get("currentStep", "") if check_status == 200 else ""
            )

            # 生成信息
            first, last = generate_name()
            self.org = select_university()
            email = generate_email(first, last, self.org["domain"])
            dob = generate_birth_date()

            print(f"\n   🎓 学生: {first} {last}")
            print(f"   📧 邮箱: {email}")
            print(f"   🏫 学校: {self.org['name']}")
            print(f"   🎂 出生日期: {dob}")
            print(f"   🔑 ID: {self.vid[:20]}...")
            print(f"   📍 当前步骤: {current_step}")

            # 步骤1: 生成文档
            doc_type = "transcript" if random.random() < 0.7 else "id_card"
            if doc_type == "transcript":
                print("\n   ▶ 步骤 1/3: 生成学术成绩单...")
                doc = generate_transcript(first, last, self.org["name"], dob)
                filename = "transcript.png"
            else:
                print("\n   ▶ 步骤 1/3: 生成学生证...")
                doc = generate_student_id(first, last, self.org["name"])
                filename = "student_card.png"
            print(f"     📄 大小: {len(doc) / 1024:.1f} KB")

            # 步骤2: 提交信息 (已过此步骤则跳过)
            if current_step == "collectStudentPersonalInfo":
                print("   ▶ 步骤 2/3: 提交学生信息...")
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
                        if HAS_ANTI_DETECT:
                            handle_fraud_rejection(
                                retry_count=0,
                                error_payload=data,
                                message=f"University: {self.org['name']}",
                            )
                    stats.record(self.org["name"], False)
                    return {
                        "success": False,
                        "error": f"Error: {error_ids}",
                        "is_fraud_reject": "fraudRulesReject" in str(error_ids),
                    }

                print(f"     📍 当前步骤: {data.get('currentStep')}")
                current_step = data.get("currentStep", "")
            elif current_step in ["docUpload", "sso"]:
                print("   ▶ 步骤 2/3: 跳过 (已过信息提交)...")
            else:
                print(
                    f"   ▶ 步骤 2/3: 未知步骤 '{current_step}'，尝试继续..."
                )

            # 步骤3: 跳过 SSO (如需要)
            if current_step in ["sso", "collectStudentPersonalInfo"]:
                print("   ▶ 步骤 3/4: 跳过 SSO...")
                self._request("DELETE", f"/verification/{self.vid}/step/sso")

            # 步骤4: 上传文档
            print("   ▶ 步骤 4/5: 上传文档...")
            upload_body = {
                "files": [
                    {
                        "fileName": filename,
                        "mimeType": "image/png",
                        "fileSize": len(doc),
                    }
                ]
            }
            data, status = self._request(
                "POST", f"/verification/{self.vid}/step/docUpload", upload_body
            )

            if not data.get("documents"):
                stats.record(self.org["name"], False)
                return {"success": False, "error": "没有上传 URL"}

            upload_url = data["documents"][0].get("uploadUrl")
            if not self._upload_s3(upload_url, doc):
                stats.record(self.org["name"], False)
                return {"success": False, "error": "上传失败"}

            print("     ✅ 文档已上传!")

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
                    "message": "已立即验证! 无需审核。",
                    "student": f"{first} {last}",
                    "email": email,
                    "school": self.org["name"],
                    "redirectUrl": data.get("redirectUrl"),
                }
            elif final_step == "pending":
                return {
                    "success": False,
                    "pending": True,
                    "message": "文档已提交审核，等待 24-48 小时结果。",
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
                    "message": f"未知状态: {final_step}，请手动检查。",
                    "student": f"{first} {last}",
                    "email": email,
                    "school": self.org["name"],
                }

        except Exception as e:
            if self.org:
                stats.record(self.org["name"], False)
            return {"success": False, "error": str(e)}
