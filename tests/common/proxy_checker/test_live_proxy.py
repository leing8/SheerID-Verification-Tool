"""
test_live_proxy.py — 实时代理集成测试

通过真实代理地址验证以下能力:
  1. 格式解析  — 代理字符串能否被正确解析
  2. 地理位置  — 出口 IP 所在国家/城市/时区
  3. IP 属性  — 住宅 / 数据中心 / ISP / Mobile
  4. 纯净度   — 风险等级评估
  5. 综合报告  — 格式化终端输出

使用方式:
    pytest tests/common/proxy_checker/test_live_proxy.py -v -s \\
        --proxy="http://user:pass@host:port"

未提供 --proxy 时，所有测试自动跳过。
"""

import pytest

from proxy_checker import (
    ProxyChecker,
    evaluate_reputation,
    format_result,
    parse_proxy,
    print_result,
)
from proxy_checker.models import ProxyCheckResult, ProxyType, RiskLevel


# ──────────────────────────────────────────────────────
# 格式解析测试
# ──────────────────────────────────────────────────────

class TestLiveProxyFormat:
    """验证代理字符串格式能被正确解析"""

    def test_proxy_parseable(self, proxy_url):
        """代理地址必须能被 parse_proxy 正确解析"""
        info = parse_proxy(proxy_url)

        print(f"\n{'=' * 60}")
        print(f"  代理格式解析结果")
        print(f"{'=' * 60}")
        print(f"  原始地址   : {proxy_url}")

        assert info is not None, (
            f"代理地址格式无效，无法解析: {proxy_url!r}\n"
            f"支持格式: http://host:port | http://user:pass@host:port | "
            f"socks5://host:port | host:port | host:port:user:pass"
        )

        print(f"  协议       : {info.protocol}")
        print(f"  主机       : {info.host}")
        print(f"  端口       : {info.port}")
        print(f"  用户名     : {info.username or '(无)'}")
        print(f"  密码       : {'*' * len(info.password) if info.password else '(无)'}")
        print(f"{'=' * 60}")

        assert info.host, "主机名不能为空"
        assert info.port > 0, f"端口号无效: {info.port}"

    def test_proxy_protocol_valid(self, proxy_url):
        """代理协议必须是支持的类型"""
        info = parse_proxy(proxy_url)
        assert info is not None
        assert info.protocol in ("http", "https", "socks5", "socks4"), (
            f"不支持的代理协议: {info.protocol}"
        )


# ──────────────────────────────────────────────────────
# 实时地理位置测试
# ──────────────────────────────────────────────────────

class TestLiveGeoDetection:
    """通过代理发起真实 HTTP 请求，验证出口 IP 地理信息"""

    def test_geo_detection_succeeds(self, proxy_session):
        """地理位置检测必须返回有效结果（非 unknown）"""
        from proxy_checker.geo import detect_geo

        geo = detect_geo(proxy_session, timeout=15)

        print(f"\n{'=' * 60}")
        print(f"  地理位置检测结果")
        print(f"{'=' * 60}")
        print(f"  出口 IP    : {geo.ip}")
        print(f"  国家代码   : {geo.country}")
        print(f"  城市       : {geo.city}")
        print(f"  地区       : {geo.region or '(未知)'}")
        print(f"  组织/ISP   : {geo.org or '(未知)'}")
        print(f"  时区       : {geo.timezone or '(未知)'}")
        print(f"{'=' * 60}")

        assert geo.ip != "unknown", (
            "无法获取出口 IP，代理可能无法连接或被封禁"
        )
        assert geo.country != "unknown", (
            f"无法识别国家代码，IP={geo.ip}"
        )
        assert len(geo.country) == 2, (
            f"国家代码应为 2 位 ISO 代码，实际: {geo.country!r}"
        )

    def test_geo_country_is_uppercase(self, proxy_session):
        """国家代码应为大写"""
        from proxy_checker.geo import detect_geo
        geo = detect_geo(proxy_session, timeout=15)
        if geo.country != "unknown":
            assert geo.country == geo.country.upper(), (
                f"国家代码未标准化为大写: {geo.country!r}"
            )


# ──────────────────────────────────────────────────────
# IP 属性测试
# ──────────────────────────────────────────────────────

