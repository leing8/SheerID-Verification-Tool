"""
Gemini 验证器核心模块
执行 SheerID 学生身份验证流程
"""

import random
import re
import sys
from typing import Dict, Optional, Tuple

try:
    import httpx
except ImportError:
    print("❌ 错误: 需要安装 httpx。安装命令: pip install httpx")
    sys.exit(1)

from config import SHEERID_API_URL, PROGRAM_ID
from stats import stats
from universities import select_university
from utils import generate_name, generate_email, generate_birth_date
from doc_generator import generate_transcript, generate_student_id

# 尝试导入反检测模块
try:
    from anti_detect import (
        get_headers,
        get_fingerprint,
        create_session,
        random_delay,
        handle_fraud_rejection,
    )

    HAS_ANTI_DETECT = True
except ImportError:
    HAS_ANTI_DETECT = False
    print("[警告] 反检测模块未找到，使用基础请求头")
    print("[警告] 没有反检测模块，被检测风险极高！")


class GeminiVerifier:
    """Gemini 学生验证器 - 增强功能版"""

    def __init__(self, url: str, proxy: str = None):
        self.url = url
        self.vid = self._parse_id(url)
        self.fingerprint = get_fingerprint() if HAS_ANTI_DETECT else self._basic_fingerprint()

        # 使用增强版反检测会话
        if HAS_ANTI_DETECT:
            self.client, self.lib_name, self.impersonate_target = create_session(proxy)
            print(
                f"[信息] 会话已创建，使用 {self.lib_name}（伪装为: {self.impersonate_target}）"
            )
        else:
            proxy_url = None
            if proxy:
                if not proxy.startswith("http"):
                    proxy = f"http://{proxy}"
                proxy_url = proxy
            self.client = httpx.Client(timeout=30, proxy=proxy_url)
            self.lib_name = "httpx"

        self.org = None

    def __del__(self):
        if hasattr(self, "client"):
            self.client.close()

    @staticmethod
    def _basic_fingerprint() -> str:
        """基础指纹生成（无反检测模块时使用）"""
        import hashlib
        import time
        components = [str(time.time()), str(random.random())]
        return hashlib.md5("|".join(components).encode()).hexdigest()

    @staticmethod
    def _parse_id(url: str) -> Optional[str]:
        match = re.search(r"verificationId=([a-f0-9]+)", url, re.IGNORECASE)
        return match.group(1) if match else None

    def _random_delay(self):
        """请求间延迟"""
        if HAS_ANTI_DETECT:
            random_delay()
        else:
            import time
            from config import MIN_DELAY, MAX_DELAY
            time.sleep(random.randint(MIN_DELAY, MAX_DELAY) / 1000)

    def _request(
        self, method: str, endpoint: str, body: Dict = None
    ) -> Tuple[Dict, int]:
        self._random_delay()
        try:
            # 如果可用则使用反检测请求头
            headers = (
                get_headers(for_sheerid=True)
                if HAS_ANTI_DETECT
                else {"Content-Type": "application/json"}
            )
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
        # 不同会话实现接受不同的关键字参数
        # 尝试多种变体以最大化兼容性（curl_cffi、httpx、requests）
        attempts = [
            lambda: self.client.put(
                url, content=data, headers={"Content-Type": "image/png"}, timeout=60
            ),
            lambda: self.client.put(
                url, data=data, headers={"Content-Type": "image/png"}, timeout=60
            ),
            lambda: self.client.request(
                "PUT", url, data=data, headers={"Content-Type": "image/png"}, timeout=60
            ),
        ]

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
                    print(f"     ❗ S3上传失败: HTTP {resp.status_code} | {body}")
                    return False
                else:
                    if resp:
                        return True
                    return False
            except TypeError as e:
                last_exc = e
                continue
            except Exception as e:
                last_exc = e
                continue

        print(f"     ❗ S3上传尝试全部失败。最后错误: {last_exc}")
        return False

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

            # 生成学生信息
            first, last = generate_name()
            self.org = select_university()
            email = generate_email(first, last, self.org["domain"])
            dob = generate_birth_date()

            print(f"\n   🎓 学生: {first} {last}")
            print(f"   📧 邮箱: {email}")
            print(f"   🏫 学校: {self.org['name']}")
            print(f"   🎂 生日: {dob}")
            print(f"   🔑 验证ID: {self.vid[:20]}...")
            print(f"   📍 起始步骤: {current_step}")

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
            print(f"     📄 文件大小: {len(doc) / 1024:.1f} KB")

            # 步骤2: 提交信息（如果已过此步骤则跳过）
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
                        if HAS_ANTI_DETECT:
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
                print("   ▶ 步骤 2/3: 跳过（已通过信息提交步骤）...")
            else:
                print(
                    f"   ▶ 步骤 2/3: 未知步骤 '{current_step}'，尝试继续..."
                )

            # 步骤3: 如需要则跳过SSO
            if current_step in ["sso", "collectStudentPersonalInfo"]:
                print("   ▶ 步骤 3/4: 跳过SSO...")
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
                return {"success": False, "error": "未获取到上传URL"}

            upload_url = data["documents"][0].get("uploadUrl")
            if not self._upload_s3(upload_url, doc):
                stats.record(self.org["name"], False)
                return {"success": False, "error": "上传失败"}

            print("     ✅ 文档上传成功！")

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
