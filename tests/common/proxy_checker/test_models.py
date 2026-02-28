"""
test_models.py — proxy_checker 数据模型测试

测试枚举类型、dataclass 默认值、frozen 不可变性、passed 属性逻辑。
"""

import pytest

from proxy_checker.models import (
    GeoResult,
    ProxyCheckResult,
    ProxyInfo,
    ProxyType,
    ReputationResult,
    RiskLevel,
)


class TestProxyType:
    """ProxyType 枚举完整性"""

    def test_all_values(self):
        """应包含 5 种代理类型"""
        expected = {"residential", "datacenter", "mobile", "isp", "unknown"}
        actual = {t.value for t in ProxyType}
        assert actual == expected

    def test_str_enum(self):
        """ProxyType 继承 str，可直接比较字符串"""
        assert ProxyType.RESIDENTIAL == "residential"
        assert ProxyType.DATACENTER == "datacenter"


class TestRiskLevel:
    """RiskLevel 枚举完整性"""

    def test_all_values(self):
        """应包含 3 种风险等级"""
        expected = {"low", "medium", "high"}
        actual = {r.value for r in RiskLevel}
        assert actual == expected

    def test_str_enum(self):
        """RiskLevel 继承 str，可直接比较字符串"""
        assert RiskLevel.LOW == "low"
        assert RiskLevel.HIGH == "high"


class TestProxyInfo:
    """ProxyInfo (frozen dataclass) 测试"""

    def test_create_basic(self):
        """基本创建"""
        info = ProxyInfo(url="http://proxy.example.com:8080")
        assert info.url == "http://proxy.example.com:8080"
        assert info.protocol == "http"
        assert info.host == ""
        assert info.port == 0

    def test_create_with_auth(self):
        """带认证信息创建"""
        info = ProxyInfo(
            url="http://user:pass@proxy.example.com:8080",
            protocol="http",
            host="proxy.example.com",
            port=8080,
            username="user",
            password="pass",
        )
        assert info.username == "user"
        assert info.password == "pass"
        assert info.port == 8080

    def test_frozen_immutable(self):
        """frozen=True 不可修改"""
        info = ProxyInfo(url="http://example.com:8080")
        with pytest.raises(AttributeError):
            info.url = "changed"

    def test_default_no_auth(self):
        """默认无认证"""
        info = ProxyInfo(url="http://example.com:8080")
        assert info.username is None
        assert info.password is None


class TestGeoResult:
    """GeoResult 默认值和赋值"""

    def test_defaults(self):
        """默认值应全部为 'unknown' 或空"""
        geo = GeoResult()
        assert geo.ip == "unknown"
        assert geo.country == "unknown"
        assert geo.city == "unknown"
        assert geo.region == ""
        assert geo.org == ""
        assert geo.timezone == ""

    def test_custom_values(self):
        """自定义赋值"""
        geo = GeoResult(ip="1.2.3.4", country="US", city="LA", org="ISP Inc")
        assert geo.ip == "1.2.3.4"
        assert geo.country == "US"
        assert geo.org == "ISP Inc"

    def test_mutable(self):
        """GeoResult 非 frozen，字段可修改"""
        geo = GeoResult()
        geo.country = "CN"
        assert geo.country == "CN"


class TestReputationResult:
    """ReputationResult 默认值"""

    def test_defaults(self):
        """默认应为 UNKNOWN 类型、MEDIUM 风险"""
        rep = ReputationResult()
        assert rep.proxy_type == ProxyType.UNKNOWN
        assert rep.is_datacenter is False
        assert rep.risk_level == RiskLevel.MEDIUM
        assert rep.provider == ""


class TestProxyCheckResult:
    """ProxyCheckResult 综合测试"""

    def test_defaults(self):
        """默认值：未匹配、无错误"""
        result = ProxyCheckResult()
        assert result.is_country_match is False
        assert result.expected_country == ""
        assert result.latency_ms == 0.0
        assert result.error is None

    def test_passed_true(self):
        """国家匹配 + 非数据中心 → passed = True"""
        result = ProxyCheckResult(
            reputation=ReputationResult(is_datacenter=False),
            is_country_match=True,
        )
        assert result.passed is True

    def test_passed_false_country_mismatch(self):
        """国家不匹配 → passed = False"""
        result = ProxyCheckResult(
            reputation=ReputationResult(is_datacenter=False),
            is_country_match=False,
        )
        assert result.passed is False

    def test_passed_false_datacenter(self):
        """数据中心 IP → passed = False 即使国家匹配"""
        result = ProxyCheckResult(
            reputation=ReputationResult(is_datacenter=True),
            is_country_match=True,
        )
        assert result.passed is False

    def test_passed_false_both(self):
        """国家不匹配 + 数据中心 → passed = False"""
        result = ProxyCheckResult(
            reputation=ReputationResult(is_datacenter=True),
            is_country_match=False,
        )
        assert result.passed is False

    def test_error_result(self):
        """错误结果"""
        result = ProxyCheckResult(error="Timeout")
        assert result.error == "Timeout"
        assert result.passed is False
