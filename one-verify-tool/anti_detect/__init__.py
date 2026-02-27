"""
SheerID 验证工具 - 反检测模块

功能:
- TLS 指纹伪装 (curl_cffi Chrome 模拟)
- 代理验证与格式化
- 欺诈拒绝处理与重试
- 会话创建与预热

注意: 指纹和请求头生成已迁移到 device_fingerprint 模块。

用法:
    from anti_detect import create_session, handle_fraud_rejection, should_retry_fraud
"""

# 公共 API 导出
from .fraud import FRAUD_ERROR_HELP, handle_fraud_rejection, should_retry_fraud
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
    # session
    "random_delay",
    "get_random_impersonate",
    "create_session",
    "print_anti_detect_info",
    "make_request",
    "warm_session",
    "generate_student_email",
    # proxy
    "validate_proxy",
    "check_proxy_type",
    "get_proxy_country",
    "get_matched_proxy",
    # fraud
    "FRAUD_ERROR_HELP",
    "should_retry_fraud",
    "handle_fraud_rejection",
]
