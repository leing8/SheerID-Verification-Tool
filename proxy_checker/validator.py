"""
proxy_checker.validator — 代理字符串验证与解析

支持多种常见代理格式的统一解析。
"""

from typing import Optional
from urllib.parse import urlparse

from .models import ProxyInfo


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
        return None

    proxy = proxy.strip()

    # ── 已包含协议前缀 → 用 urlparse 解析 ──
    if "://" in proxy:
        return _parse_url(proxy)

    # ── host:port ──
    parts = proxy.split(":")
    if len(parts) == 2:
        host, port = parts
        return _build_proxy_info(f"http://{host}:{port}", "http", host, port)

    # ── host:port:user:pass ──
    if len(parts) == 4:
        host, port, user, pwd = parts
        url = f"http://{user}:{pwd}@{host}:{port}"
        return _build_proxy_info(url, "http", host, port, user, pwd)

    # ── user:pass@host:port ──
    if "@" in proxy:
        url = f"http://{proxy}"
        return _parse_url(url)

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
