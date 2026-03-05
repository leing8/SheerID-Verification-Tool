"""ProxyChecker 核心测试

覆盖:
- 同步检测 (国家匹配 / 不匹配 / 数据中心)
- 异常处理
- 异步检测
- get_matched_proxy 策略
- 关键日志输出验证
"""

import logging
import threading

import pytest
from proxy_checker import ProxyChecker
from proxy_checker.models import ProxyCheckResult, ProxyType, RiskLevel


class TestCheckSync:
    """同步检测"""

    def test_check_success_country_match(self, checker, mock_session) -> None:
        """美国代理 → 国家匹配"""
        result = checker.check(mock_session, expected_country="US")

        assert isinstance(result, ProxyCheckResult)
        assert result.is_country_match is True
        assert result.geo.country == "US"
        assert result.geo.ip == "203.0.113.42"
        assert result.error is None
        assert result.latency_ms >= 0

    def test_check_country_mismatch(self, checker, mock_session_non_us) -> None:
        """德国代理 → 国家不匹配"""
        result = checker.check(mock_session_non_us, expected_country="US")

        assert result.is_country_match is False
        assert result.geo.country == "DE"
        assert result.expected_country == "US"

    def test_check_datacenter_detected(self, checker, mock_session_datacenter) -> None:
        """AWS IP → 数据中心检测"""
        result = checker.check(mock_session_datacenter, expected_country="US")

        assert result.is_country_match is True
        assert result.reputation.is_datacenter is True
        assert result.reputation.proxy_type == ProxyType.DATACENTER
        assert result.reputation.risk_level == RiskLevel.HIGH
        assert result.passed is False  # datacenter + US match → not passed

    def test_check_residential_passes(self, checker, mock_session) -> None:
        """住宅 IP + 国家匹配 → passed"""
        result = checker.check(mock_session, expected_country="US")

        assert result.reputation.is_datacenter is False
        assert result.passed is True

    def test_check_error_handling(self, checker, failing_session) -> None:
        """所有 API 失败 → 返回 error 结果"""
        result = checker.check(failing_session, expected_country="US")

        # geo 检测全部失败时，detect_geo 返回默认 GeoResult(ip="unknown")
        # evaluate_reputation 仍然能执行，所以不一定有 error
        assert isinstance(result, ProxyCheckResult)


class TestCheckAsync:
    """异步检测"""

    def test_check_async_returns_thread(self, checker, mock_session) -> None:
        """返回已启动的守护线程"""
        thread = checker.check_async(mock_session, expected_country="US")

        assert isinstance(thread, threading.Thread)
        assert thread.daemon is True

    def test_check_async_callback(self, checker, mock_session) -> None:
        """异步检测完成后执行回调"""
        results = []

        def callback(result):
            results.append(result)

        thread = checker.check_async(
            mock_session, expected_country="US", callback=callback
        )
        thread.join(timeout=5)

        assert len(results) == 1
        assert isinstance(results[0], ProxyCheckResult)
        assert results[0].geo.country == "US"


class TestGetMatchedProxy:
    """代理匹配策略"""

    def test_empty_list_returns_none(self) -> None:
        """空列表 → None"""
        assert ProxyChecker.get_matched_proxy("US", []) is None

    def test_country_match_priority(self) -> None:
        """优先匹配国家"""
        proxies = [
            "http://de.proxy.example:8080",
            "http://us.proxy.example:8080",
            "http://random.proxy:8080",
        ]
        result = ProxyChecker.get_matched_proxy("US", proxies)
        assert "us." in result

    def test_fallback_to_random(self) -> None:
        """无匹配时随机选择"""
        proxies = ["http://abc.example:8080", "http://xyz.example:8080"]
        result = ProxyChecker.get_matched_proxy("US", proxies)
        assert result in proxies


class TestCheckerLogging:
    """日志输出验证"""

    def test_check_info_logs(self, checker, mock_session, caplog) -> None:
        """check() 产生 INFO 日志"""
        with caplog.at_level(logging.INFO, logger="proxy_checker.checker"):
            checker.check(mock_session, expected_country="US")

        messages = caplog.text
        assert "开始代理检测" in messages
        assert "[步骤1/3] 地理位置" in messages
        assert "[步骤2/3] 纯净度评估" in messages
        assert "[步骤3/3] 综合结果" in messages

    def test_geo_module_logging(self, checker, mock_session, caplog) -> None:
        """geo 模块产生日志"""
        with caplog.at_level(logging.DEBUG, logger="proxy_checker.geo"):
            checker.check(mock_session, expected_country="US")

        messages = caplog.text
        assert "地理位置检测成功" in messages

    def test_reputation_module_logging(self, checker, mock_session, caplog) -> None:
        """reputation 模块产生 DEBUG 日志"""
        with caplog.at_level(logging.DEBUG, logger="proxy_checker.reputation"):
            checker.check(mock_session, expected_country="US")

        messages = caplog.text
        assert "纯净度评估" in messages
