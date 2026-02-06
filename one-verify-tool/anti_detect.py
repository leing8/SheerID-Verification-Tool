"""
SheerID 验证工具反检测模块
用于绕过反欺诈检测的共享模块

功能特性:
- 随机 User-Agent 轮换（Chrome、Firefox、Edge、Safari）
- 类浏览器请求头（正确排序）
- 随机指纹生成
- 请求延迟随机化
- TLS 指纹伪装（Chrome 模拟，使用 curl_cffi）
- NewRelic 追踪请求头（SheerID 必需）
- Canvas/WebGL 指纹模拟
- 代理验证和格式化

使用方法:
    from anti_detect import get_headers, get_fingerprint, random_delay, create_session
    from anti_detect import generate_newrelic_headers  # 用于 SheerID API 调用
    from anti_detect import make_request  # 带模拟功能的高级请求

关键提示: 为获得最佳效果，请安装 curl_cffi:
    pip install curl_cffi

没有 curl_cffi，SheerID 可以检测到 Python 的 TLS 指纹并拒绝请求。
"""

import random
import hashlib
import time
import uuid
import base64
import json
import sys

# ============ Chrome 模拟版本 ============
# 这些是 curl_cffi 可以模拟的 Chrome 版本
# 2026年1月更新 - 使用最新稳定版本
CHROME_VERSIONS = [
    "chrome131",  # Chrome 131（稳定版）
    "chrome130",  # Chrome 130
    "chrome124",  # Chrome 124
    "chrome123",  # Chrome 123
    "chrome120",  # Chrome 120
    "chrome119",  # Chrome 119
    "chrome116",  # Chrome 116
    "chrome110",  # Chrome 110
    "chrome107",  # Chrome 107
    "chrome104",  # Chrome 104
    "chrome101",  # Chrome 101
    "chrome100",  # Chrome 100
    "chrome99",  # Chrome 99
]

# 多浏览器类型轮换（curl_cffi 支持这些）
IMPERSONATE_OPTIONS = {
    "chrome": ["chrome131", "chrome130", "chrome124", "chrome120"],
    "edge": ["edge131", "edge127", "edge101"],
    "safari": ["safari18", "safari17_2_ios", "safari17_0"],
}

# 默认模拟 - 使用最新稳定版
DEFAULT_IMPERSONATE = "chrome131"

# ============ User-Agent 列表 ============
# 真实浏览器 User-Agent（2026年1月更新）
# 重要: 这些必须与我们模拟的 Chrome 版本匹配
USER_AGENTS_CHROME = [
    # Chrome 131 Windows（匹配 chrome131 模拟）
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Chrome 131 Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Chrome 130 Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Chrome 130 Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]

# 向后兼容的旧列表
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Edge Windows（基于 Chromium）
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
]

# ============ 屏幕分辨率 ============
RESOLUTIONS = [
    "1920x1080",
    "1366x768",
    "1536x864",
    "1440x900",
    "1280x720",
    "2560x1440",
    "1600x900",
    "1680x1050",
    "1280x800",
    "1024x768",
]

# ============ 时区 ============
TIMEZONES = [-8, -7, -6, -5, -4, -3, 0, 1, 2, 3, 5.5, 8, 9, 10]

# ============ 语言 ============
LANGUAGES = [
    "en-US,en;q=0.9",
    "en-US,en;q=0.9,es;q=0.8",
    "en-GB,en;q=0.9",
    "en-CA,en;q=0.9",
    "en-AU,en;q=0.9",
]

# ============ 平台 ============
# 必须与 User-Agent 匹配以保持一致性
PLATFORMS = [
    (
        "Windows",
        '"Windows"',
        '"Chromium";v="131", "Google Chrome";v="131", "Not_A Brand";v="24"',
    ),
    (
        "Windows",
        '"Windows"',
        '"Chromium";v="130", "Google Chrome";v="130", "Not_A Brand";v="24"',
    ),
    (
        "macOS",
        '"macOS"',
        '"Chromium";v="131", "Google Chrome";v="131", "Not_A Brand";v="24"',
    ),
    (
        "Linux",
        '"Linux"',
        '"Chromium";v="131", "Google Chrome";v="131", "Not_A Brand";v="24"',
    ),
]

