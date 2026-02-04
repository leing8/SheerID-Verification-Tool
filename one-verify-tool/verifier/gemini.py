"""
Gemini 验证器模块 - SheerID 学生验证核心逻辑

包含:
- GeminiVerifier: 完整的 Gemini 学生验证流程
"""

import re
import random
from typing import Dict, Optional, Tuple, List

try:
    import httpx
except ImportError:
    print("❌ 错误: 需要 httpx。请安装: pip install httpx")
    import sys
    sys.exit(1)

from core import (
    PROGRAM_ID,
    SHEERID_API_URL,
    HAS_CURL_CFFI,
    BrowserProfile,
    create_new_profile,
    reset_profile,
    get_headers_with_profile,
    get_fingerprint,
    get_full_fingerprint,
    get_matched_ua_for_impersonate,
    get_proxy_country,
    SessionManager,
    create_session,
    warm_session_enhanced,
    handle_fraud_rejection,
    random_delay,
    interaction_delay,
    reading_delay,
)
from generator import (
    generate_name,
    generate_email,
    generate_birth_date,
    generate_transcript,
    generate_harvard_transcript,
    generate_student_id,
    generate_enrollment_letter,
)
from stats import stats
from core.debug_logger import debug_logger
from core.verification_store import verification_store
from .university import select_university, fraud_tracker, validate_university_ip_match


