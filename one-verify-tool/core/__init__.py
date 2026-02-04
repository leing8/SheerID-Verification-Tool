"""
核心模块包 - 反检测和会话管理

导出所有核心功能供外部使用
"""

# 常量
from .constants import (
    HAS_CURL_CFFI,
    PROGRAM_ID,
    SHEERID_API_URL,
    MIN_DELAY,
    MAX_DELAY,
    TYPING_MIN_DELAY,
    TYPING_MAX_DELAY,
    PAGE_READ_DELAY,
    RATE_LIMIT_CONFIG,
    DEFAULT_IMPERSONATE,
    CHROME_VERSIONS,
    USER_AGENTS,
    USER_AGENTS_CHROME,
    RESOLUTIONS,
    SCREEN_CONFIGS,
    US_TIMEZONES,
    US_TIMEZONE_NAMES,
    LANGUAGES,
    PLATFORMS,
    PLATFORMS_LEGACY,
    SEC_CH_UA_TEMPLATES,
    WEBGL_CONFIGS,
    WEBGL_VENDORS,
    WEBGL_RENDERERS,
    WEBGL_EXTENSIONS,
    NAVIGATOR_PROPS,
    NAVIGATOR_PLUGINS,
    AUDIO_CONTEXT_CONFIG,
)

# 指纹
from .fingerprint import (
    BrowserProfile,
    get_or_create_profile,
    reset_profile,
    create_new_profile,
    get_random_user_agent,
    get_fingerprint,
    get_canvas_fingerprint,
    get_webgl_fingerprint,
    get_audio_fingerprint,
    get_full_fingerprint,
    get_matched_ua_for_impersonate,
)

# 请求头
from .headers import (
    generate_newrelic_headers,
    get_headers,
    get_headers_with_profile,
    get_resource_headers,
    get_navigation_headers,
)

# 延迟
from .delay import (
    random_delay,
    typing_delay,
    reading_delay,
    interaction_delay,
    wait_between_requests,
    simulate_form_fill_timing,
    get_human_delay_pattern,
)

# 代理
from .proxy import (
    validate_proxy,
    check_proxy_type,
    get_proxy_country,
)

# 会话
from .session import (
    SessionManager,
    create_session,
    warm_session,
    warm_session_enhanced,
    make_request,
)

# 欺诈处理
from .fraud import (
    should_retry_fraud,
    handle_fraud_rejection,
)


def check_anti_detect_status() -> dict:
    """检查反检测模块状态"""
    status = {
        "curl_cffi": HAS_CURL_CFFI,
        "expected_success_rate": "65-85%" if HAS_CURL_CFFI else "5-20%",
        "recommendation": None if HAS_CURL_CFFI else "pip install curl_cffi",
        "features": {
            "tls_fingerprint": HAS_CURL_CFFI,
            "browser_profile": True,
            "human_delays": True,
            "rate_limiting": True,
            "header_ordering": True,
            "client_hints": True,
        },
    }
    return status


def require_curl_cffi():
    """强制要求 curl_cffi（未安装则退出）"""
    import sys
    if not HAS_CURL_CFFI:
        print("\n" + "=" * 60)
        print("❌ 致命错误: curl_cffi 未安装")
        print("=" * 60)
        print("此工具需要 curl_cffi 进行 TLS 指纹伪装。")
        print("请安装: pip install curl_cffi")
        print("=" * 60)
        sys.exit(1)


def create_verification_session(proxy: str = None, impersonate: str = None) -> SessionManager:
    """
    创建验证会话的便捷函数
    
    Args:
        proxy: 代理 URL
        impersonate: Chrome 版本
    
    Returns:
        SessionManager: 配置好的会话管理器
    """
    return SessionManager(proxy=proxy, impersonate=impersonate)