# ============ WebGL 厂商 ============
WEBGL_VENDORS = [
    "Google Inc. (NVIDIA)",
    "Google Inc. (Intel)",
    "Google Inc. (AMD)",
    "Google Inc. (Apple)",
]

WEBGL_RENDERERS = [
    "ANGLE (NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (Apple M1 Pro)",
]


def get_random_user_agent() -> str:
    """获取随机的 User-Agent 字符串"""
    return random.choice(USER_AGENTS)


def get_fingerprint() -> str:
    """生成逼真的浏览器指纹哈希"""
    components = [
        str(int(time.time() * 1000)),
        str(random.random()),
        random.choice(RESOLUTIONS),
        str(random.choice(TIMEZONES)),
        random.choice(LANGUAGES).split(",")[0],
        random.choice(["Win32", "MacIntel", "Linux x86_64"]),
        random.choice(["Google Inc.", "Apple Computer, Inc.", ""]),
        str(random.randint(2, 16)),  # CPU 核心数
        str(random.randint(4, 32)),  # 设备内存
        str(random.randint(0, 1)),  # 触摸屏支持
        str(uuid.uuid4()),  # 会话 ID
    ]
    return hashlib.md5("|".join(components).encode()).hexdigest()


def get_canvas_fingerprint() -> str:
    """生成逼真的 Canvas 指纹哈希"""
    # 模拟 canvas toDataURL 哈希
    seed = str(time.time()) + str(random.random())
    return hashlib.sha256(seed.encode()).hexdigest()[:32]


def get_webgl_fingerprint() -> dict:
    """生成 WebGL 指纹数据"""
    return {
        "vendor": random.choice(WEBGL_VENDORS),
        "renderer": random.choice(WEBGL_RENDERERS),
        "hash": hashlib.md5(str(random.random()).encode()).hexdigest(),
    }


def get_audio_fingerprint() -> str:
    """生成音频上下文指纹"""
    # 模拟 AudioContext 指纹
    return str(random.uniform(124.0, 124.1))[:15]


def get_full_fingerprint() -> dict:
    """生成完整的浏览器指纹用于反检测"""
    screen = random.choice(RESOLUTIONS)
    width, height = screen.split("x")

    return {
        "hash": get_fingerprint(),
        "canvas": get_canvas_fingerprint(),
        "webgl": get_webgl_fingerprint(),
        "audio": get_audio_fingerprint(),
        "screen": {
            "width": int(width),
            "height": int(height),
            "colorDepth": random.choice([24, 32]),
            "pixelRatio": random.choice([1, 1.25, 1.5, 2]),
        },
        "timezone": random.choice(TIMEZONES),
        "language": random.choice(LANGUAGES).split(",")[0],
        "platform": random.choice(["Win32", "MacIntel", "Linux x86_64"]),
        "cpuCores": random.randint(2, 16),
        "memory": random.randint(4, 32),
        "touchSupport": random.choice([True, False]),
        "sessionId": str(uuid.uuid4()),
    }


def generate_newrelic_headers() -> dict:
    """
    生成 SheerID API 所需的 NewRelic 追踪请求头
    这些请求头有助于使请求看起来像来自真实浏览器
    """
    trace_id = uuid.uuid4().hex + uuid.uuid4().hex[:8]
    trace_id = trace_id[:32]
    span_id = uuid.uuid4().hex[:16]
    timestamp = int(time.time() * 1000)

    payload = {
        "v": [0, 1],
        "d": {
            "ty": "Browser",
            "ac": "364029",
            "ap": "134291347",
            "id": span_id,
            "tr": trace_id,
            "ti": timestamp,
        },
    }

    return {
        "newrelic": base64.b64encode(json.dumps(payload).encode()).decode(),
        "traceparent": f"00-{trace_id}-{span_id}-01",
        "tracestate": f"364029@nr=0-1-364029-134291347-{span_id}----{timestamp}",
    }


