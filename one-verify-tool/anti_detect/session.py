"""
会话管理模块
创建 HTTP 会话、TLS 伪装和请求发送
"""

import random
import time

from .config import DEFAULT_IMPERSONATE, IMPERSONATE_OPTIONS, CHROME_VERSIONS, USER_AGENTS, RESOLUTIONS
from .headers import get_headers
from .proxy import validate_proxy, check_proxy_type


def random_delay(min_ms: int = 300, max_ms: int = 1200):
    """
    使用 Gamma 分布的随机延迟以模拟人类行为
    Gamma 分布比均匀随机更逼真
    """
    try:
        import numpy as np

        # Gamma 分布更好地模拟人类反应时间
        shape, scale = 2.0, (max_ms - min_ms) / 4000
        delay = min_ms / 1000 + np.random.gamma(shape, scale)
        delay = min(delay, max_ms / 1000)  # 限制最大值
    except ImportError:
        # 回退到带轻微变化的基础随机
        delay = random.randint(min_ms, max_ms) / 1000
        delay += random.uniform(0, 0.15)  # 添加额外随机性

    time.sleep(delay)


def get_random_impersonate(browser_type: str = None) -> str:
    """
    获取随机浏览器模拟字符串以增加多样性

    参数:
        browser_type: 'chrome'、'edge'、'safari' 或 None（加权随机）

    返回:
        模拟字符串，如 'chrome131'
    """
    if browser_type and browser_type in IMPERSONATE_OPTIONS:
        return random.choice(IMPERSONATE_OPTIONS[browser_type])

    # 偏向 Chrome（最常见，最安全）
    weights = [0.75, 0.15, 0.10]
    browser = random.choices(["chrome", "edge", "safari"], weights=weights)[0]
    return random.choice(IMPERSONATE_OPTIONS[browser])


def create_session(proxy: str = None, impersonate: str = None):
    """
    使用最佳可用库创建 HTTP 会话
    优先级: curl_cffi（带模拟） > cloudscraper > httpx > requests

    关键: 强烈建议使用带 Chrome 模拟的 curl_cffi。
    没有它，SheerID 可以检测 Python 的 TLS 指纹（JA3/JA4）。

    参数:
        proxy: 代理 URL（如需要会进行格式化）
        impersonate: 要模拟的 Chrome 版本（如 "chrome131"）
                    如果为 None，使用 DEFAULT_IMPERSONATE

    返回:
        tuple: (session, library_name, impersonate_version)
    """
    # 验证并格式化代理
    proxy = validate_proxy(proxy)
    proxies = None
    if proxy:
        proxies = {"http": proxy, "https": proxy, "all://": proxy}

        # 如果使用数据中心代理则发出警告
        proxy_type = check_proxy_type(proxy)
        if proxy_type == "datacenter":
            print("[警告] ⚠️  检测到数据中心代理！SheerID 可能会拒绝请求。")
            print("[警告]    强烈建议使用住宅代理。")

    # 确定模拟版本
    imp_version = impersonate or DEFAULT_IMPERSONATE

    # 首先尝试 curl_cffi（最佳 - TLS 指纹伪装）
    try:
        from curl_cffi import requests as curl_requests

        # 测试是否支持模拟
        try:
            if proxies:
                session = curl_requests.Session(
                    proxies=proxies, impersonate=imp_version
                )
            else:
                session = curl_requests.Session(impersonate=imp_version)

            print(f"[反检测] ✅ 使用 curl_cffi，模拟 {imp_version}")
            print(f"[反检测]    TLS 指纹将匹配真实 Chrome 浏览器")
            return session, "curl_cffi", imp_version

        except Exception as e:
            # 如果版本不支持则尝试不使用模拟
            print(
                f"[警告] 不支持模拟 '{imp_version}'，尝试回退..."
            )

            # 尝试旧版本
            for fallback_ver in ["chrome120", "chrome110", "chrome100"]:
                try:
                    if proxies:
                        session = curl_requests.Session(
                            proxies=proxies, impersonate=fallback_ver
                        )
                    else:
                        session = curl_requests.Session(impersonate=fallback_ver)
                    print(
                        f"[反检测] ✅ 使用 curl_cffi，模拟 {fallback_ver}"
                    )
                    return session, "curl_cffi", fallback_ver
                except Exception:
                    continue

            # 最后手段 - 不使用模拟
            if proxies:
                session = curl_requests.Session(proxies=proxies)
            else:
                session = curl_requests.Session()
            print("[反检测] ⚠️  curl_cffi 已加载但模拟失败")
            print("[反检测]    TLS 指纹可能被检测到！")
            return session, "curl_cffi", None

    except ImportError:
        print("\n" + "=" * 60)
        print("⚠️  严重警告: curl_cffi 未安装！")
        print("=" * 60)
        print("没有 curl_cffi，您的 TLS 指纹是可检测的。")
        print("SheerID 很可能会拒绝您的验证请求。")
        print("")
        print("立即安装: pip install curl_cffi")
        print("=" * 60 + "\n")

    # 尝试 cloudscraper（Cloudflare 绕过，但无 TLS 伪装）
    try:
        import cloudscraper

        session = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        if proxies:
            session.proxies = proxies
        print("[反检测] ⚠️  使用 cloudscraper（无 TLS 模拟）")
        return session, "cloudscraper", None
    except ImportError:
        pass

    # 尝试 httpx（异步支持，但 TLS 可检测）
    try:
        import httpx

        proxy_url = proxies.get("all://") if proxies else None
        session = httpx.Client(timeout=30, proxy=proxy_url)
        print("[反检测] ⚠️  使用 httpx（TLS 指纹可被检测！）")
        print(
            "[反检测]    预期成功率: ~20-40%（使用 curl_cffi 可达 60-80%）"
        )
        return session, "httpx", None
    except ImportError:
        pass

    # 回退到 requests（最容易被检测）
    import requests

    session = requests.Session()
    if proxies:
        session.proxies = proxies
    print("[反检测] ❌ 使用 requests（检测风险极高！）")
    print("[反检测]    预期成功率: ~5-20%")
    print("[反检测]    请运行: pip install curl_cffi")
    return session, "requests", None


