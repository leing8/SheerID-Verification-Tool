"""
anti_detect.proxy — 代理验证与类型检测桥接模块

此模块是 common/proxy_checker 的轻量适配层，
为 session.py 提供所需的 validate_proxy() 和 check_proxy_type()。

说明:
  代理完整检测功能（含地理位置、声誉评分等）在 common/proxy_checker 模块中。
  此模块仅暴露 session.py 启动时需要的同步轻量接口。
"""

import sys
from pathlib import Path

# 确保 common 目录在路径中
_COMMON_DIR = Path(__file__).resolve().parent.parent.parent / "common"
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from proxy_checker.validator import parse_proxy
from proxy_checker.reputation import evaluate_reputation


def validate_proxy(proxy: str) -> str:
    """验证并规范化代理字符串。

    - 为裸 host:port 格式自动补全 http:// 协议头
    - 格式无效时返回原始字符串（交由 curl_cffi 处理）

    Args:
        proxy: 原始代理字符串 (或 None)

    Returns:
        规范化后的代理 URL 字符串，或 None
    """
    if not proxy:
        return None

    info = parse_proxy(proxy)
    if info:
        return info.url

    # 无法解析时原样返回，避免屏蔽合法格式
    return proxy


def check_proxy_type(proxy: str) -> str:
    """快速判断代理类型（不发起网络请求）。

    仅通过代理主机名关键词进行静态判断，
    无需 geo API 调用，速度极快。

    Args:
        proxy: 代理 URL 字符串

    Returns:
        "datacenter" | "residential" | "mobile" | "isp" | "unknown"
    """
    if not proxy:
        return "unknown"

    info = parse_proxy(proxy)
    hostname = info.host if info else proxy

    # 用主机名做静态声誉评估（org 留空）
    result = evaluate_reputation(org="", hostname=hostname)
    return result.proxy_type.value
