"""
proxy_checker 模块单元测试
"""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from proxy_checker import (
    ProxyChecker,
    parse_proxy,
    detect_geo,
    evaluate_reputation,
    infer_country_from_hostname,
    format_result,
    print_result,
)
from proxy_checker.models import (
    GeoResult,
    ProxyCheckResult,
    ProxyType,
    ReputationResult,
    RiskLevel,
)


# ════════════════════════════════════════════
# validator — parse_proxy 测试
# ════════════════════════════════════════════

class TestParseProxy:
    """代理字符串解析测试"""

    def test_none_input(self):
        assert parse_proxy(None) is None

    def test_empty_string(self):
        assert parse_proxy("") is None
        assert parse_proxy("  ") is None

    def test_host_port(self):
        info = parse_proxy("1.2.3.4:8080")
        assert info is not None
        assert info.url == "http://1.2.3.4:8080"
        assert info.host == "1.2.3.4"
        assert info.port == 8080
        assert info.protocol == "http"

    def test_host_port_user_pass(self):
        info = parse_proxy("1.2.3.4:8080:myuser:mypass")
        assert info is not None
        assert info.url == "http://myuser:mypass@1.2.3.4:8080"
        assert info.host == "1.2.3.4"
        assert info.port == 8080
        assert info.username == "myuser"
        assert info.password == "mypass"

    def test_user_pass_at_host_port(self):
        info = parse_proxy("user:pass@proxy.example.com:3128")
        assert info is not None
        assert info.host == "proxy.example.com"
        assert info.port == 3128
        assert info.username == "user"
        assert info.password == "pass"

    def test_http_url(self):
        info = parse_proxy("http://proxy.example.com:8080")
        assert info is not None
        assert info.protocol == "http"
        assert info.host == "proxy.example.com"
        assert info.port == 8080

    def test_socks5_url(self):
        info = parse_proxy("socks5://user:pass@proxy.example.com:1080")
        assert info is not None
        assert info.protocol == "socks5"
        assert info.username == "user"
        assert info.password == "pass"

    def test_invalid_format(self):
        assert parse_proxy("just-a-string") is None

    def test_invalid_port(self):
        assert parse_proxy("host:abc") is None

    def test_frozen_dataclass(self):
        info = parse_proxy("1.2.3.4:8080")
        with pytest.raises(AttributeError):
            info.host = "5.6.7.8"


# ════════════════════════════════════════════
# geo — 地理位置检测测试
# ════════════════════════════════════════════

