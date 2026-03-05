"""模拟 verifier.py 调用链的集成测试

验证 proxy_checker 生成的检测结果可以正确用于 verifier.py 中的代理验证流程。

verifier.py 中的调用:
    from proxy_checker import ProxyChecker
    ProxyChecker().check_async(self.client, expected_country="US")

覆盖:
- 完整调用链模拟
- ProxyCheckResult 结构完整性
- passed 属性逻辑
- 多场景 (匹配/不匹配/数据中心)
"""

import pytest
from proxy_checker import ProxyChecker
from proxy_checker.models import ProxyCheckResult, ProxyType, RiskLevel


class TestVerifierProxyFlow:
    """模拟 verifier.py 的完整代理检测链"""

    def test_full_flow_residential_us(self, checker, mock_session) -> None:
        """
        模拟 verifier.py 中的调用:
            ProxyChecker().check_async(self.client, expected_country="US")
        使用同步版本便于断言
        """
        result = checker.check(mock_session, expected_country="US")

        assert isinstance(result, ProxyCheckResult)
        assert result.error is None
        assert result.geo.ip == "203.0.113.42"
        assert result.geo.country == "US"
        assert result.is_country_match is True
        assert result.reputation.is_datacenter is False
        assert result.passed is True
        assert result.latency_ms >= 0

    def test_datacenter_fails_passed(self, checker, mock_session_datacenter) -> None:
        """数据中心 IP 即使国家匹配也 passed=False"""
        result = checker.check(mock_session_datacenter, expected_country="US")

        assert result.is_country_match is True
        assert result.reputation.is_datacenter is True
        assert result.passed is False

    def test_wrong_country_fails_passed(self, checker, mock_session_non_us) -> None:
        """非目标国家 → passed=False"""
        result = checker.check(mock_session_non_us, expected_country="US")

        assert result.is_country_match is False
        assert result.passed is False


class TestProxyCheckResultFields:
    """ProxyCheckResult 字段验证"""

    def test_all_fields_populated(self, checker, mock_session) -> None:
        """所有字段非 None"""
        result = checker.check(mock_session, expected_country="US")

        assert result.geo is not None
        assert result.geo.ip != "unknown"
        assert result.geo.country
        assert result.geo.city
        assert result.reputation is not None
        assert result.reputation.proxy_type is not None
        assert result.reputation.risk_level is not None
        assert result.expected_country == "US"
        assert result.latency_ms >= 0

    def test_geo_fields(self, checker, mock_session) -> None:
        """GeoResult 字段完整"""
        result = checker.check(mock_session, expected_country="US")
        geo = result.geo

        assert geo.ip
        assert geo.country
        assert geo.city
        assert geo.org

    def test_reputation_fields(self, checker, mock_session) -> None:
        """ReputationResult 字段完整"""
        result = checker.check(mock_session, expected_country="US")
        rep = result.reputation

        assert isinstance(rep.proxy_type, ProxyType)
        assert isinstance(rep.risk_level, RiskLevel)
        assert isinstance(rep.is_datacenter, bool)


class TestAsyncVerifierFlow:
    """模拟 verifier.py 异步调用"""

    def test_async_with_callback(self, checker, mock_session) -> None:
        """异步检测回调可获取完整结果"""
        results = []

        def on_result(result):
            results.append(result)

        thread = checker.check_async(
            mock_session,
            expected_country="US",
            callback=on_result,
        )
        thread.join(timeout=5)

        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].geo.country == "US"

    def test_async_default_callback_no_crash(self, checker, mock_session) -> None:
        """默认回调 (print_result) 不崩溃"""
        thread = checker.check_async(mock_session, expected_country="US")
        thread.join(timeout=5)
        assert not thread.is_alive()
