"""
test_checker.py — ProxyChecker 核心检测器测试

使用 mock 代替网络层，测试同步/异步检测和代理选择逻辑。
"""

import threading
from unittest.mock import MagicMock, patch

import pytest
from proxy_checker.checker import ProxyChecker
from proxy_checker.models import GeoResult, ProxyType, ReputationResult, RiskLevel


@pytest.fixture
def mock_geo():
    """模拟的 GeoResult"""
    return GeoResult(
        ip="203.0.113.42",
        country="US",
        city="Los Angeles",
        region="California",
        org="Spectrum Cable",
        timezone="America/Los_Angeles",
    )


@pytest.fixture
def mock_reputation():
    """模拟的 ReputationResult"""
    return ReputationResult(
        proxy_type=ProxyType.RESIDENTIAL,
        is_datacenter=False,
        risk_level=RiskLevel.LOW,
        provider="",
    )


class TestProxyCheckerSync:
    """同步检测 (check 方法)"""

    @patch("proxy_checker.checker.evaluate_reputation")
    @patch("proxy_checker.checker.detect_geo")
    def test_check_success(self, mock_detect, mock_eval, mock_geo, mock_reputation):
        """正常检测流程 → 返回完整 ProxyCheckResult"""
        mock_detect.return_value = mock_geo
        mock_eval.return_value = mock_reputation

        checker = ProxyChecker()
        session = MagicMock()
        result = checker.check(session, expected_country="US")

        assert result.geo.ip == "203.0.113.42"
        assert result.geo.country == "US"
        assert result.is_country_match is True
        assert result.reputation.proxy_type == ProxyType.RESIDENTIAL
        assert result.passed is True
        assert result.latency_ms >= 0
        assert result.error is None

    @patch("proxy_checker.checker.evaluate_reputation")
    @patch("proxy_checker.checker.detect_geo")
    def test_check_country_mismatch(self, mock_detect, mock_eval, mock_reputation):
        """IP 国家与预期不匹配"""
        mock_detect.return_value = GeoResult(
            ip="1.2.3.4", country="DE", city="Frankfurt", org="Some ISP"
        )
        mock_eval.return_value = mock_reputation

        checker = ProxyChecker()
        result = checker.check(MagicMock(), expected_country="US")

        assert result.is_country_match is False
        assert result.expected_country == "US"
        assert result.passed is False

    @patch("proxy_checker.checker.detect_geo")
    def test_check_exception_returns_error(self, mock_detect):
        """检测过程异常 → 返回带 error 的结果"""
        mock_detect.side_effect = Exception("Network timeout")

        checker = ProxyChecker()
        result = checker.check(MagicMock(), expected_country="US")

        assert result.error == "Network timeout"
        assert result.expected_country == "US"
        assert result.passed is False

    @patch("proxy_checker.checker.evaluate_reputation")
    @patch("proxy_checker.checker.detect_geo")
    def test_check_case_insensitive_country(self, mock_detect, mock_eval, mock_geo, mock_reputation):
        """expected_country 大小写不敏感"""
        mock_detect.return_value = mock_geo
        mock_eval.return_value = mock_reputation

        checker = ProxyChecker()
        result = checker.check(MagicMock(), expected_country="us")

        assert result.is_country_match is True
        assert result.expected_country == "US"


class TestProxyCheckerAsync:
    """异步检测 (check_async 方法)"""

    @patch("proxy_checker.checker.evaluate_reputation")
    @patch("proxy_checker.checker.detect_geo")
    def test_async_returns_daemon_thread(self, mock_detect, mock_eval, mock_geo, mock_reputation):
        """check_async 返回已启动的守护线程"""
        mock_detect.return_value = mock_geo
        mock_eval.return_value = mock_reputation

        checker = ProxyChecker()
        thread = checker.check_async(MagicMock(), expected_country="US")

        assert isinstance(thread, threading.Thread)
        assert thread.daemon is True
        thread.join(timeout=5)

    @patch("proxy_checker.checker.evaluate_reputation")
    @patch("proxy_checker.checker.detect_geo")
    def test_async_calls_callback(self, mock_detect, mock_eval, mock_geo, mock_reputation):
        """check_async 完成后应调用 callback"""
        mock_detect.return_value = mock_geo
        mock_eval.return_value = mock_reputation

        callback = MagicMock()
        checker = ProxyChecker()
        thread = checker.check_async(
            MagicMock(),
            expected_country="US",
            callback=callback,
        )
        thread.join(timeout=5)

        callback.assert_called_once()
        result = callback.call_args[0][0]
        assert result.geo.country == "US"
        assert result.passed is True


class TestGetMatchedProxy:
    """代理选择逻辑"""

    def test_empty_list_returns_none(self):
        """空代理列表 → None"""
        assert ProxyChecker.get_matched_proxy("US", []) is None

    def test_country_match_preferred(self):
        """优先选择国家匹配的代理"""
        proxies = [
            "http://de.proxy.net:8080",
            "http://us.proxy.net:8080",
            "http://uk.proxy.net:8080",
        ]
        result = ProxyChecker.get_matched_proxy("US", proxies)
        assert result == "http://us.proxy.net:8080"

    def test_residential_preferred_over_random(self):
        """无国家匹配时，优先选择住宅代理"""
        proxies = [
            "http://unknown.proxy.net:8080",
            "http://residential.proxy.net:8080",
        ]
        result = ProxyChecker.get_matched_proxy("JP", proxies)
        # 应选择 residential (住宅关键词匹配)
        assert result == "http://residential.proxy.net:8080"

    def test_random_fallback(self):
        """无国家匹配也无住宅标识 → 随机返回"""
        proxies = [
            "http://proxy1.example.net:8080",
            "http://proxy2.example.net:8080",
        ]
        result = ProxyChecker.get_matched_proxy("JP", proxies)
        assert result in proxies

    def test_multiple_country_matches_random_selection(self):
        """多个国家匹配 → 从中随机选择"""
        proxies = [
            "http://us.proxy1.net:8080",
            "http://us.proxy2.net:8080",
            "http://de.proxy.net:8080",
        ]
        result = ProxyChecker.get_matched_proxy("US", proxies)
        assert "us." in result
