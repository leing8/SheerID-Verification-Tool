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


def create_session(proxy: str = None, impersonate: str = None):
    """
    创建 curl_cffi HTTP 会话，强制使用 Chrome TLS 模拟。

    curl_cffi 在 C 层完整复制 Chrome 的 TLS 栈，包括：
    - JA3 哈希: TLS 版本 + 加密套件 + 扩展 + 椭圆曲线
    - JA4 哈希: 对浏览器扩展排序后计算，抗随机化
    - HTTP/2 帧: SETTINGS、WINDOW_UPDATE、PRIORITY 帧顺序
    - ALPS/GREASE: Chrome 特有的 TLS 扩展

    Args:
        proxy:       代理 URL
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

    # 使用传入的模拟版本，回退到 curl_cffi 默认 Chrome
    imp_version = impersonate or "chrome131"

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
        print("请更新 curl_cffi: pip install --upgrade curl_cffi")
        sys.exit(1)


def warm_session(
    session,
    program_id: str = None,
    verification_id: str = None,
    headers: dict = None,
):
    """
    预热会话，复现真实 Chrome 加载 SheerID 验证页面时的 GET 请求序列。

    基于 SheerID 官方 API Quickstart 文档的推荐请求顺序:
      1. GET /program/{programId}/theme   — 官方第一个推荐的 GET，获取程序主题
      2. GET /verification/{verificationId} — 浏览器加载时读取当前验证状态
      3. GET /organization/search          — 用户聚焦到学校输入框时触发的搜索

    ADP (受众数据平台) 会将"没有背景 GET 请求直接 POST 提交"标记为高风险。
    此函数通过复现上述序列建立正常的请求上下文。

    Args:
        session:         create_session() 返回的 HTTP 会话
        program_id:      SheerID 项目 ID
        verification_id: 当前验证 ID（用于复现 GET /verification/{id}）
        headers:         DeviceIdentity 生成的完整请求头
    """
    base_url = "https://services.sheerid.com/rest/v2"
    hdrs = headers or {"Content-Type": "application/json"}

    if program_id:
        try:
            # 步骤 1: 获取程序主题 (官方文档推荐的首个 GET 请求)
            # 参考: https://developer.sheerid.com/api-quickstart#retrieve-theme
            session.get(
                f"{base_url}/program/{program_id}/theme",
                headers=hdrs,
                timeout=10,
            )
            random_delay(600, 1200)
        except Exception:
            pass

    if verification_id:
        try:
            # 步骤 2: 读取当前验证状态 (浏览器页面加载时必然发生)
            # 参考: https://developer.sheerid.com/api-quickstart#retrieve-verification-segment
            session.get(
                f"{base_url}/verification/{verification_id}",
                headers=hdrs,
                timeout=10,
            )
            random_delay(400, 900)
        except Exception:
            pass

    try:
        # 步骤 3: 组织搜索 (模拟用户点击/聚焦学校输入框时的空搜索)
        params = {"country": "US", "term": ""}
        if program_id:
            params["programId"] = program_id
        session.get(
            f"{base_url}/organization/search",
            params=params,
            headers=hdrs,
            timeout=10,
        )
        random_delay(300, 700)
    except Exception:
        pass

    return session
