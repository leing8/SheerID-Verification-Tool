# one-verify-tool 包初始化
"""
Google One (Gemini) 学生认证工具
SheerID 学生身份验证 - 用于获取 Google One AI Premium
"""

from .config import PROGRAM_ID, SHEERID_API_URL
from .stats import stats
from .verifier import GeminiVerifier

__all__ = [
    "GeminiVerifier",
    "stats",
    "PROGRAM_ID",
    "SHEERID_API_URL",
]
