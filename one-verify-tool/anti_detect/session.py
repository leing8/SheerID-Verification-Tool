"""
反检测模块 - 会话管理

HTTP 会话创建（优先级: curl_cffi > cloudscraper > httpx > requests）、
会话预热、学生邮箱生成。
"""

import random
import time

from .constants import (
    CHROME_VERSIONS,
    DEFAULT_IMPERSONATE,
    IMPERSONATE_OPTIONS,
    USER_AGENTS,
)


def random_delay(min_ms: int = 300, max_ms: int = 1200):
    """使用 Gamma 分布的随机延迟，模拟人类操作行为"""
    try:
        import numpy as np

        # Gamma 分布更接近人类真实反应时间
        shape, scale = 2.0, (max_ms - min_ms) / 4000
        delay = min_ms / 1000 + np.random.gamma(shape, scale)
        delay = min(delay, max_ms / 1000)  # 上限截断
    except ImportError:
        # 回退到基本随机 + 微小随机偏移
        delay = random.randint(min_ms, max_ms) / 1000
        delay += random.uniform(0, 0.15)

    time.sleep(delay)


def get_random_impersonate(browser_type: str = None) -> str:
    """
    随机获取浏览器模拟标识

    Args:
        browser_type: 'chrome'/'edge'/'safari'，为 None 则按权重随机选择
    """
    if browser_type and browser_type in IMPERSONATE_OPTIONS:
        return random.choice(IMPERSONATE_OPTIONS[browser_type])

    # Chrome 权重最高（最常见、最安全）
    weights = [0.75, 0.15, 0.10]
    browser = random.choices(["chrome", "edge", "safari"], weights=weights)[0]
    return random.choice(IMPERSONATE_OPTIONS[browser])


def create_session(proxy: str = None, impersonate: str = None):
    """
    创建 HTTP 会话，按优先级选择最佳可用库
    优先级: curl_cffi(带模拟) > cloudscraper > httpx > requests

    重要: 强烈推荐 curl_cffi + Chrome 模拟，
    否则 SheerID 可检测到 Python 的 TLS 指纹 (JA3/JA4)

    Args:
        proxy: 代理 URL
        impersonate: 模拟的 Chrome 版本，默认使用 DEFAULT_IMPERSONATE

    Returns:
        tuple: (session, 库名称, 模拟版本)
    """
    from .proxy import check_proxy_type, validate_proxy

    # 验证并格式化代理
    proxy = validate_proxy(proxy)
    proxies = None
    if proxy:
        proxies = {"http": proxy, "https": proxy, "all://": proxy}

        # 警告: 数据中心代理风险高
        proxy_type = check_proxy_type(proxy)
        if proxy_type == "datacenter":
            print("[警告] ⚠️  检测到数据中心代理! SheerID 可能拒绝请求")
            print("[警告]    强烈建议使用住宅代理")

    # 确定模拟版本
    imp_version = impersonate or DEFAULT_IMPERSONATE

    # 优先尝试 curl_cffi (最佳 - TLS 指纹伪装)
    try:
        from curl_cffi import requests as curl_requests

        # 检查模拟版本是否支持
        try:
            if proxies:
                session = curl_requests.Session(
                    proxies=proxies, impersonate=imp_version
                )
            else:
                session = curl_requests.Session(impersonate=imp_version)

            print(f"[反检测] ✅ 使用 curl_cffi {imp_version} 模拟")
            print(f"[反检测]    TLS 指纹将匹配真实 Chrome 浏览器")
            return session, "curl_cffi", imp_version

        except Exception:
            # 版本不支持时尝试回退版本
            print(f"[警告] 模拟版本 '{imp_version}' 不支持，尝试回退版本...")

            # 尝试旧版本
            for fallback_ver in ["chrome120", "chrome110", "chrome100"]:
                try:
                    if proxies:
                        session = curl_requests.Session(
                            proxies=proxies, impersonate=fallback_ver
                        )
                    else:
                        session = curl_requests.Session(impersonate=fallback_ver)
                    print(f"[反检测] ✅ 使用 curl_cffi {fallback_ver} 模拟")
                    return session, "curl_cffi", fallback_ver
                except Exception:
                    continue

            # 最后手段 - 不使用模拟
            if proxies:
                session = curl_requests.Session(proxies=proxies)
            else:
                session = curl_requests.Session()
            print("[反检测] ⚠️  curl_cffi 已加载但模拟失败")
            print("[反检测]    TLS 指纹可能被检测!")
            return session, "curl_cffi", None

    except ImportError:
        print("\n" + "=" * 60)
        print("⚠️  严重: curl_cffi 未安装!")
        print("=" * 60)
        print("未安装 curl_cffi，你的 TLS 指纹将被检测")
        print("SheerID 很可能拒绝你的验证请求")
        print("")
        print("请安装: pip install curl_cffi")
        print("=" * 60 + "\n")

    # 尝试 cloudscraper (Cloudflare 绕过，无 TLS 伪装)
    try:
        import cloudscraper

        session = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        if proxies:
            session.proxies = proxies
        print("[反检测] ⚠️  使用 cloudscraper (无 TLS 模拟)")
        return session, "cloudscraper", None
    except ImportError:
        pass

    # 尝试 httpx (支持异步，但 TLS 可检测)
    try:
        import httpx

        proxy_url = proxies.get("all://") if proxies else None
        session = httpx.Client(timeout=30, proxy=proxy_url)
        print("[反检测] ⚠️  使用 httpx (TLS 指纹可被检测!)")
        return session, "httpx", None
    except ImportError:
        pass

    # 回退到 requests (最容易被检测)
    import requests

    session = requests.Session()
    if proxies:
        session.proxies = proxies
    print("[反检测] ❌ 使用 requests (检测风险极高!)")
    print("[反检测]    请执行: pip install curl_cffi")
    return session, "requests", None


