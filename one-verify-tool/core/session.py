"""
会话管理模块 - HTTP 会话创建和预热

包含:
- create_session: 创建 HTTP 会话
- warm_session: 会话预热
- make_request: 发送请求
- SessionManager: 增强的会话管理器
"""

import time
import random
from typing import Tuple, Optional, Dict, Any

from .constants import HAS_CURL_CFFI, DEFAULT_IMPERSONATE, RATE_LIMIT_CONFIG
from .proxy import validate_proxy, check_proxy_type
from .headers import get_headers, get_resource_headers, get_navigation_headers
from .delay import random_delay, interaction_delay
from .fingerprint import get_or_create_profile, create_new_profile, BrowserProfile


class SessionManager:
    """
    增强的会话管理器
    
    提供：
    - 一致的浏览器配置文件
    - 请求速率控制
    - Cookie 管理
    - 预热和真实浏览器行为模拟
    """
    
    def __init__(self, proxy: str = None, impersonate: str = None):
        """
        初始化会话管理器
        
        Args:
            proxy: 代理 URL
            impersonate: Chrome 版本（如 "chrome133"）
        """
        self.proxy = validate_proxy(proxy)
        self.impersonate = impersonate or DEFAULT_IMPERSONATE
        
        # 创建浏览器配置文件
        chrome_version = self.impersonate.replace("chrome", "").replace("edge", "").replace("safari", "")
        self.profile = create_new_profile(chrome_version=chrome_version)
        
        # 创建 HTTP 会话
        self.session, self.lib_name, self.impersonate_target = create_session(
            self.proxy, self.impersonate
        )
        
        # 请求追踪
        self.request_times = []
        self.request_count = 0
        
        # Cookie 存储
        self.cookies = {}
        
        # 预热状态
        self.is_warmed = False
    
    def _check_rate_limit(self):
        """检查并执行速率限制"""
        now = time.time()
        
        # 清理过期的请求记录（1分钟前的）
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # 检查每分钟请求数
        if len(self.request_times) >= RATE_LIMIT_CONFIG["max_requests_per_minute"]:
            wait_time = 60 - (now - self.request_times[0])
            if wait_time > 0:
                print(f"[速率限制] 等待 {wait_time:.1f}s...")
                time.sleep(wait_time)
                self.request_times = []
        
        # 检查最小间隔
        if self.request_times:
            last_request = self.request_times[-1]
            min_interval = RATE_LIMIT_CONFIG["min_interval_ms"] / 1000
            elapsed = now - last_request
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
        
        # 检查突发限制
        recent_requests = [t for t in self.request_times if now - t < 2]
        if len(recent_requests) >= RATE_LIMIT_CONFIG["burst_limit"]:
            cooldown = RATE_LIMIT_CONFIG["cooldown_after_burst_ms"] / 1000
            print(f"[速率限制] 突发冷却 {cooldown:.1f}s...")
            time.sleep(cooldown)
        
        # 记录本次请求
        self.request_times.append(time.time())
        self.request_count += 1
    
    def get_headers(self, **kwargs) -> Dict:
        """获取带配置文件的请求头"""
        from .headers import get_headers_with_profile
        return get_headers_with_profile(self.profile, **kwargs)
    
    def request(self, method: str, url: str, **kwargs) -> Any:
        """
        发送请求（带速率限制和人类化延迟）
        """
        self._check_rate_limit()
        
        # 添加人类化延迟
        random_delay(300, 800)
        
        # 确保使用正确的 headers
        if "headers" not in kwargs:
            kwargs["headers"] = self.get_headers()
        
        return make_request(
            self.session, method, url,
            impersonate=self.impersonate_target,
            **kwargs
        )
    
    def warm(self, program_id: str = None) -> bool:
        """
        预热会话
        
        模拟真实浏览器的页面加载行为，包括资源请求。
        """
        if self.is_warmed:
            return True
        
        try:
            success = warm_session_enhanced(
                self.session,
                self.profile,
                program_id,
                self.impersonate_target
            )
            self.is_warmed = success
            return success
        except Exception as e:
            print(f"[警告] 会话预热失败: {e}")
            return False
    
    def close(self):
        """关闭会话"""
        if hasattr(self.session, "close"):
            self.session.close()


