"""
模板系统初始化和导出
"""

from .base_template import UniversityTemplate
from .harvard_template import HarvardTemplate, harvard_template
from .us_generic import USGenericTemplate, default_us_template

__all__ = [
    "UniversityTemplate",
    "USGenericTemplate",
    "default_us_template",
    "HarvardTemplate",
    "harvard_template",
]
