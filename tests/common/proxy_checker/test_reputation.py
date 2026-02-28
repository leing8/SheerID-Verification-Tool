"""
test_reputation.py — 代理纯净度评估测试

测试 evaluate_reputation 对各类 org / hostname 的判断逻辑。
纯函数测试，无网络依赖。
"""

import pytest

from proxy_checker.models import ProxyType, RiskLevel
from proxy_checker.reputation import evaluate_reputation


class TestDatacenterDetection:
    """数据中心 IP 识别"""

    @pytest.mark.parametrize("org", [
        "Amazon Technologies Inc.",
        "AWS EC2 us-east-1",
        "Google Cloud Platform",
        "Microsoft Azure",
        "DigitalOcean LLC",
        "OVH SAS",
        "Hetzner Online GmbH",
        "Vultr Holdings",
        "Linode / Akamai Technologies",
        "Cloudflare Inc",
        "Oracle Cloud Infrastructure",
        "Alibaba Cloud Computing",
        "Tencent Cloud Computing",
        "Contabo GmbH",
    ])
    def test_datacenter_org_detected(self, org):
        """数据中心 org → DATACENTER + HIGH risk + is_datacenter=True"""
        result = evaluate_reputation(org=org)
        assert result.proxy_type == ProxyType.DATACENTER
        assert result.is_datacenter is True
        assert result.risk_level == RiskLevel.HIGH

    @pytest.mark.parametrize("org, expected_provider", [
        ("Amazon Technologies Inc.", "AWS"),
        ("Google Cloud Platform", "Google Cloud"),
        ("Microsoft Azure Cloud", "Microsoft Azure"),
        ("DigitalOcean LLC", "DigitalOcean"),
        ("OVH SAS", "OVH"),
        ("Hetzner Online GmbH", "Hetzner"),
        ("Vultr Holdings", "Vultr"),
        ("Cloudflare Inc", "Cloudflare"),
    ])
    def test_provider_extracted(self, org, expected_provider):
        """数据中心 org → 正确提取提供商名称"""
        result = evaluate_reputation(org=org)
        assert result.provider == expected_provider


class TestResidentialDetection:
    """住宅代理识别"""

    @pytest.mark.parametrize("org, hostname", [
        ("BrightData residential", ""),
        ("", "residential.proxy.example.com"),
        ("Oxylabs Networks", ""),
        ("SmartProxy Ltd", ""),
        ("NetNut LTD", ""),
        ("", "resi.proxy.net:8080"),
    ])
    def test_residential_detected(self, org, hostname):
        """住宅代理关键词 → RESIDENTIAL + LOW risk"""
        result = evaluate_reputation(org=org, hostname=hostname)
        assert result.proxy_type == ProxyType.RESIDENTIAL
        assert result.is_datacenter is False
        assert result.risk_level == RiskLevel.LOW


class TestMobileDetection:
    """移动网络代理识别"""

    @pytest.mark.parametrize("org", [
        "T-Mobile USA",
        "Verizon Wireless",
        "Vodafone Group",
        "China Mobile",
        "China Unicom",
    ])
    def test_mobile_detected(self, org):
        """移动网络 org → MOBILE + LOW risk"""
        result = evaluate_reputation(org=org)
        assert result.proxy_type == ProxyType.MOBILE
        assert result.is_datacenter is False
        assert result.risk_level == RiskLevel.LOW


class TestISPDetection:
    """ISP 识别"""

    @pytest.mark.parametrize("org", [
        "Comcast Cable Communications",
        "Spectrum Networks",
        "Cox Communications",
        "CenturyLink",
    ])
    def test_isp_detected(self, org):
        """ISP org → ISP + LOW risk"""
        result = evaluate_reputation(org=org)
        assert result.proxy_type == ProxyType.ISP
        assert result.is_datacenter is False
        assert result.risk_level == RiskLevel.LOW


class TestUnknownType:
    """未知代理类型"""

    @pytest.mark.parametrize("org", [
        "",
        "Some Random Company",
        "Acme Corp",
        "Unknown ISP Ltd",
    ])
    def test_unknown_org(self, org):
        """未识别的 org → UNKNOWN + MEDIUM risk"""
        result = evaluate_reputation(org=org)
        assert result.proxy_type == ProxyType.UNKNOWN
        assert result.is_datacenter is False
        assert result.risk_level == RiskLevel.MEDIUM

    def test_empty_org_and_hostname(self):
        """org 和 hostname 均为空 → UNKNOWN"""
        result = evaluate_reputation(org="", hostname="")
        assert result.proxy_type == ProxyType.UNKNOWN


class TestHostnameAsSupplementary:
    """hostname 作为辅助判断"""

    def test_hostname_overrides_empty_org(self):
        """org 为空但 hostname 含关键词 → 仍能识别"""
        result = evaluate_reputation(org="", hostname="brightdata-residential.proxy.com")
        assert result.proxy_type == ProxyType.RESIDENTIAL

    def test_case_insensitive(self):
        """org 和 hostname 匹配不区分大小写"""
        result = evaluate_reputation(org="AMAZON AWS EC2")
        assert result.proxy_type == ProxyType.DATACENTER
        assert result.is_datacenter is True
