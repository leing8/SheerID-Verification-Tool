"""
反检测模块 - 会话管理

HTTP 会话创建，强制使用 curl_cffi + Chrome TLS 模拟。
curl_cffi 不可用时退出程序。

关于 JA4 指纹：
    curl_cffi 通过 impersonate 参数完整复制 Chrome 的 TLS Client Hello：
    - TLS 版本、加密套件列表及顺序
    - TLS 扩展列表及顺序 (JA4 依据此排序计算哈希)
    - 椭圆曲线、签名算法
    - ALPS/GREASE 扩展
    
    因此 JA3 和 JA4 哈希值均与真实 Chrome 一致，
    无需在 Python 层做额外处理。
"""

import random
import sys
import time

from .constants import (
    CHROME_VERSIONS,
    DEFAULT_IMPERSONATE,
    IMPERSONATE_OPTIONS,
    USER_AGENTS,
)

# 强制检查 curl_cffi
try:
    from curl_cffi import requests as curl_requests
except ImportError:
    print("\n" + "=" * 60)
    print("❌ 致命错误: curl_cffi 未安装!")
    print("=" * 60)
    print("curl_cffi 是必需依赖，用于伪装 TLS 指纹 (JA3/JA4)。")
    print("无此依赖，SheerID 会直接识别 Python 流量并拒绝请求。")
    print("")
    print("安装: pip install curl_cffi")
    print("=" * 60 + "\n")
    sys.exit(1)


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
    创建 curl_cffi HTTP 会话，强制使用 Chrome TLS 模拟。

    curl_cffi 在 C 层完整复制 Chrome 的 TLS 栈，包括：
    - JA3 哈希: TLS 版本 + 加密套件 + 扩展 + 椭圆曲线
    - JA4 哈希: 对浏览器扩展排序后计算，抗随机化
    - HTTP/2 帧: SETTINGS、WINDOW_UPDATE、PRIORITY 帧顺序
    - ALPS/GREASE: Chrome 特有的 TLS 扩展

    Args:
        proxy: 代理 URL
        impersonate: Chrome 模拟版本 (如 "chrome131")，
                     应与 DeviceIdentity 的 Chrome 版本一致

    Returns:
        tuple: (session, "curl_cffi", 模拟版本)
    """
    from .proxy import check_proxy_type, validate_proxy

    # 验证并格式化代理
    proxy = validate_proxy(proxy)
    proxies = None
    if proxy:
        proxies = {"http": proxy, "https": proxy, "all://": proxy}

        proxy_type = check_proxy_type(proxy)
        if proxy_type == "datacenter":
            print("[警告] ⚠️  检测到数据中心代理! SheerID 可能拒绝请求")
            print("[警告]    强烈建议使用住宅代理")

    # 使用传入的模拟版本或默认值
    imp_version = impersonate or DEFAULT_IMPERSONATE

    try:
        if proxies:
            session = curl_requests.Session(
                proxies=proxies, impersonate=imp_version
            )
        else:
            session = curl_requests.Session(impersonate=imp_version)

        print(f"[反检测] ✅ curl_cffi TLS 模拟: {imp_version}")
        print(f"[反检测]    JA3/JA4 指纹 = 真实 Chrome {imp_version.replace('chrome', '')}")
        return session, "curl_cffi", imp_version

    except Exception as e:
        print(f"\n❌ 致命错误: curl_cffi 模拟版本 '{imp_version}' 失败: {e}")
        print(f"请更新 curl_cffi: pip install --upgrade curl_cffi")
        sys.exit(1)


def print_anti_detect_info():
    """打印反检测配置信息"""
    session, lib, imp = create_session()
    print(f"\n{'=' * 50}")
    print(f"反检测配置信息")
    print(f"{'=' * 50}")
    print(f"  HTTP 库: {lib} (强制)")
    print(f"  TLS 模拟: {imp}")
    print(f"  JA3/JA4: 匹配真实 Chrome")
    print(f"  User-Agent: {len(USER_AGENTS)} 个变体")
    print(f"  Chrome 版本: {len(CHROME_VERSIONS)} 个可用")
    print(f"\n  ✅ TLS 指纹: 已伪装为 {imp}")
    print(f"  ✅ 检测风险: 低")
    print(f"{'=' * 50}\n")

    # 清理资源
    if hasattr(session, "close"):
        session.close()


def make_request(session, method: str, url: str, impersonate: str = None, **kwargs):
    """
    发送 HTTP 请求，为 curl_cffi 自动应用模拟参数

    Args:
        session: create_session() 返回的 HTTP 会话
        method: HTTP 方法
        url: 请求 URL
        impersonate: Chrome 模拟版本 (仅 curl_cffi 有效)
        **kwargs: 其他参数
    """
    imp = impersonate or DEFAULT_IMPERSONATE
    try:
        return session.request(method, url, impersonate=imp, **kwargs)
    except TypeError:
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
    """生成与大学域名匹配的学生邮箱"""
    first = first_name.lower().strip()
    last = last_name.lower().strip()

    domain = university.get("domain", "") if university else ""

    if not domain:
        # 通用邮箱提供商
        domains = ["gmail.com", "outlook.com", "yahoo.com", "icloud.com"]
        domain = random.choice(domains)

    # 常见大学邮箱格式
    patterns = [
        f"{first[0]}{last}@{domain}",
        f"{first}.{last}@{domain}",
        f"{first}{last[0]}@{domain}",
        f"{first}_{last}@{domain}",
        f"{last}{first[0]}@{domain}",
        f"{first}{random.randint(1, 99)}@{domain}",
    ]

    return random.choice(patterns)