def get_headers(for_sheerid: bool = True, with_auth: str = None) -> dict:
    """
    生成类浏览器请求头（正确排序）

    参数:
        for_sheerid: 如果为 True，使用 SheerID 特定的请求头
        with_auth: 用于 Authorization 请求头的 Bearer token
    """
    ua = get_random_user_agent()
    platform = random.choice(PLATFORMS)
    language = random.choice(LANGUAGES)

    # 基础请求头（像真实浏览器一样正确排序）
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": language,
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "sec-ch-ua": platform[2],
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": platform[1],
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": ua,
    }

    if for_sheerid:
        nr_headers = generate_newrelic_headers()
        headers.update(
            {
                "content-type": "application/json",
                "clientversion": "2.158.0",
                "clientname": "jslib",
                "origin": "https://services.sheerid.com",
                "referer": "https://services.sheerid.com/",
                **nr_headers,  # 包含 NewRelic 追踪请求头
            }
        )

    if with_auth:
        headers["authorization"] = f"Bearer {with_auth}"
        headers["origin"] = "https://chatgpt.com"
        headers["referer"] = "https://chatgpt.com/"
        headers["oai-device-id"] = str(uuid.uuid4())
        headers["oai-language"] = "en-US"

    return headers


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


def validate_proxy(proxy: str) -> str:
    """验证并格式化代理字符串"""
    if not proxy:
        return None

    proxy = proxy.strip()

    # 已有协议前缀
    if "://" in proxy:
        return proxy

    parts = proxy.split(":")

    # host:port 格式
    if len(parts) == 2:
        return f"http://{parts[0]}:{parts[1]}"

    # host:port:user:pass 格式
    elif len(parts) == 4:
        return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"

    # user:pass@host:port 格式（已正确，只需添加协议前缀）
    elif "@" in proxy:
        return f"http://{proxy}"

    print(f"[警告] 无效的代理格式: {proxy}")
    return None


def check_proxy_type(proxy: str) -> str:
    """
    检查代理是数据中心还是住宅类型
    返回: 'residential'、'datacenter'、'unknown'
    """
    # 这是启发式方法 - 实际检查需要 IP 数据库查询
    datacenter_indicators = [
        "vultr",
        "digitalocean",
        "linode",
        "aws",
        "azure",
        "gcp",
        "ovh",
        "hetzner",
        "contabo",
        "hostinger",
    ]

    residential_indicators = [
        "residential",
        "mobile",
        "isp",
        "roxy",
        "bright",
        "oxylabs",
        "smartproxy",
        "geosurf",
    ]

    proxy_lower = proxy.lower()

    for ind in residential_indicators:
        if ind in proxy_lower:
            return "residential"

    for ind in datacenter_indicators:
        if ind in proxy_lower:
            return "datacenter"

    return "unknown"


def get_proxy_country(proxy: str) -> str:
    """
    尝试从主机名确定代理所在国家
    返回国家代码（US、NL、UK 等）或 'unknown'
    """
    country_indicators = {
        "us": ["us.", "-us-", ".us.", "america", "united-states"],
        "nl": ["nl.", "-nl-", ".nl.", "netherlands", "dutch", "amsterdam"],
        "uk": ["uk.", "-uk-", ".uk.", "london", "britain", "england"],
        "de": ["de.", "-de-", ".de.", "germany", "frankfurt", "berlin"],
        "fr": ["fr.", "-fr-", ".fr.", "france", "paris"],
        "ca": ["ca.", "-ca-", ".ca.", "canada", "toronto"],
        "au": ["au.", "-au-", ".au.", "australia", "sydney"],
    }

    proxy_lower = proxy.lower()

    for country, indicators in country_indicators.items():
        for ind in indicators:
            if ind in proxy_lower:
                return country.upper()

    return "unknown"