def make_request(session, method: str, url: str, impersonate: str = None, **kwargs):
    """
    使用 curl_cffi 的正确模拟发起 HTTP 请求

    这是一个辅助函数，确保对于支持的库每个请求都使用模拟。

    参数:
        session: 来自 create_session() 的 HTTP 会话
        method: HTTP 方法（GET、POST、PUT、DELETE）
        url: 请求 URL
        impersonate: 要模拟的 Chrome 版本（用于 curl_cffi）
        **kwargs: 其他参数（json、headers 等）

    返回:
        Response 对象
    """
    imp = impersonate or DEFAULT_IMPERSONATE

    # 检查是否为 curl_cffi 会话
    session_type = type(session).__module__

    if "curl_cffi" in session_type:
        # curl_cffi 支持每请求模拟
        try:
            return session.request(method, url, impersonate=imp, **kwargs)
        except TypeError:
            # 旧版本不支持每请求模拟
            return session.request(method, url, **kwargs)
    else:
        # 其他库 - 直接发起请求
        return session.request(method, url, **kwargs)


def warm_session(session, program_id: str = None, headers: dict = None):
    """
    在验证尝试前预热会话
    通过先建立会话使请求看起来更像真实浏览器

    参数:
        session: 来自 create_session() 的 HTTP 会话
        program_id: SheerID 项目 ID（可选）
        headers: 要使用的请求头（可选）

    返回:
        session: 预热后的会话
    """
    base_url = "https://services.sheerid.com"
    hdrs = headers or get_headers(for_sheerid=True)

    try:
        # 步骤1: 加载主 API（像浏览器在页面加载时那样）
        session.get(f"{base_url}/rest/v2/config", headers=hdrs, timeout=10)
        random_delay(500, 1000)
    except Exception:
        pass

    if program_id:
        try:
            # 步骤2: 加载项目信息
            session.get(
                f"{base_url}/rest/v2/program/{program_id}", headers=hdrs, timeout=10
            )
            random_delay(300, 700)
        except Exception:
            pass

    try:
        # 步骤3: 检查组织端点（使用空搜索词搜索）
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
    生成与大学域名匹配的逼真学生邮箱

    参数:
        first_name: 学生名
        last_name: 学生姓
        university: 包含 'domain' 键的大学字典（可选）

    返回:
        生成的邮箱地址
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


def print_anti_detect_info():
    """打印反检测配置信息"""
    session, lib, imp = create_session()
    print(f"\n{'=' * 50}")
    print(f"反检测配置")
    print(f"{'=' * 50}")
    print(f"  HTTP 库: {lib}")
    print(f"  模拟: {imp or '无（可检测！）'}")
    print(f"  User-Agent: {len(USER_AGENTS)} 种变体")
    print(f"  分辨率: {len(RESOLUTIONS)} 种变体")
    print(f"  Chrome 版本: {len(CHROME_VERSIONS)} 个可用")

    if lib == "curl_cffi" and imp:
        print(f"\n  ✅ TLS 指纹: 伪装为 {imp}")
        print(f"  ✅ 检测风险: 低")
    elif lib == "curl_cffi":
        print(f"\n  ⚠️  TLS 指纹: 部分伪装")
        print(f"  ⚠️  检测风险: 中")
    else:
        print(f"\n  ❌ TLS 指纹: Python 签名（可检测）")
        print(f"  ❌ 检测风险: 高")

    print(f"{'=' * 50}\n")

    # 清理
    if hasattr(session, "close"):
        session.close()
