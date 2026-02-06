"""
代理工具模块
代理验证、格式化和匹配
"""

import random


def validate_proxy(proxy: str) -> str:
    """验证并格式化代理字符串"""
    if not proxy:
        return None

    proxy = proxy.strip()

    # 已有协议前缀
    if "://" in proxy:
        return proxy

    parts = proxy.split(":")

    # host:port 格式
    if len(parts) == 2:
        return f"http://{parts[0]}:{parts[1]}"

    # host:port:user:pass 格式
    elif len(parts) == 4:
        return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"

    # user:pass@host:port 格式（已正确，只需添加协议前缀）
    elif "@" in proxy:
        return f"http://{proxy}"

    print(f"[警告] 无效的代理格式: {proxy}")
    return None


def check_proxy_type(proxy: str) -> str:
    """
    检查代理是数据中心还是住宅类型
    返回: 'residential'、'datacenter'、'unknown'
    """
    # 这是启发式方法 - 实际检查需要 IP 数据库查询
    datacenter_indicators = [
        "vultr",
        "digitalocean",
        "linode",
        "aws",
        "azure",
        "gcp",
        "ovh",
        "hetzner",
        "contabo",
        "hostinger",
    ]

    residential_indicators = [
        "residential",
        "mobile",
        "isp",
        "roxy",
        "bright",
        "oxylabs",
        "smartproxy",
        "geosurf",
    ]

    proxy_lower = proxy.lower()

    for ind in residential_indicators:
        if ind in proxy_lower:
            return "residential"

    for ind in datacenter_indicators:
        if ind in proxy_lower:
            return "datacenter"

    return "unknown"


def get_proxy_country(proxy: str) -> str:
    """
    尝试从主机名确定代理所在国家
    返回国家代码（US、NL、UK 等）或 'unknown'
    """
    country_indicators = {
        "us": ["us.", "-us-", ".us.", "america", "united-states"],
        "nl": ["nl.", "-nl-", ".nl.", "netherlands", "dutch", "amsterdam"],
        "uk": ["uk.", "-uk-", ".uk.", "london", "britain", "england"],
        "de": ["de.", "-de-", ".de.", "germany", "frankfurt", "berlin"],
        "fr": ["fr.", "-fr-", ".fr.", "france", "paris"],
        "ca": ["ca.", "-ca-", ".ca.", "canada", "toronto"],
        "au": ["au.", "-au-", ".au.", "australia", "sydney"],
    }

    proxy_lower = proxy.lower()

    for country, indicators in country_indicators.items():
        for ind in indicators:
            if ind in proxy_lower:
                return country.upper()

    return "unknown"


def get_matched_proxy(target_country: str, proxies: list) -> str:
    """
    获取与目标国家匹配的代理（用于大学位置匹配）

    参数:
        target_country: 国家代码（US、NL、UK 等）
        proxies: 代理 URL 列表

    返回:
        匹配的代理 URL，如无匹配则返回随机代理
    """
    if not proxies:
        return None

    target = target_country.upper()
    matched = []

    for proxy in proxies:
        proxy_country = get_proxy_country(proxy)
        if proxy_country == target:
            matched.append(proxy)

    if matched:
        return random.choice(matched)

    # 无匹配 - 如果有住宅代理则返回随机住宅代理
    residential = [p for p in proxies if check_proxy_type(p) == "residential"]
    if residential:
        return random.choice(residential)

    return random.choice(proxies)