def get_matched_proxy(target_country: str, proxies: list) -> str:
    """
    获取与目标国家匹配的代理（用于大学位置匹配）

    参数:
        target_country: 国家代码（US、NL、UK 等）
        proxies: 代理 URL 列表

    返回:
        匹配的代理 URL，如无匹配则返回随机代理
    """
    if not proxies:
        return None

    target = target_country.upper()
    matched = []

    for proxy in proxies:
        proxy_country = get_proxy_country(proxy)
        if proxy_country == target:
            matched.append(proxy)

    if matched:
        return random.choice(matched)

    # 无匹配 - 如果有住宅代理则返回随机住宅代理
    residential = [p for p in proxies if check_proxy_type(p) == "residential"]
    if residential:
        return random.choice(residential)

    return random.choice(proxies)


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


def get_matched_ua_for_impersonate(impersonate: str = None) -> str:
    """
    获取与我们模拟的 Chrome 版本匹配的 User-Agent

    重要: User-Agent 必须与 TLS 指纹版本匹配，
    否则 SheerID 可以检测到不匹配。
    """
    imp = impersonate or DEFAULT_IMPERSONATE

    # 提取版本号
    version = imp.replace("chrome", "").replace("edge", "").replace("safari", "")

    # 查找匹配的 UA
    for ua in USER_AGENTS_CHROME:
        if f"Chrome/{version}." in ua:
            return ua

    # 回退到第一个 Chrome UA
    return USER_AGENTS_CHROME[0]


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


FRAUD_ERROR_HELP = """\
🚨 检测到欺诈规则拒绝 (fraudRulesReject)

SheerID 的欺诈/风险引擎拒绝了此次尝试。这通常由以下一个或多个风险信号触发:
- TLS 指纹不匹配（Python HTTP 库 vs 真实浏览器）
- 数据中心 / 被标记的 IP 信誉
- 跨尝试重复使用的设备指纹 / 请求头 / NewRelic 模式
- 高重试频率或来自同一 IP 的重复失败
- 地理位置不匹配（IP 国家/地区 vs 组织）

✅ 解决方法（按顺序尝试）:
  1) 安装 curl_cffi 进行 TLS 伪装:
     pip install curl_cffi
  2) 使用住宅代理而非数据中心代理
  3) 等待 24-48 小时后再重试（风险分数通常会降低）
  4) 尝试不同的大学/组织（有些更严格）
  5) 检查您的 IP 是否被列入黑名单（如需要则更换 IP/提供商）

注意:
- 使用相同 IP + 指纹立即重试可能会使封锁持续更长时间。
- 如果无法安装 curl_cffi，预计欺诈拒绝率会高得多。
"""


def should_retry_fraud(retry_count: int):
    """判断在 fraudRulesReject 后是否应该重试。

    实现有上限的指数退避策略:
    - 30秒, 60秒, 120秒
    - 最多 3 次重试

    参数:
        retry_count: 已尝试的重试次数（从0开始）。

    返回:
        (should_retry, delay_seconds)
    """
    if retry_count < 0:
        retry_count = 0

    backoff_schedule = [30, 60, 120]

    if retry_count >= len(backoff_schedule):
        return False, 0

    return True, backoff_schedule[retry_count]