def create_session(proxy: str = None, impersonate: str = None):
    """
    创建 HTTP 会话
    
    优先级: curl_cffi (TLS 伪装) > httpx > requests
    
    Args:
        proxy: 代理 URL
        impersonate: Chrome 版本（如 "chrome133"）
    
    Returns:
        (session, library_name, impersonate_version)
    """
    proxy = validate_proxy(proxy)
    proxies = None
    if proxy:
        proxies = {"http": proxy, "https": proxy, "all://": proxy}
        
        proxy_type = check_proxy_type(proxy)
        if proxy_type == "datacenter":
            print("[警告] ⚠️  检测到数据中心代理！SheerID 可能拒绝请求。")
            print("[警告]    强烈建议使用住宅代理。")
    
    imp_version = impersonate or DEFAULT_IMPERSONATE
    
    # curl_cffi（最佳 - TLS 指纹伪装）
    if HAS_CURL_CFFI:
        try:
            from curl_cffi import requests as curl_requests
            
            if proxies:
                session = curl_requests.Session(proxies=proxies, impersonate=imp_version)
            else:
                session = curl_requests.Session(impersonate=imp_version)
            
            print(f"[反检测] ✅ curl_cffi 已启用，模拟 {imp_version}")
            return session, "curl_cffi", imp_version
        except Exception as e:
            # 尝试回退版本
            fallback_versions = ["chrome132", "chrome131", "chrome130", "chrome120"]
            for fallback in fallback_versions:
                try:
                    from curl_cffi import requests as curl_requests
                    if proxies:
                        session = curl_requests.Session(proxies=proxies, impersonate=fallback)
                    else:
                        session = curl_requests.Session(impersonate=fallback)
                    print(f"[反检测] ✅ curl_cffi 已启用，模拟 {fallback}（回退）")
                    return session, "curl_cffi", fallback
                except:
                    continue
            
            # 最后手段：无伪装
            from curl_cffi import requests as curl_requests
            if proxies:
                session = curl_requests.Session(proxies=proxies)
            else:
                session = curl_requests.Session()
            print("[反检测] ⚠️  curl_cffi 已加载但伪装失败")
            return session, "curl_cffi", None
    
    # httpx 备用
    try:
        import httpx
        proxy_url = proxies.get("all://") if proxies else None
        session = httpx.Client(timeout=30, proxy=proxy_url)
        print("[反检测] ⚠️  使用 httpx（TLS 指纹可检测！）")
        return session, "httpx", None
    except ImportError:
        pass
    
    # requests 最后手段
    import requests
    session = requests.Session()
    if proxies:
        session.proxies = proxies
    print("[反检测] ❌ 使用 requests（检测风险非常高！）")
    return session, "requests", None


def warm_session(session, program_id: str = None, headers: dict = None):
    """
    会话预热 - 模拟真实浏览器的页面加载行为（兼容旧 API）
    """
    profile = get_or_create_profile()
    return warm_session_enhanced(session, profile, program_id)


def warm_session_enhanced(
    session,
    profile: BrowserProfile,
    program_id: str = None,
    impersonate: str = None
) -> bool:
    """
    增强的会话预热
    
    模拟真实浏览器访问 SheerID 的完整请求序列。
    """
    from .headers import get_headers_with_profile, get_resource_headers
    
    base_url = "https://services.sheerid.com"
    success = True
    
    # 1. 首先请求主页/验证页（导航请求）
    try:
        nav_headers = get_navigation_headers(profile)
        # 模拟访问入口页面
        random_delay(500, 1000)
    except Exception:
        pass
    
    # 2. 获取配置
    try:
        hdrs = get_headers_with_profile(profile, for_sheerid=True)
        make_request(
            session, "GET", f"{base_url}/rest/v2/config",
            headers=hdrs, impersonate=impersonate, timeout=10
        )
        random_delay(300, 600)
    except Exception:
        pass
    
    # 3. 获取程序信息
    if program_id:
        try:
            hdrs = get_headers_with_profile(profile, for_sheerid=True)
            make_request(
                session, "GET", f"{base_url}/rest/v2/program/{program_id}",
                headers=hdrs, impersonate=impersonate, timeout=10
            )
            random_delay(200, 500)
        except Exception:
            pass
    
    # 4. 模拟搜索组织
    try:
        hdrs = get_headers_with_profile(profile, for_sheerid=True)
        params = {"country": "US", "term": ""}
        if program_id:
            params["programId"] = program_id
        make_request(
            session, "GET", f"{base_url}/rest/v2/organization/search",
            params=params, headers=hdrs, impersonate=impersonate, timeout=10
        )
        random_delay(200, 400)
    except Exception:
        pass
    
    # 5. 模拟资源请求（可选，增加真实性）
    try:
        res_headers = get_resource_headers(profile, "script")
        # 不实际请求，只是设置 headers 以模拟
        random_delay(100, 200)
    except Exception:
        pass
    
    print("[信息] 会话预热完成")
    return success


def make_request(session, method: str, url: str, impersonate: str = None, **kwargs):
    """
    发送 HTTP 请求（curl_cffi 支持每请求伪装）
    
    Args:
        session: HTTP 会话
        method: HTTP 方法
        url: 请求 URL
        impersonate: TLS 伪装版本
        **kwargs: 其他请求参数
    
    Returns:
        Response 对象
    """
    imp = impersonate or DEFAULT_IMPERSONATE
    session_type = type(session).__module__
    
    if "curl_cffi" in session_type:
        try:
            return session.request(method, url, impersonate=imp, **kwargs)
        except TypeError:
            # 某些版本不支持 impersonate 参数
            return session.request(method, url, **kwargs)
    else:
        return session.request(method, url, **kwargs)
