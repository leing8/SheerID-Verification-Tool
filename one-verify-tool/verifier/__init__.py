"""
验证器模块包 - SheerID 验证

导出验证器类和函数
"""

from .university import (
    select_university,
    fraud_tracker,
    FraudTracker,
    validate_university_ip_match,
    get_university_by_name,
    get_universities_by_country,
)
from .gemini import GeminiVerifier
