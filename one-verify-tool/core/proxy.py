"""
代理处理模块 - 代理验证和国家检测

包含:
- validate_proxy: 验证并格式化代理
- check_proxy_type: 检查代理类型
- get_proxy_country: 推断代理国家
"""


def validate_proxy(proxy: str) -> str:
    """验证并格式化代理字符串"""
    if not proxy:
        return None
    
    proxy = proxy.strip()
    
    if "://" in proxy:
        return proxy
    
    parts = proxy.split(":")
    
    if len(parts) == 2:
        return f"http://{parts[0]}:{parts[1]}"
    elif len(parts) == 4:
        return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
    elif "@" in proxy:
        return f"http://{proxy}"
    
    print(f"[警告] 代理格式无效: {proxy}")
    return None


def check_proxy_type(proxy: str) -> str:
    """
    检查代理类型
    
    Returns:
        'residential', 'datacenter', 或 'unknown'
    """
    if not proxy:
        return "unknown"
    
    proxy_lower = proxy.lower()
    
    datacenter_indicators = [
        "vultr", "digitalocean", "linode", "aws", "azure", "gcp", "ovh", "hetzner"
    ]
    residential_indicators = [
        "residential", "mobile", "isp", "roxy", "bright", "oxylabs", "smartproxy"
    ]
    
    for ind in residential_indicators:
        if ind in proxy_lower:
            return "residential"
    
    for ind in datacenter_indicators:
        if ind in proxy_lower:
            return "datacenter"
    
    return "unknown"


def get_proxy_country(proxy: str) -> str:
    """从代理地址推断国家代码"""
    if not proxy:
        return "US"
    
    proxy_lower = proxy.lower()
    
    country_indicators = {
        "US": ["us.", "-us-", ".us.", "america", "united-states", "nyc", "la.", "chicago"],
        "CA": ["ca.", "-ca-", ".ca.", "canada", "toronto", "vancouver"],
        "UK": ["uk.", "-uk-", ".uk.", "london", "britain", "england"],
        "DE": ["de.", "-de-", ".de.", "germany", "frankfurt", "berlin"],
        "AU": ["au.", "-au-", ".au.", "australia", "sydney", "melbourne"],
    }
    
    for country, indicators in country_indicators.items():
        for ind in indicators:
            if ind in proxy_lower:
                return country
    
    return "US"
