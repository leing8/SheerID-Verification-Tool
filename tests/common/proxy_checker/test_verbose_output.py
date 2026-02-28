"""
test_verbose_output.py — 代理检测模块完整信息输出测试

运行时使用 -s 参数查看完整输出:
    pytest tests/common/proxy_checker/test_verbose_output.py -v -s
"""

import pytest

from proxy_checker import (
    ProxyChecker,
    evaluate_reputation,
    format_result,
    infer_country_from_hostname,
    parse_proxy,
)
from proxy_checker.models import (
    GeoResult,
    ProxyCheckResult,
    ProxyType,
    ReputationResult,
    RiskLevel,
)


class TestProxyCheckerVerboseOutput:
    """输出完整代理检测模块信息，便于人工检查"""

    def test_models_overview(self):
        """输出所有数据模型的枚举值和默认实例"""
        print("\n" + "=" * 72)
        print("  proxy_checker 数据模型总览")
        print("=" * 72)

        # 枚举类型
        print(f"\n── ProxyType 枚举 ──")
        for pt in ProxyType:
            print(f"  {pt.name:<15} = {pt.value}")

        print(f"\n── RiskLevel 枚举 ──")
        for rl in RiskLevel:
            print(f"  {rl.name:<15} = {rl.value}")

        # 默认实例
        print(f"\n── GeoResult 默认值 ──")
        geo = GeoResult()
        print(f"  ip       : {geo.ip}")
        print(f"  country  : {geo.country}")
        print(f"  city     : {geo.city}")
        print(f"  region   : {geo.region!r}")
        print(f"  org      : {geo.org!r}")
        print(f"  timezone : {geo.timezone!r}")

        print(f"\n── ReputationResult 默认值 ──")
        rep = ReputationResult()
        print(f"  proxy_type    : {rep.proxy_type.value}")
        print(f"  is_datacenter : {rep.is_datacenter}")
        print(f"  risk_level    : {rep.risk_level.value}")
        print(f"  provider      : {rep.provider!r}")

        print("\n" + "=" * 72)

    def test_proxy_parsing_showcase(self):
        """输出各种代理格式的解析结果"""
        print("\n" + "=" * 72)
        print("  parse_proxy 解析结果对比")
        print("=" * 72)

        test_proxies = [
            "http://proxy.example.com:8080",
            "http://admin:secret@proxy.example.com:3128",
            "socks5://socks.proxy.com:1080",
            "192.168.1.100:8080",
            "192.168.1.100:8080:admin:secret",
            "admin:secret@proxy.example.com:8080",
            "",
            "invalid",
        ]

        print(f"\n  {'Proxy Input':<50} {'Proto':<8} {'Host':<25} {'Port':<6} {'User':<10} {'Pass'}")
        print(f"  {'-'*50} {'-'*8} {'-'*25} {'-'*6} {'-'*10} {'-'*10}")

        for proxy in test_proxies:
            info = parse_proxy(proxy) if proxy else parse_proxy("")
            if info:
                print(
                    f"  {proxy:<50} {info.protocol:<8} {info.host:<25} "
                    f"{info.port:<6} {str(info.username or '-'):<10} "
                    f"{str(info.password or '-')}"
                )
            else:
                print(f"  {proxy or '(empty)':<50} → None")

        print("\n" + "=" * 72)

    def test_reputation_evaluation_showcase(self):
        """输出各类 org 的纯净度评估结果"""
        print("\n" + "=" * 72)
        print("  evaluate_reputation 评估结果对比")
        print("=" * 72)

        test_cases = [
            ("Amazon Technologies Inc.", ""),
            ("Google Cloud Platform", ""),
            ("Microsoft Azure", ""),
            ("DigitalOcean LLC", ""),
            ("Hetzner Online GmbH", ""),
            ("Comcast Cable Communications", ""),
            ("Spectrum Networks", ""),
            ("T-Mobile USA", ""),
            ("Verizon Wireless", ""),
            ("", "brightdata-residential.proxy.com"),
            ("", "residential.proxy.net"),
            ("Some Random Company", ""),
            ("", ""),
        ]

        print(f"\n  {'Org / Hostname':<40} {'Type':<15} {'DC?':<5} {'Risk':<8} {'Provider'}")
        print(f"  {'-'*40} {'-'*15} {'-'*5} {'-'*8} {'-'*15}")

        for org, hostname in test_cases:
            result = evaluate_reputation(org=org, hostname=hostname)
            label = org if org else f"[host: {hostname}]"
            print(
                f"  {label:<40} {result.proxy_type.value:<15} "
                f"{'Yes' if result.is_datacenter else 'No':<5} "
                f"{result.risk_level.value:<8} {result.provider or '-'}"
            )

        print("\n" + "=" * 72)

    def test_hostname_country_inference_showcase(self):
        """输出主机名国家推断结果"""
        print("\n" + "=" * 72)
        print("  infer_country_from_hostname 推断结果")
        print("=" * 72)

        hostnames = [
            "us.proxy.example.com:8080",
            "proxy-us-west.example.com",
            "nl.proxy.io:3128",
            "amsterdam.proxy.net:8080",
            "proxy-uk-london.example.com",
            "frankfurt.proxy.net:1080",
            "tokyo.proxy.net:8080",
            "singapore.proxy.net",
            "seoul.proxy.net:3128",
            "proxy.example.com:8080",
            "192.168.1.1:3128",
        ]

        print(f"\n  {'Hostname':<45} {'Inferred Country'}")
        print(f"  {'-'*45} {'-'*16}")

        for hostname in hostnames:
            country = infer_country_from_hostname(hostname)
            print(f"  {hostname:<45} {country}")

        print("\n" + "=" * 72)

    def test_format_result_showcase(self):
        """输出各种场景下的格式化结果"""
        print("\n" + "=" * 72)
        print("  format_result 格式化输出展示")
        print("=" * 72)

        # 场景 1：正常通过（住宅 IP，国家匹配）
        print("\n── 场景 1: 住宅 IP + 国家匹配 (PASS) ──")
        result1 = ProxyCheckResult(
            geo=GeoResult(ip="203.0.113.42", country="US", city="Los Angeles", org="Spectrum Cable"),
            reputation=ReputationResult(
                proxy_type=ProxyType.RESIDENTIAL, is_datacenter=False,
                risk_level=RiskLevel.LOW,
            ),
            is_country_match=True,
            expected_country="US",
            latency_ms=156.3,
        )
        print(format_result(result1))

        # 场景 2：数据中心 IP（国家匹配但高风险）
        print("\n── 场景 2: 数据中心 IP + 国家匹配 (WARNING) ──")
        result2 = ProxyCheckResult(
            geo=GeoResult(ip="54.89.123.45", country="US", city="Ashburn", org="Amazon AWS EC2"),
            reputation=ReputationResult(
                proxy_type=ProxyType.DATACENTER, is_datacenter=True,
                risk_level=RiskLevel.HIGH, provider="AWS",
            ),
            is_country_match=True,
            expected_country="US",
            latency_ms=89.7,
        )
        print(format_result(result2))

        # 场景 3：国家不匹配
        print("\n── 场景 3: 国家不匹配 (FAIL) ──")
        result3 = ProxyCheckResult(
            geo=GeoResult(ip="185.220.101.1", country="DE", city="Frankfurt", org="Hetzner"),
            reputation=ReputationResult(
                proxy_type=ProxyType.DATACENTER, is_datacenter=True,
                risk_level=RiskLevel.HIGH, provider="Hetzner",
            ),
            is_country_match=False,
            expected_country="US",
            latency_ms=234.5,
        )
        print(format_result(result3))

        # 场景 4：检测失败
        print("\n── 场景 4: 检测失败 (ERROR) ──")
        result4 = ProxyCheckResult(
            expected_country="US",
            error="Connection refused: proxy 192.168.1.1:8080",
        )
        print(format_result(result4))

        print("\n" + "=" * 72)
