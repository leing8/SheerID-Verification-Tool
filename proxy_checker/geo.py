"""
proxy_checker.geo — 地理位置检测

通过代理发起真实 HTTP 请求，检测出口 IP 的地理位置。
支持多 API 源故障转移。
"""

from typing import Callable, Dict, List, Tuple

from .models import GeoResult

# ── API 源定义 ──────────────────────────────
# 每项: (URL, 解析函数)

_API_SOURCES: List[Tuple[str, Callable[[Dict], GeoResult]]] = [
    (
        "https://ipapi.co/json/",
        lambda d: GeoResult(
            ip=d.get("ip", "unknown"),
            country=d.get("country_code", "unknown"),
            city=d.get("city", "unknown"),
            region=d.get("region", ""),
            org=d.get("org", ""),
            timezone=d.get("timezone", ""),
        ),
    ),
    (
        "https://ipinfo.io/json",
        lambda d: GeoResult(
            ip=d.get("ip", "unknown"),
            country=d.get("country", "unknown"),
            city=d.get("city", "unknown"),
            region=d.get("region", ""),
            org=d.get("org", ""),
            timezone=d.get("timezone", ""),
        ),
    ),
    (
        "http://ip-api.com/json/?fields=query,country,countryCode,city,regionName,org,isp,timezone",
        lambda d: GeoResult(
            ip=d.get("query", "unknown"),
            country=d.get("countryCode", "unknown"),
            city=d.get("city", "unknown"),
            region=d.get("regionName", ""),
            org=d.get("org", "") or d.get("isp", ""),
            timezone=d.get("timezone", ""),
        ),
    ),
]


def detect_geo(session, *, timeout: int = 8) -> GeoResult:
    """
    通过代理发起 HTTP 请求，检测出口 IP 的真实地理位置。

    多 API 源自动故障转移: ipapi.co → ipinfo.io → ip-api.com

    Args:
        session: 已配置代理的 HTTP 会话 (需支持 .get() 方法)
        timeout: 请求超时秒数

    Returns:
        GeoResult，所有 API 均失败时返回默认值 (ip="unknown", ...)
    """
    for url, parser in _API_SOURCES:
        try:
            resp = session.get(url, timeout=timeout)
            data = resp.json()
            result = parser(data)
            # 规范化国家代码为大写
            result.country = result.country.upper() if result.country else "UNKNOWN"
            return result
        except Exception:
            continue

    return GeoResult()


def infer_country_from_hostname(proxy: str) -> str:
    """
    从代理主机名推断国家代码 (快速推断，不发 HTTP 请求)。

    仅作辅助参考，准确性有限。

    Args:
        proxy: 代理 URL 或主机名

    Returns:
        国家代码 (大写) 或 "UNKNOWN"
    """
    _COUNTRY_INDICATORS = {
        "US": ["us.", "-us-", ".us.", "america", "united-states"],
        "NL": ["nl.", "-nl-", ".nl.", "netherlands", "dutch", "amsterdam"],
        "UK": ["uk.", "-uk-", ".uk.", "london", "britain", "england"],
        "DE": ["de.", "-de-", ".de.", "germany", "frankfurt", "berlin"],
        "FR": ["fr.", "-fr-", ".fr.", "france", "paris"],
        "CA": ["ca.", "-ca-", ".ca.", "canada", "toronto"],
        "AU": ["au.", "-au-", ".au.", "australia", "sydney"],
        "JP": ["jp.", "-jp-", ".jp.", "japan", "tokyo"],
        "SG": ["sg.", "-sg-", ".sg.", "singapore"],
        "KR": ["kr.", "-kr-", ".kr.", "korea", "seoul"],
    }

    proxy_lower = proxy.lower()
    for country, indicators in _COUNTRY_INDICATORS.items():
        if any(ind in proxy_lower for ind in indicators):
            return country

    return "UNKNOWN"
