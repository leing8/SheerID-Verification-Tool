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

# 配置常量
from .config import (
    CHROME_VERSIONS,
    IMPERSONATE_OPTIONS,
    DEFAULT_IMPERSONATE,
    USER_AGENTS_CHROME,
    USER_AGENTS,
    RESOLUTIONS,
    TIMEZONES,
    LANGUAGES,
    PLATFORMS,
    WEBGL_VENDORS,
    WEBGL_RENDERERS,
    UA_PLATFORM_MAP,
    CHROME_VERSION_SEC_CH_UA,
    COMMON_FONTS_WINDOWS,
    COMMON_FONTS_MAC,
    COMMON_PLUGINS,
    NAVIGATOR_PROPERTIES,
)
# 指纹生成
from .fingerprint import (
    get_fingerprint,
    get_canvas_fingerprint,
    get_webgl_fingerprint,
    get_audio_fingerprint,
    get_fonts_fingerprint,
    get_plugins_fingerprint,
    get_webrtc_fingerprint,
    get_navigator_fingerprint,
    get_screen_fingerprint,
    get_timezone_fingerprint,
    get_full_fingerprint,
    # 新增：设备档案模块
    DeviceProfile,
    GPUProfile,
    GPU_PROFILES,
    generate_device_profile,
)
# 欺诈处理
from .fraud import (
    FRAUD_ERROR_HELP,
    should_retry_fraud,
    handle_fraud_rejection,
)
# 请求头生成
from .headers import (
    generate_newrelic_headers,
    get_headers,
    get_matched_ua_for_impersonate,
)
# 代理工具
from .proxy import (
    validate_proxy,
    check_proxy_type,
    get_proxy_country,
    get_matched_proxy,
)
# 会话管理
from .session import (
    random_delay,
    get_random_impersonate,
    create_session,
    make_request,
    warm_session,
    print_anti_detect_info,
)

__all__ = [
    # 配置
    "CHROME_VERSIONS",
    "IMPERSONATE_OPTIONS",
    "DEFAULT_IMPERSONATE",
    "USER_AGENTS_CHROME",
    "USER_AGENTS",
    "RESOLUTIONS",
    "TIMEZONES",
    "LANGUAGES",
    "PLATFORMS",
    "WEBGL_VENDORS",
    "WEBGL_RENDERERS",
    "UA_PLATFORM_MAP",
    "CHROME_VERSION_SEC_CH_UA",
    "COMMON_FONTS_WINDOWS",
    "COMMON_FONTS_MAC",
    "COMMON_PLUGINS",
    "NAVIGATOR_PROPERTIES",
    # 指纹
    "get_fingerprint",
    "get_canvas_fingerprint",
    "get_webgl_fingerprint",
    "get_audio_fingerprint",
    "get_fonts_fingerprint",
    "get_plugins_fingerprint",
    "get_webrtc_fingerprint",
    "get_navigator_fingerprint",
    "get_screen_fingerprint",
    "get_timezone_fingerprint",
    "get_full_fingerprint",
    # 设备档案
    "DeviceProfile",
    "GPUProfile",
    "GPU_PROFILES",
    "generate_device_profile",
    # 请求头
    "generate_newrelic_headers",
    "get_headers",
    "get_matched_ua_for_impersonate",
    # 代理
    "validate_proxy",
    "check_proxy_type",
    "get_proxy_country",
    "get_matched_proxy",
    # 会话
    "random_delay",
    "get_random_impersonate",
    "create_session",
    "make_request",
    "warm_session",
    "print_anti_detect_info",
    # 欺诈
    "FRAUD_ERROR_HELP",
    "should_retry_fraud",
    "handle_fraud_rejection",
]

if __name__ == "__main__":
    # 测试
    print("\n" + "=" * 60)
    print(" 反检测模块测试 ")
    print("=" * 60 + "\n")

    print_anti_detect_info()

    # 测试用种子（模拟 verificationId）
    _test_seed = "test_verification_id_12345"

    print(f"示例指纹:")
    print(f"  基础哈希: {get_fingerprint(_test_seed)}")
    print(f"  Canvas 指纹: {get_canvas_fingerprint(_test_seed)}")
    print(f"  音频指纹: {get_audio_fingerprint(_test_seed)}")

    webgl = get_webgl_fingerprint(_test_seed)
    print(f"  WebGL 厂商: {webgl['vendor']}")
    print(f"  WebGL 渲染器: {webgl['renderer'][:40]}...")

    print(f"\n示例 User-Agent:")
    ua = get_matched_ua_for_impersonate()
    print(f"  {ua[:70]}...")

    print(f"\n示例请求头 (SheerID):")
    headers = get_headers()
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
