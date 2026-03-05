"""代理纯净度评估测试

覆盖:
- 数据中心检测 (AWS/Azure/GCP 等)
- 住宅代理检测
- Mobile 代理检测
- ISP 检测
- 风险等级
- 提供商识别
"""

import pytest
from proxy_checker.models import ProxyType, RiskLevel
from proxy_checker.reputation import evaluate_reputation


class TestDatacenterDetection:
    """数据中心 IP 检测"""

    @pytest.mark.parametrize("org,provider", [
        ("Amazon.com, Inc. (AWS)", "AWS"),
        ("Amazon EC2 us-east-1", "AWS"),
        ("Google LLC (GCE)", "Google Cloud"),
        ("Microsoft Azure Cloud", "Microsoft Azure"),
        ("DigitalOcean, LLC", "DigitalOcean"),
        ("OVH SAS", "OVH"),
        ("Hetzner Online GmbH", "Hetzner"),
        ("Vultr Holdings", "Vultr"),
        ("Akamai Connected Cloud (Linode)", "Linode/Akamai"),
        ("Cloudflare, Inc.", "Cloudflare"),
        ("Alibaba Cloud Computing", "Alibaba Cloud"),
        ("Tencent Cloud Computing", "Tencent Cloud"),
    ])
    def test_datacenter_orgs(self, org: str, provider: str) -> None:
        """已知数据中心 ISP"""
        result = evaluate_reputation(org=org)
        assert result.is_datacenter is True
        assert result.proxy_type == ProxyType.DATACENTER
        assert result.risk_level == RiskLevel.HIGH
        assert result.provider == provider


class TestResidentialDetection:
    """住宅代理检测"""

    @pytest.mark.parametrize("hostname", [
        "residential.proxy.example",
        "resi-us-east.proxy.example",
        "brightdata.proxy.example",
        "oxylabs.proxy.example",
        "smartproxy.proxy.example",
        "iproyal.proxy.example",
    ])
    def test_residential_hostnames(self, hostname: str) -> None:
        """住宅代理主机名"""
        result = evaluate_reputation(org="Unknown ISP", hostname=hostname)
        assert result.proxy_type == ProxyType.RESIDENTIAL
        assert result.is_datacenter is False
        assert result.risk_level == RiskLevel.LOW


class TestMobileDetection:
    """Mobile 代理检测"""

    @pytest.mark.parametrize("org", [
        "T-Mobile USA",
        "Verizon Wireless",
        "Vodafone Group",
    ])
    def test_mobile_orgs(self, org: str) -> None:
        """Mobile 运营商"""
        result = evaluate_reputation(org=org)
        assert result.proxy_type == ProxyType.MOBILE
        assert result.risk_level == RiskLevel.LOW


class TestISPDetection:
    """ISP 检测"""

    @pytest.mark.parametrize("org", [
        "Comcast Cable Communications",
        "Spectrum Networks",
        "Cox Communications",
    ])
    def test_isp_orgs(self, org: str) -> None:
        """已知 ISP"""
        result = evaluate_reputation(org=org)
        assert result.proxy_type == ProxyType.ISP
        assert result.is_datacenter is False
        assert result.risk_level == RiskLevel.LOW


class TestUnknownType:
    """未知类型"""

    def test_unknown_org(self) -> None:
        """未知 org → UNKNOWN type"""
        result = evaluate_reputation(org="Some Random Corp")
        assert result.proxy_type == ProxyType.UNKNOWN
        assert result.risk_level == RiskLevel.MEDIUM

    def test_empty_org(self) -> None:
        """空 org"""
        result = evaluate_reputation(org="")
        assert result.proxy_type == ProxyType.UNKNOWN


class TestRiskAssessment:
    """风险等级"""

    def test_datacenter_high_risk(self) -> None:
        result = evaluate_reputation(org="Amazon AWS")
        assert result.risk_level == RiskLevel.HIGH

    def test_residential_low_risk(self) -> None:
        result = evaluate_reputation(org="", hostname="residential.proxy")
        assert result.risk_level == RiskLevel.LOW

    def test_unknown_medium_risk(self) -> None:
        result = evaluate_reputation(org="Unknown")
        assert result.risk_level == RiskLevel.MEDIUM
