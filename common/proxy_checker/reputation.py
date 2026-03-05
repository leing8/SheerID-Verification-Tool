"""
proxy_checker.reputation — 代理属性与纯净度评估

基于 IP 归属组织 (org) 和代理主机名，判断代理类型、是否数据中心 IP、风险等级。
"""

import logging

from .models import ProxyType, ReputationResult, RiskLevel

logger = logging.getLogger(__name__)

# ── 数据中心关键词 ──
_DATACENTER_KEYWORDS = frozenset({
    "amazon", "aws", "ec2",
    "google", "gce", "google cloud",
    "microsoft", "azure",
    "digitalocean",
    "ovh",
    "hetzner",
    "vultr",
    "linode", "akamai",
    "cloudflare",
    "oracle cloud",
    "alibaba", "aliyun",
    "tencent",
    "contabo",
    "hostinger",
    "upcloud",
    "kamatera",
    "choopa",
})

# ── 住宅代理提供商关键词 ──
_RESIDENTIAL_KEYWORDS = frozenset({
    "residential", "resi",
    "bright", "brightdata",
    "oxylabs",
    "smartproxy",
    "geosurf",
    "netnut",
    "soax",
    "packetstream",
    "iproyal",
    "luminati",
    "proxyrack",
    "storm proxies",
})

# ── Mobile 提供商关键词 ──
_MOBILE_KEYWORDS = frozenset({
    "mobile", "4g", "5g", "lte",
    "t-mobile", "verizon wireless", "at&t wireless",
    "vodafone", "o2",
    "china mobile", "china unicom", "china telecom",
})

# ── ISP 提供商关键词 ──
_ISP_KEYWORDS = frozenset({
    "comcast", "spectrum", "cox",
    "at&t", "verizon", "centurylink",
    "bt ", "sky broadband", "virgin media",
    "deutsche telekom",
    "orange", "free ", "sfr",
    "kddi", "ntt",
})


def evaluate_reputation(org: str, hostname: str = "") -> ReputationResult:
    """
    评估代理的属性和纯净度。

    Args:
        org:      IP 归属组织 (来自 geo 检测结果)
        hostname: 代理主机名 (用于辅助推断类型)

    Returns:
        ReputationResult 包含 proxy_type, is_datacenter, risk_level, provider
    """
    org_lower = org.lower() if org else ""
    host_lower = hostname.lower() if hostname else ""
    combined = f"{org_lower} {host_lower}"

    proxy_type = _detect_type(combined)
    is_datacenter = proxy_type == ProxyType.DATACENTER
    provider = _detect_provider(org_lower)
    risk_level = _assess_risk(proxy_type, is_datacenter)

    logger.debug(
        "纯净度评估: org=%s, type=%s, datacenter=%s, risk=%s, provider=%s",
        org[:30] if org else "(空)", proxy_type.value, is_datacenter,
        risk_level.value, provider or "(无)",
    )

    return ReputationResult(
        proxy_type=proxy_type,
        is_datacenter=is_datacenter,
        risk_level=risk_level,
        provider=provider,
    )


# ────────────────────────────────────────────
# 内部检测函数
# ────────────────────────────────────────────

def _detect_type(combined: str) -> ProxyType:
    """从 org + hostname 综合判断代理类型"""
    # 优先检查住宅/mobile (代理主机名中的标识更可靠)
    if any(kw in combined for kw in _MOBILE_KEYWORDS):
        return ProxyType.MOBILE
    if any(kw in combined for kw in _RESIDENTIAL_KEYWORDS):
        return ProxyType.RESIDENTIAL
    if any(kw in combined for kw in _ISP_KEYWORDS):
        return ProxyType.ISP
    if any(kw in combined for kw in _DATACENTER_KEYWORDS):
        return ProxyType.DATACENTER
    return ProxyType.UNKNOWN


def _detect_provider(org_lower: str) -> str:
    """尝试提取 IP 归属的提供商名称"""
    _PROVIDER_MAP = {
        "amazon": "AWS", "aws": "AWS", "ec2": "AWS",
        "google": "Google Cloud", "gce": "Google Cloud",
        "microsoft": "Microsoft Azure", "azure": "Microsoft Azure",
        "digitalocean": "DigitalOcean",
        "ovh": "OVH",
        "hetzner": "Hetzner",
        "vultr": "Vultr",
        "linode": "Linode/Akamai", "akamai": "Linode/Akamai",
        "cloudflare": "Cloudflare",
        "alibaba": "Alibaba Cloud", "aliyun": "Alibaba Cloud",
        "tencent": "Tencent Cloud",
        "oracle": "Oracle Cloud",
        "contabo": "Contabo",
    }
    for keyword, provider in _PROVIDER_MAP.items():
        if keyword in org_lower:
            return provider
    return ""


def _assess_risk(proxy_type: ProxyType, is_datacenter: bool) -> RiskLevel:
    """
    风险等级评估:
      - 数据中心 IP → HIGH (最容易被检测和封禁)
      - 未知类型    → MEDIUM
      - 住宅/ISP    → LOW
    """
    if is_datacenter:
        return RiskLevel.HIGH
    if proxy_type in (ProxyType.RESIDENTIAL, ProxyType.ISP, ProxyType.MOBILE):
        return RiskLevel.LOW
    return RiskLevel.MEDIUM
