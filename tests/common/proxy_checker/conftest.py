"""
tests/common/proxy_checker/conftest.py

proxy_checker 专属 fixtures。
顶层 conftest.py 的 sample_vid fixtures 在此继承可用。
"""

import pytest

from proxy_checker import ProxyChecker
from proxy_checker.models import (
    GeoResult,
    ProxyCheckResult,
    ProxyType,
    ReputationResult,
    RiskLevel,
)


@pytest.fixture
def checker():
    """返回 ProxyChecker 实例"""
    return ProxyChecker()


@pytest.fixture
def sample_geo_result():
    """返回一个模拟的美国住宅 IP 地理信息"""
    return GeoResult(
        ip="203.0.113.42",
        country="US",
        city="Los Angeles",
        region="California",
        org="Spectrum Cable",
        timezone="America/Los_Angeles",
    )


@pytest.fixture
def sample_reputation():
    """返回一个住宅代理的纯净度评估结果"""
    return ReputationResult(
        proxy_type=ProxyType.RESIDENTIAL,
        is_datacenter=False,
        risk_level=RiskLevel.LOW,
        provider="",
    )


@pytest.fixture
def sample_check_result(sample_geo_result, sample_reputation):
    """返回一个完整的代理检测通过结果"""
    return ProxyCheckResult(
        geo=sample_geo_result,
        reputation=sample_reputation,
        is_country_match=True,
        expected_country="US",
        latency_ms=156.3,
    )


@pytest.fixture
def sample_error_result():
    """返回一个检测失败的结果"""
    return ProxyCheckResult(
        expected_country="US",
        error="Connection timeout",
    )


# ── 实时代理 Fixtures ────────────────────────────────────

@pytest.fixture
def proxy_url(request):
    """
    从 --proxy 参数读取代理地址。
    未提供则跳过测试。

    使用方式:
        pytest tests/common/proxy_checker/test_live_proxy.py -v -s --proxy="http://user:pass@host:port"
    """
    url = request.config.getoption("--proxy")
    if not url:
        pytest.skip("需要 --proxy 参数才能运行实时代理测试")
    return url


@pytest.fixture
def proxy_session(proxy_url):
    """
    创建配置了指定代理的 curl_cffi 会话。
    自动以 Chrome 浏览器身份进行 TLS 握手。
    """
    from curl_cffi.requests import Session
    session = Session(impersonate="chrome110")
    session.proxies = {
        "http": proxy_url,
        "https": proxy_url,
    }
    yield session
    session.close()