def handle_fraud_rejection(
    *,
    retry_count: int = 0,
    error_payload=None,
    message: str = None,
):
    """打印醒目的欺诈横幅和可操作的帮助信息，然后返回重试指导。

    此处理程序旨在当 SheerID 响应 `fraudRulesReject` 错误时调用。

    参数:
        retry_count: 已尝试的重试次数（从0开始）。
        error_payload: 可选的 API 错误 JSON 负载以显示（尽力而为）。
        message: 可选的人类可读消息/上下文以显示。

    返回:
        (should_retry, delay_seconds)
    """
    # ANSI 颜色（无外部依赖）。如果终端不支持 ANSI，输出仍然可读。
    red = "\x1b[31m"
    yellow = "\x1b[33m"
    cyan = "\x1b[36m"
    bold = "\x1b[1m"
    reset = "\x1b[0m"

    banner = "\n".join(
        [
            "+--------------------------------------------------------------+",
            "|                  !!! 检测到欺诈拦截 !!!                       |",
            "|               SheerID 返回 fraudRulesReject                   |",
            "+--------------------------------------------------------------+",
        ]
    )

    print(f"\n{red}{bold}{banner}{reset}")
    print(f"{yellow}❌ 验证被 SheerID 欺诈规则阻止。{reset}")

    if message:
        print(f"{cyan}🧾 上下文:{reset} {message}")

    # 尽力提取有用字段，不假设严格的模式。
    if isinstance(error_payload, dict) and error_payload:
        interesting_keys = [
            "code",
            "errorCode",
            "message",
            "detail",
            "details",
            "error",
            "errors",
        ]
        extracted = {}
        for k in interesting_keys:
            if k in error_payload and error_payload.get(k) not in (None, ""):
                extracted[k] = error_payload.get(k)

        if extracted:
            # 保持简洁，避免在控制台输出大量负载。
            print(f"{cyan}🔎 SheerID 错误负载（关键字段）:{reset}")
            for k, v in extracted.items():
                v_str = str(v)
                if len(v_str) > 400:
                    v_str = v_str[:400] + "..."
                print(f"  - {k}: {v_str}")

    print("\n" + "=" * 62)
    print(FRAUD_ERROR_HELP)
    print("=" * 62)

    should_retry, delay_seconds = should_retry_fraud(retry_count)
    if should_retry:
        print(
            f"{yellow}⏳ 建议重试:{reset} 第 #{retry_count + 1}/3 次，{delay_seconds}秒后"
        )
        print(
            f"{yellow}💡 提示:{reset} 重试前请更换 IP/指纹；避免快速连续重试。"
        )
    else:
        print(f"{red}🛑 已达最大重试次数。{reset} 请勿继续发送请求。")
        print(
            f"{yellow}✅ 最佳下一步:{reset} 等待 24-48 小时并更换 IP/指纹。"
        )

    return should_retry, delay_seconds


if __name__ == "__main__":
    # 测试
    print("\n" + "=" * 60)
    print(" 反检测模块测试 ")
    print("=" * 60 + "\n")

    print_anti_detect_info()

    print(f"示例指纹:")
    print(f"  基础哈希: {get_fingerprint()}")
    print(f"  Canvas 指纹: {get_canvas_fingerprint()}")
    print(f"  音频指纹: {get_audio_fingerprint()}")

    webgl = get_webgl_fingerprint()
    print(f"  WebGL 厂商: {webgl['vendor']}")
    print(f"  WebGL 渲染器: {webgl['renderer'][:40]}...")

    print(f"\n示例 User-Agent:")
    ua = get_matched_ua_for_impersonate()
    print(f"  {ua[:70]}...")

    print(f"\n示例请求头 (SheerID):")
    headers = get_headers(for_sheerid=True)
    for k, v in list(headers.items())[:8]:
        print(f"  {k}: {str(v)[:50]}{'...' if len(str(v)) > 50 else ''}")

    print(f"\nNewRelic 请求头:")
    nr = generate_newrelic_headers()
    print(f"  traceparent: {nr['traceparent'][:50]}...")

    print("\n" + "=" * 60)
    print(" 建议 ")
    print("=" * 60)
    print("""
1. 安装 curl_cffi 进行 TLS 伪装:
   pip install curl_cffi

2. 使用住宅代理（数据中心 IP 经常被阻止）

3. 将代理位置与大学所在国家匹配

4. 每次验证尝试生成唯一指纹
""")
