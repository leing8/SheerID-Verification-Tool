"""
proxy_checker.formatter — 终端彩色输出格式化
"""

from .models import ProxyCheckResult, RiskLevel


# ── ANSI 色彩 ──
_GREEN = "\x1b[32m"
_YELLOW = "\x1b[33m"
_RED = "\x1b[31m"
_DIM = "\x1b[2m"
_RESET = "\x1b[0m"
_BOLD = "\x1b[1m"


def format_result(result: ProxyCheckResult) -> str:
    """
    将 ProxyCheckResult 格式化为可读的彩色终端字符串。

    Args:
        result: 代理检测结果

    Returns:
        多行格式化字符串 (含 ANSI 色彩)
    """
    if result.error:
        return f"  {_RED}❌ 代理检测失败: {result.error}{_RESET}"

    geo = result.geo
    rep = result.reputation
    lines = []

    # IP / 地理信息
    ip_str = f"{geo.ip} | {geo.country}/{geo.city}"
    if geo.org:
        ip_str += f" | {geo.org}"

    if result.is_country_match:
        lines.append(f"  {_GREEN}✅ 代理 IP: {ip_str}{_RESET}")
    else:
        lines.append(f"  {_RED}⚠️  代理 IP: {ip_str}{_RESET}")
        lines.append(
            f"  {_RED}⚠️  警告: IP 不在 {result.expected_country}! "
            f"目标服务可能拒绝请求{_RESET}"
        )

    # 数据中心检测
    if rep.is_datacenter:
        provider_info = f" ({rep.provider})" if rep.provider else ""
        lines.append(
            f"  {_YELLOW}⚠️  检测到数据中心 IP{provider_info}, "
            f"建议使用住宅代理{_RESET}"
        )

    # 代理类型 & 风险
    type_label = rep.proxy_type.value
    risk_color = {
        RiskLevel.LOW: _GREEN,
        RiskLevel.MEDIUM: _YELLOW,
        RiskLevel.HIGH: _RED,
    }.get(rep.risk_level, _DIM)
    lines.append(
        f"  {_DIM}   类型: {type_label} | "
        f"风险: {risk_color}{rep.risk_level.value}{_RESET}{_DIM} | "
        f"延迟: {result.latency_ms:.0f}ms{_RESET}"
    )

    return "\n".join(lines)


def print_result(result: ProxyCheckResult) -> None:
    """格式化并打印代理检测结果到终端"""
    output = format_result(result)
    if output:
        print(f"\n{output}")