class TestGeo:
    """地理位置检测测试"""

    def test_detect_geo_ipapi(self):
        """模拟 ipapi.co 返回正常数据"""
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "ip": "8.8.8.8",
            "country_code": "US",
            "city": "Mountain View",
            "region": "California",
            "org": "Google LLC",
            "timezone": "America/Los_Angeles",
        }
        mock_session.get.return_value = mock_resp

        result = detect_geo(mock_session)
        assert result.ip == "8.8.8.8"
        assert result.country == "US"
        assert result.city == "Mountain View"
        assert result.org == "Google LLC"

    def test_detect_geo_fallback(self):
        """第一个 API 失败，自动转到第二个"""
        mock_session = MagicMock()
        call_count = [0]

        def side_effect(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise ConnectionError("first API down")
            resp = MagicMock()
            resp.json.return_value = {
                "ip": "1.2.3.4",
                "country": "NL",
                "city": "Amsterdam",
                "region": "NH",
                "org": "ISP Co",
            }
            return resp

        mock_session.get.side_effect = side_effect
        result = detect_geo(mock_session)
        assert result.ip == "1.2.3.4"
        assert result.country == "NL"
        assert call_count[0] >= 2

    def test_detect_geo_all_fail(self):
        """所有 API 都失败，返回默认值"""
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("all down")
        result = detect_geo(mock_session)
        assert result.ip == "unknown"
        assert result.country == "unknown"

    def test_infer_country_us(self):
        assert infer_country_from_hostname("us.proxy.com") == "US"
        assert infer_country_from_hostname("proxy-us-east.example.com") == "US"

    def test_infer_country_nl(self):
        assert infer_country_from_hostname("amsterdam.proxy.com") == "NL"

    def test_infer_country_unknown(self):
        assert infer_country_from_hostname("proxy.example.com") == "UNKNOWN"


# ════════════════════════════════════════════
# reputation — 纯净度评估测试
# ════════════════════════════════════════════

class TestReputation:
    """代理纯净度评估测试"""

    def test_datacenter_aws(self):
        result = evaluate_reputation("Amazon.com, Inc.")
        assert result.is_datacenter is True
        assert result.proxy_type == ProxyType.DATACENTER
        assert result.risk_level == RiskLevel.HIGH
        assert result.provider == "AWS"

    def test_datacenter_google(self):
        result = evaluate_reputation("Google Cloud")
        assert result.is_datacenter is True
        assert result.provider == "Google Cloud"

    def test_residential_hostname(self):
        result = evaluate_reputation("", hostname="residential.brightdata.com")
        assert result.proxy_type == ProxyType.RESIDENTIAL
        assert result.is_datacenter is False
        assert result.risk_level == RiskLevel.LOW

    def test_mobile(self):
        result = evaluate_reputation("T-Mobile USA")
        assert result.proxy_type == ProxyType.MOBILE
        assert result.risk_level == RiskLevel.LOW

    def test_isp(self):
        result = evaluate_reputation("Comcast Cable Communications")
        assert result.proxy_type == ProxyType.ISP
        assert result.is_datacenter is False
        assert result.risk_level == RiskLevel.LOW

    def test_unknown(self):
        result = evaluate_reputation("Some Random Local Corp")
        assert result.proxy_type == ProxyType.UNKNOWN
        assert result.risk_level == RiskLevel.MEDIUM


# ════════════════════════════════════════════
# checker — ProxyChecker 测试
# ════════════════════════════════════════════

class TestProxyChecker:
    """ProxyChecker 主检测器测试"""

    def _mock_session(self, country_code="US", org="Comcast"):
        """构造一个模拟 session"""
        session = MagicMock()
        resp = MagicMock()
        resp.json.return_value = {
            "ip": "5.6.7.8",
            "country_code": country_code,
            "city": "Test City",
            "region": "Test Region",
            "org": org,
        }
        session.get.return_value = resp
        return session

    def test_check_sync_match(self):
        """同步检测 — 国家匹配"""
        session = self._mock_session("US", "Comcast ISP")
        checker = ProxyChecker()
        result = checker.check(session, expected_country="US")

        assert result.is_country_match is True
        assert result.geo.ip == "5.6.7.8"
        assert result.geo.country == "US"
        assert result.expected_country == "US"
        assert result.latency_ms >= 0
        assert result.error is None

    def test_check_sync_mismatch(self):
        """同步检测 — 国家不匹配"""
        session = self._mock_session("DE", "Hetzner")
        checker = ProxyChecker()
        result = checker.check(session, expected_country="US")

        assert result.is_country_match is False
        assert result.reputation.is_datacenter is True

    def test_check_sync_all_api_fail(self):
        """同步检测 — 所有 API 失败时返回默认值 (不报错)"""
        session = MagicMock()
        session.get.side_effect = Exception("network failure")
        checker = ProxyChecker()
        result = checker.check(session, expected_country="US")

        # detect_geo 内部已处理异常，返回默认值
        assert result.error is None
        assert result.geo.ip == "unknown"
        assert result.geo.country == "unknown"
        assert result.is_country_match is False

    def test_check_async_callback(self):
        """异步检测 — 子线程 + callback"""
        session = self._mock_session("US", "Residential ISP")
        checker = ProxyChecker()

        results = []
        event = threading.Event()

        def on_result(r):
            results.append(r)
            event.set()

        thread = checker.check_async(session, expected_country="US", callback=on_result)
        assert isinstance(thread, threading.Thread)
        assert thread.daemon is True

        event.wait(timeout=5)
        assert len(results) == 1
        assert results[0].is_country_match is True

    def test_passed_property(self):
        """ProxyCheckResult.passed 属性"""
        # 国家匹配 + 非数据中心 → passed
        result = ProxyCheckResult(
            geo=GeoResult(country="US"),
            reputation=ReputationResult(is_datacenter=False),
            is_country_match=True,
        )
        assert result.passed is True

        # 数据中心 → not passed
        result2 = ProxyCheckResult(
            geo=GeoResult(country="US"),
            reputation=ReputationResult(is_datacenter=True),
            is_country_match=True,
        )
        assert result2.passed is False

    def test_get_matched_proxy_country(self):
        """国家匹配代理选择"""
        proxies = [
            "http://nl.proxy.com:8080",
            "http://us.residential.com:8080",
            "http://de.proxy.com:8080",
        ]
        result = ProxyChecker.get_matched_proxy("US", proxies)
        assert "us." in result

    def test_get_matched_proxy_fallback_residential(self):
        """无国家匹配时，优先返回住宅代理"""
        proxies = [
            "http://dc.example.com:8080",
            "http://residential.brightdata.com:8080",
        ]
        result = ProxyChecker.get_matched_proxy("JP", proxies)
        assert "residential" in result or "bright" in result

    def test_get_matched_proxy_empty(self):
        assert ProxyChecker.get_matched_proxy("US", []) is None


# ════════════════════════════════════════════
# formatter — 格式化输出测试
# ════════════════════════════════════════════

class TestFormatter:
    """终端格式化测试"""

    def test_format_match(self):
        result = ProxyCheckResult(
            geo=GeoResult(ip="1.2.3.4", country="US", city="NYC", org="ISP Co"),
            reputation=ReputationResult(
                proxy_type=ProxyType.RESIDENTIAL,
                risk_level=RiskLevel.LOW,
            ),
            is_country_match=True,
            expected_country="US",
            latency_ms=120.5,
        )
        output = format_result(result)
        assert "✅" in output
        assert "1.2.3.4" in output
        assert "US" in output

    def test_format_mismatch_datacenter(self):
        result = ProxyCheckResult(
            geo=GeoResult(ip="5.6.7.8", country="DE", city="Frankfurt", org="Hetzner"),
            reputation=ReputationResult(
                proxy_type=ProxyType.DATACENTER,
                is_datacenter=True,
                risk_level=RiskLevel.HIGH,
                provider="Hetzner",
            ),
            is_country_match=False,
            expected_country="US",
            latency_ms=200.0,
        )
        output = format_result(result)
        assert "⚠️" in output
        assert "数据中心" in output
        assert "Hetzner" in output

    def test_format_error(self):
        result = ProxyCheckResult(error="connection timeout")
        output = format_result(result)
        assert "❌" in output
        assert "connection timeout" in output

    def test_print_result_no_error(self, capsys):
        result = ProxyCheckResult(
            geo=GeoResult(ip="1.1.1.1", country="US", city="LA"),
            reputation=ReputationResult(proxy_type=ProxyType.RESIDENTIAL),
            is_country_match=True,
            expected_country="US",
            latency_ms=50,
        )
        print_result(result)
        captured = capsys.readouterr()
        assert "1.1.1.1" in captured.out
