"""
proxy_checker.validator — 代理字符串验证与解析

支持多种常见代理格式的统一解析。
"""

import logging
from typing import Optional
from urllib.parse import urlparse

from .models import ProxyInfo

logger = logging.getLogger(__name__)


def parse_proxy(proxy: str) -> Optional[ProxyInfo]:
    """
    解析代理字符串为 ProxyInfo，支持多种格式。

    支持格式:
        - http://host:port
        - http://user:pass@host:port
        - socks5://host:port
        - host:port
        - host:port:user:pass
        - user:pass@host:port

    Args:
        proxy: 代理字符串

    Returns:
        ProxyInfo 或 None (格式无效时)
    """
    if not proxy or not proxy.strip():
        logger.debug("代理解析: 输入为空")
        return None

    proxy = proxy.strip()

    # ── 已包含协议前缀 → 用 urlparse 解析 ──
    if "://" in proxy:
        result = _parse_url(proxy)
        logger.debug("代理解析 (URL格式): host=%s, port=%d", result.host if result else "N/A", result.port if result else 0)
        return result

    # ── host:port ──
    parts = proxy.split(":")
    if len(parts) == 2:
        host, port = parts
        result = _build_proxy_info(f"http://{host}:{port}", "http", host, port)
        logger.debug("代理解析 (host:port): host=%s, port=%s", host, port)
        return result

    # ── host:port:user:pass ──
    if len(parts) == 4:
        host, port, user, pwd = parts
        url = f"http://{user}:{pwd}@{host}:{port}"
        result = _build_proxy_info(url, "http", host, port, user, pwd)
        logger.debug("代理解析 (host:port:user:pass): host=%s, port=%s, user=%s", host, port, user)
        return result

    # ── user:pass@host:port ──
    if "@" in proxy:
        url = f"http://{proxy}"
        result = _parse_url(url)
        logger.debug("代理解析 (user:pass@host:port): host=%s", result.host if result else "N/A")
        return result

    logger.debug("代理解析: 无法识别的格式: %s", proxy[:30])
    return None


# ────────────────────────────────────────────
# 内部工具函数
# ────────────────────────────────────────────

def _parse_url(url: str) -> Optional[ProxyInfo]:
    """通过 urlparse 解析完整 URL"""
    parsed = urlparse(url)
    if not parsed.hostname:
        return None
    return ProxyInfo(
        url=url,
        protocol=parsed.scheme or "http",
        host=parsed.hostname,
        port=parsed.port or 0,
        username=parsed.username,
        password=parsed.password,
    )


def _build_proxy_info(
    url: str,
    protocol: str,
    host: str,
    port_str: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> Optional[ProxyInfo]:
    """构建 ProxyInfo，捕获端口解析错误"""
    try:
        port = int(port_str)
    except ValueError:
        return None
    return ProxyInfo(
        url=url,
        protocol=protocol,
        host=host,
        port=port,
        username=username,
        password=password,
    )
