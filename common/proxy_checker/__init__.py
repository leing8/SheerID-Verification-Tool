"""
proxy_checker — 代理 IP 检测公共模块

检测代理 IP 的位置、来源、属性、纯净度。
支持可选的主线程同步或子线程异步检测。

用法:
    from proxy_checker import ProxyChecker, parse_proxy, print_result

    # 解析代理地址
    info = parse_proxy("http://user:pass@host:port")

    # 同步检测
    checker = ProxyChecker()
    result = checker.check(session, expected_country="US")
    print_result(result)

    # 异步检测 (自动打印)
    checker.check_async(session, expected_country="US")
"""

from .checker import ProxyChecker
from .formatter import format_result, print_result
from .geo import detect_geo, infer_country_from_hostname
from .models import (
    GeoResult,
    ProxyCheckResult,
    ProxyInfo,
    ProxyType,
    ReputationResult,
    RiskLevel,
)
from .reputation import evaluate_reputation
from .validator import parse_proxy

__all__ = [
    # 主入口
    "ProxyChecker",
    # 解析
    "parse_proxy",
    # 检测
    "detect_geo",
    "infer_country_from_hostname",
    "evaluate_reputation",
    # 格式化
    "format_result",
    "print_result",
    # 数据模型
    "ProxyInfo",
    "GeoResult",
    "ReputationResult",
    "ProxyCheckResult",
    "ProxyType",
    "RiskLevel",
]
