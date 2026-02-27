"""
SheerID 验证工具 - 反检测模块

功能:
- 随机 User-Agent 轮换 (Chrome, Firefox, Edge, Safari)
- 浏览器级请求头排序
- 浏览器指纹生成 (Canvas/WebGL/Audio)
- 人类行为模拟延迟
- TLS 指纹伪装 (curl_cffi Chrome 模拟)
- NewRelic 追踪头 (SheerID 必需)
- 代理验证与格式化

用法:
    from anti_detect import get_headers, get_fingerprint, random_delay, create_session
    from anti_detect import generate_newrelic_headers
    from anti_detect import make_request

重要: 必须安装 curl_cffi 以伪装 TLS 指纹:
    pip install curl_cffi
"""

# 公共 API 导出 - 保持向后兼容
from .fingerprint import (
    get_audio_fingerprint,
    get_canvas_fingerprint,
    get_fingerprint,
    get_full_fingerprint,
    get_webgl_fingerprint,
)
from .fraud import FRAUD_ERROR_HELP, handle_fraud_rejection, should_retry_fraud
from .headers import (
    generate_newrelic_headers,
    get_headers,
    get_matched_ua_for_impersonate,
    get_random_user_agent,
)
from .proxy import (
    check_proxy_type,
    get_matched_proxy,
    get_proxy_country,
    validate_proxy,
)
from .session import (
    create_session,
    generate_student_email,
    get_random_impersonate,
    make_request,
    print_anti_detect_info,
    random_delay,
    warm_session,
)

__all__ = [
    # fingerprint
    "get_fingerprint",
    "get_canvas_fingerprint",
    "get_webgl_fingerprint",
    "get_audio_fingerprint",
    "get_full_fingerprint",
    # headers
    "get_random_user_agent",
    "generate_newrelic_headers",
    "get_headers",
    "get_matched_ua_for_impersonate",
    # proxy
    "validate_proxy",
    "check_proxy_type",
    "get_proxy_country",
    "get_matched_proxy",
    # session
    "random_delay",
    "get_random_impersonate",
    "create_session",
    "print_anti_detect_info",
    "make_request",
    "warm_session",
    "generate_student_email",
    # fraud
    "FRAUD_ERROR_HELP",
    "should_retry_fraud",
    "handle_fraud_rejection",
]
