"""
模板系统初始化和导出
"""

from .base_template import UniversityTemplate
from .us_generic import USGenericTemplate, default_us_template

__all__ = [
    "UniversityTemplate",
    "USGenericTemplate",
    "default_us_template",
]
