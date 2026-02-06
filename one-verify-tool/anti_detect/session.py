"""
会话管理模块
创建 HTTP 会话、TLS 伪装和请求发送
"""

import random
import time

# 强制导入 numpy
try:
    import numpy as np
except ImportError:
    raise ImportError(
        "numpy 未安装，无法继续运行。\n"
        "请运行: pip install numpy"
    )

from .config import DEFAULT_IMPERSONATE, IMPERSONATE_OPTIONS
from .headers import get_headers
from .proxy import validate_proxy, check_proxy_type


def random_delay(min_ms: int = 300, max_ms: int = 1200):
    """
    使用 Gamma 分布的随机延迟以模拟人类行为
    Gamma 分布比均匀随机更逼真
    """
    # Gamma 分布更好地模拟人类反应时间
    shape, scale = 2.0, (max_ms - min_ms) / 4000
    delay = min_ms / 1000 + np.random.gamma(shape, scale)
    delay = min(delay, max_ms / 1000)  # 限制最大值

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
    使用 curl_cffi 创建 HTTP 会话（强制要求）

    curl_cffi 是通过 SheerID 验证的必要条件，没有它 TLS 指纹会被检测。

    参数:
        proxy: 代理 URL（如需要会进行格式化）
        impersonate: 要模拟的 Chrome 版本（如 "chrome131"）
                    如果为 None，使用 DEFAULT_IMPERSONATE

    返回:
        tuple: (session, library_name, impersonate_version)

    异常:
        ImportError: 如果 curl_cffi 未安装
        RuntimeError: 如果无法创建有效会话
    """
    # 强制导入 curl_cffi，不提供降级方案
    from curl_cffi import requests as curl_requests

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

    # 确定模拟版本（强制使用最新版本，不降级）
    imp_version = impersonate or DEFAULT_IMPERSONATE

    # 创建会话（强制成功，失败则报错）
    if proxies:
        session = curl_requests.Session(proxies=proxies, impersonate=imp_version)
    else:
        session = curl_requests.Session(impersonate=imp_version)

    print(f"[反检测] ✅ 使用 curl_cffi，模拟 {imp_version}")
    print(f"[反检测]    TLS 指纹将匹配真实 Chrome 浏览器")
    return session, "curl_cffi", imp_version


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

    # 强制要求 curl_cffi 会话
    session_type = type(session).__module__

    if "curl_cffi" not in session_type:
        raise RuntimeError(
            "会话类型无效，必须使用 curl_cffi 创建会话。"
            "\n请通过 create_session() 创建会话。"
        )
    
    # curl_cffi 支持每请求模拟
    try:
        return session.request(method, url, impersonate=imp, **kwargs)
    except TypeError:
        # 旧版本不支持每请求模拟
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
    hdrs = headers or get_headers()

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


# generate_student_email 已移除，请使用 utils.py 中的 generate_email


def print_anti_detect_info():
    """打印反检测配置信息"""
    from .config import CHROME_VERSIONS, USER_AGENTS, RESOLUTIONS
    
    session, lib, imp = create_session()
    print(f"\n{'=' * 50}")
    print(f"反检测配置")
    print(f"{'=' * 50}")
    print(f"  HTTP 库: {lib}")
    print(f"  模拟: {imp}")
    print(f"  User-Agent: {len(USER_AGENTS)} 种变体")
    print(f"  分辨率: {len(RESOLUTIONS)} 种变体")
    print(f"  Chrome 版本: {len(CHROME_VERSIONS)} 个可用")
    print(f"\n  ✅ TLS 指纹: 伪装为 {imp}")
    print(f"  ✅ 检测风险: 低")
    print(f"{'=' * 50}\n")

    # 清理
    if hasattr(session, "close"):
        session.close()