def print_anti_detect_info():
    """打印反检测配置信息"""
    session, lib, imp = create_session()
    print(f"\n{'=' * 50}")
    print(f"反检测配置信息")
    print(f"{'=' * 50}")
    print(f"  HTTP 库: {lib}")
    print(f"  模拟版本: {imp or '无 (可被检测!)'}")
    print(f"  User-Agent: {len(USER_AGENTS)} 个变体")
    print(f"  Chrome 版本: {len(CHROME_VERSIONS)} 个可用")

    if lib == "curl_cffi" and imp:
        print(f"\n  ✅ TLS 指纹: 已伪装为 {imp}")
        print(f"  ✅ 检测风险: 低")
    elif lib == "curl_cffi":
        print(f"\n  ⚠️  TLS 指纹: 部分伪装")
        print(f"  ⚠️  检测风险: 中")
    else:
        print(f"\n  ❌ TLS 指纹: Python 签名 (可被检测)")
        print(f"  ❌ 检测风险: 高")

    print(f"{'=' * 50}\n")

    # 清理资源
    if hasattr(session, "close"):
        session.close()


def make_request(session, method: str, url: str, impersonate: str = None, **kwargs):
    """
    发送 HTTP 请求，为 curl_cffi 自动应用模拟参数

    Args:
        session: create_session() 返回的 HTTP 会话
        method: HTTP 方法 (GET, POST, PUT, DELETE)
        url: 请求 URL
        impersonate: Chrome 模拟版本 (仅 curl_cffi 有效)
        **kwargs: 其他参数 (json, headers 等)
    """
    imp = impersonate or DEFAULT_IMPERSONATE

    # 检查是否为 curl_cffi 会话
    session_type = type(session).__module__

    if "curl_cffi" in session_type:
        # curl_cffi 支持按请求设置模拟
        try:
            return session.request(method, url, impersonate=imp, **kwargs)
        except TypeError:
            # 旧版本不支持按请求设置模拟
            return session.request(method, url, **kwargs)
    else:
        return session.request(method, url, **kwargs)


def warm_session(session, program_id: str = None, headers: dict = None):
    """
    预热会话，模拟真实浏览器页面加载行为

    Args:
        session: create_session() 返回的 HTTP 会话
        program_id: SheerID 项目 ID (可选)
        headers: 请求头 (可选)
    """
    base_url = "https://services.sheerid.com"
    hdrs = headers or {"Content-Type": "application/json"}

    try:
        # 第1步: 加载 API 配置（模拟浏览器页面加载）
        session.get(f"{base_url}/rest/v2/config", headers=hdrs, timeout=10)
        random_delay(500, 1000)
    except Exception:
        pass

    if program_id:
        try:
            # 第2步: 加载项目信息
            session.get(
                f"{base_url}/rest/v2/program/{program_id}", headers=hdrs, timeout=10
            )
            random_delay(300, 700)
        except Exception:
            pass

    try:
        # 第3步: 查询组织端点（以空关键词搜索）
        params = {"country": "US", "term": ""}
        if program_id:
            params["programId"] = program_id
        session.get(
            f"{base_url}/rest/v2/organization/search",
            params=params,
            headers=hdrs,
            timeout=10,
        )
        random_delay(200, 500)
    except Exception:
        pass

    return session


def generate_student_email(
    first_name: str, last_name: str, university: dict = None
) -> str:
    """
    生成与大学域名匹配的学生邮箱

    Args:
        first_name: 学生名
        last_name: 学生姓
        university: 包含 'domain' 键的大学字典 (可选)
    """
    first = first_name.lower().strip()
    last = last_name.lower().strip()

    domain = university.get("domain", "") if university else ""

    if not domain:
        # 通用邮箱提供商
        domains = ["gmail.com", "outlook.com", "yahoo.com", "icloud.com"]
        domain = random.choice(domains)

    # 常见大学邮箱格式
    patterns = [
        f"{first[0]}{last}@{domain}",  # jsmith@university.edu
        f"{first}.{last}@{domain}",  # john.smith@university.edu
        f"{first}{last[0]}@{domain}",  # johns@university.edu
        f"{first}_{last}@{domain}",  # john_smith@university.edu
        f"{last}{first[0]}@{domain}",  # smithj@university.edu
        f"{first}{random.randint(1, 99)}@{domain}",  # john42@university.edu
    ]

    return random.choice(patterns)
