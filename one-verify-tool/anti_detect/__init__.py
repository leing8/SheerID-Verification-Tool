"""
SheerID 验证工具 - 反检测模块

功能:
- TLS 指纹伪装 (curl_cffi Chrome 模拟)
- 欺诈拒绝诊断输出（fraudRulesReject 为不可恢复错误，不重试）
- 会话创建与预热

注意: 指纹和请求头生成已迁移到 common/device_fingerprint_factory 模块。
注意: 代理检测功能已迁移到 common/proxy_checker 公共模块。

用法:
    from anti_detect import create_session, handle_fraud_rejection
"""

# 公共 API 导出
from .fraud import FRAUD_ERROR_HELP, handle_fraud_rejection
from .session import (
    create_session,
    random_delay,
    warm_session,
)

__all__ = [
    # session
    "random_delay",
    "create_session",
    "warm_session",
    # fraud
    "FRAUD_ERROR_HELP",
    "handle_fraud_rejection",
]
