"""
test_formatter.py — 终端输出格式化测试

测试 format_result 和 print_result 的输出内容正确性。
"""

from proxy_checker.formatter import format_result, print_result
from proxy_checker.models import (
    GeoResult,
    ProxyCheckResult,
    ProxyType,
    ReputationResult,
    RiskLevel,
)


class TestFormatResultSuccess:
    """成功结果的格式化输出"""

    def test_contains_ip_and_country(self, sample_check_result):
        """输出应包含 IP 和国家信息"""
        output = format_result(sample_check_result)
        assert "203.0.113.42" in output
        assert "US" in output
        assert "Los Angeles" in output

    def test_contains_org(self, sample_check_result):
        """输出应包含 org 信息"""
        output = format_result(sample_check_result)
        assert "Spectrum Cable" in output

    def test_country_match_shows_checkmark(self, sample_check_result):
        """国家匹配 → 显示 ✅"""
        output = format_result(sample_check_result)
        assert "✅" in output

    def test_contains_proxy_type(self, sample_check_result):
        """输出应包含代理类型"""
        output = format_result(sample_check_result)
        assert "residential" in output

    def test_contains_latency(self, sample_check_result):
        """输出应包含延迟信息"""
        output = format_result(sample_check_result)
        assert "156" in output


class TestFormatResultCountryMismatch:
    """国家不匹配的格式化输出"""

    def test_mismatch_shows_warning(self):
        """国家不匹配 → 显示 ⚠️ 警告"""
        result = ProxyCheckResult(
            geo=GeoResult(ip="1.2.3.4", country="DE", city="Frankfurt"),
            reputation=ReputationResult(),
            is_country_match=False,
            expected_country="US",
        )
        output = format_result(result)
        assert "⚠️" in output
        assert "US" in output


class TestFormatResultDatacenter:
    """数据中心 IP 的格式化输出"""

    def test_datacenter_shows_warning(self):
        """数据中心 IP → 显示数据中心警告"""
        result = ProxyCheckResult(
            geo=GeoResult(ip="1.2.3.4", country="US", city="Ashburn", org="AWS"),
            reputation=ReputationResult(
                proxy_type=ProxyType.DATACENTER,
                is_datacenter=True,
                risk_level=RiskLevel.HIGH,
                provider="AWS",
            ),
            is_country_match=True,
            expected_country="US",
        )
        output = format_result(result)
        assert "数据中心" in output
        assert "AWS" in output

    def test_datacenter_suggests_residential(self):
        """数据中心警告应建议使用住宅代理"""
        result = ProxyCheckResult(
            geo=GeoResult(ip="1.2.3.4", country="US", city="Ashburn"),
            reputation=ReputationResult(
                proxy_type=ProxyType.DATACENTER,
                is_datacenter=True,
                risk_level=RiskLevel.HIGH,
            ),
            is_country_match=True,
            expected_country="US",
        )
        output = format_result(result)
        assert "住宅代理" in output


class TestFormatResultError:
    """错误结果的格式化输出"""

    def test_error_shows_message(self, sample_error_result):
        """错误结果 → 显示 ❌ 和错误消息"""
        output = format_result(sample_error_result)
        assert "❌" in output
        assert "Connection timeout" in output

    def test_error_contains_fail_text(self, sample_error_result):
        """错误结果包含'失败'字样"""
        output = format_result(sample_error_result)
        assert "失败" in output


class TestPrintResult:
    """print_result 函数"""

    def test_print_calls_format(self, sample_check_result, capsys):
        """print_result 应输出 format_result 的结果"""
        print_result(sample_check_result)
        captured = capsys.readouterr()
        assert "203.0.113.42" in captured.out

    def test_print_error_result(self, sample_error_result, capsys):
        """print_result 应输出错误信息"""
        print_result(sample_error_result)
        captured = capsys.readouterr()
        assert "Connection timeout" in captured.out