class TestLiveReputationEvaluation:
    """基于真实 Geo 结果评估 IP 属性和纯净度"""

    def test_reputation_evaluated(self, proxy_session):
        """IP 属性必须被成功评估"""
        from proxy_checker.geo import detect_geo

        geo = detect_geo(proxy_session, timeout=15)
        rep = evaluate_reputation(org=geo.org)

        print(f"\n{'=' * 60}")
        print(f"  IP 属性评估结果")
        print(f"{'=' * 60}")
        print(f"  IP 归属组织  : {geo.org or '(未知)'}")
        print(f"  代理类型     : {rep.proxy_type.value}")
        print(f"  是否数据中心 : {'⚠️  是' if rep.is_datacenter else '✅ 否'}")
        print(f"  风险等级     : {rep.risk_level.value.upper()}")
        print(f"  提供商       : {rep.provider or '(未识别)'}")
        print(f"{'=' * 60}")

        assert rep.proxy_type in ProxyType, f"非法代理类型: {rep.proxy_type}"
        assert rep.risk_level in RiskLevel, f"非法风险等级: {rep.risk_level}"

    def test_residential_proxy_not_datacenter(self, proxy_session):
        """
        建议测试（软断言）：住宅/ISP 代理不应被识别为数据中心。
        数据中心代理用于 SheerID 验证时更容易被拒绝。
        """
        from proxy_checker.geo import detect_geo

        geo = detect_geo(proxy_session, timeout=15)
        rep = evaluate_reputation(org=geo.org)

        if rep.is_datacenter:
            pytest.warns(
                None,
                match=None,
            )
            print(
                f"\n  ⚠️  警告: 检测到数据中心 IP ({rep.provider or geo.org})，"
                f"建议换用住宅/ISP 代理以提高 SheerID 验证通过率"
            )
        else:
            assert rep.proxy_type in (
                ProxyType.RESIDENTIAL, ProxyType.ISP,
                ProxyType.MOBILE, ProxyType.UNKNOWN,
            )


# ──────────────────────────────────────────────────────
# 综合检测 + 完整报告
# ──────────────────────────────────────────────────────

class TestLiveFullCheck:
    """完整 ProxyChecker.check 流程测试"""

    @pytest.mark.parametrize("expected_country", ["US"])
    def test_full_check_output(self, proxy_session, expected_country):
        """
        运行完整检测并打印结果报告。
        不要求必须通过（代理实际国家可能不同），只要检测流程本身不报错。
        """
        checker = ProxyChecker()
        result = checker.check(proxy_session, expected_country=expected_country, timeout=15)

        print(f"\n{'=' * 60}")
        print(f"  完整代理检测报告  (预期国家: {expected_country})")
        print(f"{'=' * 60}")

        if result.error:
            print(f"\n  ❌ 检测失败: {result.error}")
            print(f"\n  可能原因:")
            print(f"    - 代理无法连接")
            print(f"    - 代理需要认证但凭据有误")
            print(f"    - 所有 IP 检测 API 均超时")
            pytest.fail(f"代理检测失败: {result.error}")
        else:
            print_result(result)
            _print_detailed_report(result)

        assert result.error is None, f"代理检测出错: {result.error}"
        assert result.geo.ip != "unknown", "未能获取真实 IP"

    def test_full_check_records_latency(self, proxy_session):
        """检测应记录有效延迟时间"""
        checker = ProxyChecker()
        result = checker.check(proxy_session, timeout=15)

        if result.error is None:
            print(f"\n  延迟: {result.latency_ms:.0f} ms")
            assert result.latency_ms >= 0


# ──────────────────────────────────────────────────────
# 内部工具
# ──────────────────────────────────────────────────────

def _print_detailed_report(result: ProxyCheckResult) -> None:
    """输出详细的代理检测报告"""
    geo = result.geo
    rep = result.reputation

    print(f"\n  ── 地理信息 ──")
    print(f"  出口 IP      : {geo.ip}")
    print(f"  国家         : {geo.country}")
    print(f"  城市         : {geo.city}")
    print(f"  地区         : {geo.region or '(未知)'}")
    print(f"  组织/ISP     : {geo.org or '(未知)'}")
    print(f"  时区         : {geo.timezone or '(未知)'}")

    print(f"\n  ── IP 属性 ──")
    print(f"  代理类型     : {rep.proxy_type.value}")
    print(f"  是否数据中心 : {'⚠️  是 (高风险)' if rep.is_datacenter else '✅ 否'}")
    print(f"  风险等级     : {rep.risk_level.value.upper()}")
    print(f"  提供商       : {rep.provider or '(未识别)'}")

    print(f"\n  ── 综合结论 ──")
    print(f"  预期国家     : {result.expected_country}")
    print(f"  国家匹配     : {'✅ 是' if result.is_country_match else '❌ 否'}")
    print(f"  综合通过     : {'✅ PASS' if result.passed else '❌ FAIL'}")
    print(f"  检测延迟     : {result.latency_ms:.0f} ms")
    print(f"{'=' * 60}")