class GeminiVerifier:
    """
    Gemini 学生验证器 - 实现完整的 SheerID 验证流程
    
    验证流程:
    1. 检查验证链接有效性
    2. 生成虚拟学生信息
    3. 提交学生个人信息
    4. 跳过 SSO 步骤
    5. 上传验证文档
    6. 完成验证
    
    增强功能:
    - 一致的浏览器指纹
    - 人类化延迟
    - 欺诈检测处理
    - 自动重试
    """

    def __init__(self, url: str, proxy: str = None, impersonate: str = None):
        """
        初始化验证器
        
        Args:
            url: SheerID 验证链接
            proxy: 可选的代理服务器地址
            impersonate: 可选的 Chrome 版本
        """
        self.url = url
        self.vid = self._parse_id(url)
        self.proxy = proxy
        
        # 创建会话管理器（包含一致的浏览器配置文件）
        self.session_mgr = SessionManager(proxy=proxy, impersonate=impersonate)
        self.client = self.session_mgr.session
        self.profile = self.session_mgr.profile
        self.lib_name = self.session_mgr.lib_name
        self.impersonate_target = self.session_mgr.impersonate_target
        
        print(f"[信息] 会话创建成功，使用 {self.lib_name}（模拟: {self.impersonate_target}）")
        print(f"[信息] 浏览器配置文件: {self.profile.platform} / Chrome {self.profile.chrome_version}")
        print(f"[信息] 指纹 hash: {self.profile.fingerprint_hash[:16]}...")
        
        # 会话预热
        print("[信息] 正在预热会话...")
        self.session_mgr.warm(PROGRAM_ID)
        print("[信息] 会话预热完成")
        
        # 检测代理位置
        if proxy:
            self.proxy_country = get_proxy_country(proxy)
            print(f"[信息] 代理位置: {self.proxy_country}")
        else:
            self.proxy_country = "US"
        
        self.org = None
        self.retry_count = 0
        self.max_retries = 3

    def __del__(self):
        """析构函数 - 关闭 HTTP 客户端"""
        if hasattr(self, "session_mgr"):
            self.session_mgr.close()

    @staticmethod
    def _parse_id(url: str) -> Optional[str]:
        """从 URL 中解析验证 ID"""
        match = re.search(r"verificationId=([a-f0-9]+)", url, re.IGNORECASE)
        return match.group(1) if match else None

    def _get_headers(self, **kwargs) -> Dict:
        """获取带浏览器配置的请求头"""
        return get_headers_with_profile(self.profile, **kwargs)

    def _request(self, method: str, endpoint: str, body: Dict = None) -> Tuple[Dict, int]:
        """
        发送 API 请求
        
        带有人类化延迟和速率控制
        """
        # 人类化延迟
        random_delay(min_ms=400, max_ms=1200)
        
        try:
            headers = self._get_headers(for_sheerid=True)
            
            url = f"{SHEERID_API_URL}{endpoint}"
            
            if "curl_cffi" in self.lib_name:
                try:
                    resp = self.client.request(
                        method, url, json=body, headers=headers,
                        impersonate=self.impersonate_target
                    )
                except TypeError:
                    resp = self.client.request(method, url, json=body, headers=headers)
            else:
                resp = self.client.request(method, url, json=body, headers=headers)
            
            try:
                parsed = resp.json() if resp.text else {}
            except Exception:
                parsed = {"_text": resp.text}
            
            return parsed, resp.status_code
        except Exception as e:
            raise Exception(f"请求失败: {e}")

    def _upload_s3(self, url: str, data: bytes) -> bool:
        """上传文件到 S3"""
        # 模拟上传前的延迟
        interaction_delay("submit")
        
        attempts = [
            lambda: self.client.put(url, content=data, headers={"Content-Type": "image/png"}, timeout=60),
            lambda: self.client.put(url, data=data, headers={"Content-Type": "image/png"}, timeout=60),
            lambda: self.client.request("PUT", url, data=data, headers={"Content-Type": "image/png"}, timeout=60),
        ]

        for fn in attempts:
            try:
                resp = fn()
                if hasattr(resp, "status_code") and 200 <= resp.status_code < 300:
                    return True
            except:
                continue

        print("     ❗ S3 上传失败")
        return False

    def check_link(self) -> Dict:
        """检查验证链接是否有效"""
        if not self.vid:
            return {"valid": False, "error": "URL 无效"}

        data, status = self._request("GET", f"/verification/{self.vid}")
        if status != 200:
            return {"valid": False, "error": f"HTTP {status}"}

        step = data.get("currentStep", "")
        valid_steps = ["collectStudentPersonalInfo", "docUpload", "sso"]
        if step in valid_steps:
            return {"valid": True, "step": step}
        elif step == "success":
            return {"valid": False, "error": "已验证通过"}
        elif step == "pending":
            return {"valid": False, "error": "已提交，等待审核中"}
        return {"valid": False, "error": f"无效步骤: {step}"}

    def _generate_student_info(self) -> Dict:
        """
        生成 Harvard 学生信息
        
        强制使用 Harvard University 以匹配 Harvard 成绩单模板
        """
        first, last = generate_name(include_middle=random.random() < 0.2)
        
        # 强制使用 Harvard University
        from .university import get_university_by_name
        self.org = get_university_by_name("Harvard University")
        
        # 如果未找到 Harvard，使用硬编码的 Harvard 信息
        if not self.org:
            self.org = {
                "id": 1426,
                "name": "Harvard University",
                "domain": "harvard.edu",
                "weight": 92,
                "country": "US",
                "idExtended": "1426",
            }
        
        email = generate_email(first, last, self.org["domain"])
        dob = generate_birth_date()
        
        return {
            "first": first,
            "last": last,
            "email": email,
            "dob": dob,
            "org": self.org,
        }

    def _generate_document(self, student_info: Dict) -> Tuple[bytes, str]:
        """生成验证文档"""
        first = student_info["first"]
        last = student_info["last"]
        dob = student_info["dob"]
        school = student_info["org"]["name"]
        
        # 使用 Harvard 成绩单模板（仅使用此文档类型）
        print("     📄 生成 Harvard 学术成绩单...")
        doc = generate_harvard_transcript(first, last, school, dob, add_effects=True)
        filename = "transcript.png"
        
        return doc, filename

    def _submit_personal_info(self, student_info: Dict) -> Tuple[Dict, int]:
        """提交学生个人信息"""
        first = student_info["first"]
        last = student_info["last"]
        email = student_info["email"]
        dob = student_info["dob"]
        org = student_info["org"]
        
        # 获取完整指纹
        full_fp = self.profile.to_full_fingerprint()
        
        body = {
            "firstName": first,
            "lastName": last,
            "birthDate": dob,
            "email": email,
            "phoneNumber": "",
            "organization": {
                "id": org["id"],
                "idExtended": org["idExtended"],
                "name": org["name"],
            },
            "deviceFingerprintHash": full_fp["hash"],
            "locale": "en-US",
            "metadata": {
                "marketConsentValue": False,
                "verificationId": self.vid,
                "canvasHash": full_fp.get("canvas", ""),
                "webglHash": full_fp.get("webgl", {}).get("hash", ""),
                "audioHash": full_fp.get("audio", ""),
                "screenWidth": full_fp.get("screen", {}).get("width", 1920),
                "screenHeight": full_fp.get("screen", {}).get("height", 1080),
                "timezone": full_fp.get("timezone", -5),
                "language": full_fp.get("language", "en-US"),
            },
        }
        
        # 模拟表单填写延迟
        reading_delay(200)
        
        return self._request("POST", f"/verification/{self.vid}/step/collectStudentPersonalInfo", body)

    def _handle_error_response(self, data: Dict, student_info: Dict) -> Dict:
        """处理错误响应"""
        error_ids = data.get("errorIds", [])
        
        if "fraudRulesReject" in str(error_ids):
            # 记录欺诈触发
            fraud_tracker.record_fraud(self.org["name"], "fraudRulesReject")
            
            should_retry, delay = handle_fraud_rejection(
                retry_count=self.retry_count,
                error_payload=data,
                message=f"学校: {self.org['name']}"
            )
            
            if should_retry and self.retry_count < self.max_retries:
                self.retry_count += 1
                print(f"\n[重试] 等待 {delay}s 后重试（第 {self.retry_count}/{self.max_retries} 次）...")
                
                # 重新生成身份
                reset_profile()
                self.profile = create_new_profile()
                print(f"[重试] 新指纹: {self.profile.fingerprint_hash[:16]}...")
                
                return {"retry": True, "delay": delay}
        
        stats.record(self.org["name"], False)
        return {"success": False, "error": f"错误: {error_ids}"}

    def verify(self) -> Dict:
        """执行完整的验证流程"""
        if not self.vid:
            return {"success": False, "error": "验证 URL 无效"}

        try:
            # 检查当前步骤
            check_data, check_status = self._request("GET", f"/verification/{self.vid}")
            current_step = check_data.get("currentStep", "") if check_status == 200 else ""
            
            # ================================================================
            # 关键逻辑：处理不同的验证步骤
            # ================================================================
            
            if current_step in ["docUpload", "sso"]:
                # 验证已经提交过个人信息，需要使用相同的学生信息
                # 首先尝试从本地持久化存储中获取
                stored_info = verification_store.get_verification_info(self.vid)
                
                if stored_info:
                    # 找到了之前保存的信息，使用它
                    student_info = stored_info
                    self.org = stored_info["org"]
                    print(f"\n   ✅ 从本地存储加载已保存的学生信息")
                else:
                    # 本地没有保存，无法继续！
                    # 因为 SheerID API 不返回已提交的个人信息
                    print(f"\n   ❌ 错误：此验证链接已提交过个人信息，但本地没有保存记录！")
                    print(f"   ❌ 无法获取之前提交的姓名，继续会导致姓名不匹配。")
                    print(f"")
                    print(f"   💡 解决方案：")
                    print(f"      1. 使用新的验证链接重新开始")
                    print(f"      2. 或者在浏览器中手动完成此验证")
                    print(f"")
                    stats.record("Harvard University", False)
                    return {
                        "success": False, 
                        "error": "验证链接已过期或之前的信息未保存。请使用新的验证链接。"
                    }
            
            elif current_step == "collectStudentPersonalInfo":
                # 新的验证，从第一步开始
                print(f"\n   ✨ 新验证流程，生成学生信息...")
                student_info = self._generate_student_info()
                
                # 立即保存到本地存储，以便失败后重试时可以使用
                verification_store.save_verification_info(self.vid, student_info)
            
            else:
                # 其他未知步骤
                print(f"\n   ⚠️  未知步骤: {current_step}，尝试生成新信息...")
                student_info = self._generate_student_info()
            
            first, last = student_info["first"], student_info["last"]
            email = student_info["email"]
            dob = student_info["dob"]
            
            # 保存学生信息到调试日志
            debug_logger.log_student_info(student_info)

            print(f"\n   🎓 学生: {first} {last}")
            print(f"   📧 邮箱: {email}")
            print(f"   🏫 学校: {self.org['name']}")
            print(f"   🎂 生日: {dob}")
            print(f"   🔑 验证ID: {self.vid[:20]}...")
            print(f"   📍 当前步骤: {current_step}")

            # 步骤1: 生成验证文档（并行准备）
            print("\n   ▶ 步骤 1/5: 生成验证文档...")
            doc, filename = self._generate_document(student_info)
            print(f"     📄 文件: {filename} ({len(doc) / 1024:.1f} KB)")
            
            # 保存生成的文档到调试日志
            debug_logger.log_document(doc, filename)

            # 步骤2: 提交学生信息
            if current_step == "collectStudentPersonalInfo":
                print("   ▶ 步骤 2/5: 提交学生信息...")
                
                data, status = self._submit_personal_info(student_info)

                if status != 200:
                    stats.record(self.org["name"], False)
                    return {"success": False, "error": f"提交失败: {status}"}

                if data.get("currentStep") == "error":
                    result = self._handle_error_response(data, student_info)
                    if result.get("retry"):
                        import time
                        time.sleep(result["delay"])
                        return self.verify()  # 递归重试
                    return result

                current_step = data.get("currentStep", "")
                print(f"     ✅ 提交成功，下一步: {current_step}")
            elif current_step in ["docUpload", "sso"]:
                print("   ▶ 步骤 2/5: 跳过（已通过信息提交步骤）...")

            # 步骤3: 跳过 SSO
            if current_step == "sso" or True:  # 总是尝试跳过
                print("   ▶ 步骤 3/5: 跳过 SSO...")
                random_delay(300, 700)
                self._request("DELETE", f"/verification/{self.vid}/step/sso")

            # 步骤4: 上传文档
            print("   ▶ 步骤 4/5: 上传文档...")
            upload_body = {
                "files": [{
                    "fileName": filename,
                    "mimeType": "image/png",
                    "fileSize": len(doc)
                }]
            }
            data, status = self._request("POST", f"/verification/{self.vid}/step/docUpload", upload_body)

            if not data.get("documents"):
                stats.record(self.org["name"], False)
                return {"success": False, "error": "未获取到上传 URL"}

            upload_url = data["documents"][0].get("uploadUrl")
            if not self._upload_s3(upload_url, doc):
                stats.record(self.org["name"], False)
                return {"success": False, "error": "上传失败"}

            print("     ✅ 文档上传成功！")

            # 步骤5: 完成上传
            print("   ▶ 步骤 5/5: 完成上传...")
            random_delay(500, 1000)
            data, status = self._request("POST", f"/verification/{self.vid}/step/completeDocUpload")
            final_step = data.get("currentStep", "unknown")
            print(f"     📍 最终步骤: {final_step}")

            # 处理结果
            if final_step == "success":
                stats.record(self.org["name"], True)
                return {
                    "success": True,
                    "message": "验证成功！",
                    "student": f"{first} {last}",
                    "email": email,
                    "school": self.org["name"],
                    "redirectUrl": data.get("redirectUrl"),
                }
            elif final_step == "pending":
                return {
                    "success": False,
                    "pending": True,
                    "message": "文档已提交审核。请等待 24-48 小时。",
                    "student": f"{first} {last}",
                    "email": email,
                    "school": self.org["name"],
                }
            elif final_step in ["rejected", "error"]:
                error_ids = data.get("errorIds", [])
                if "fraudRulesReject" in str(error_ids):
                    fraud_tracker.record_fraud(self.org["name"], "fraudRulesReject")
                stats.record(self.org["name"], False)
                return {"success": False, "error": f"被拒绝: {error_ids}"}
            else:
                return {
                    "success": False,
                    "pending": True,
                    "message": f"未知状态: {final_step}",
                    "student": f"{first} {last}",
                    "email": email,
                    "school": self.org["name"],
                }

        except Exception as e:
            if self.org:
                stats.record(self.org["name"], False)
            return {"success": False, "error": str(e)}
