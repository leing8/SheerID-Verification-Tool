"""共享 fixtures for proxy_checker 测试

运行以下命令进行测试
  pytest tests/common/proxy_checker/test_verifier_integration.py::TestVerifierProxyFlow::test_full_flow_residential_us -v --log-cli-level=DEBUG

"""

import pytest

from proxy_checker import ProxyChecker
from proxy_checker.models import GeoResult, ProxyCheckResult, ReputationResult, ProxyType, RiskLevel


class MockResponse:
    """模拟 HTTP 响应"""

    def __init__(self, json_data: dict, status_code: int = 200):
        self._json_data = json_data
        self.status_code = status_code
        self.text = str(json_data)

    def json(self):
        return self._json_data


class MockSession:
    """模拟 HTTP 会话 — 返回预设的 geo API 响应"""

    def __init__(self, geo_data: dict = None):
        self._geo_data = geo_data or {
            "ip": "203.0.113.42",
            "country_code": "US",
            "city": "New York",
            "region": "New York",
            "org": "Comcast Cable Communications",
            "timezone": "America/New_York",
        }

    def get(self, url: str, **kwargs) -> MockResponse:
        return MockResponse(self._geo_data)


class FailingSession:
    """模拟全部 API 源失败的会话"""

    def get(self, url: str, **kwargs):
        raise ConnectionError(f"connection refused: {url}")


@pytest.fixture
def checker() -> ProxyChecker:
    """ProxyChecker 实例"""
    return ProxyChecker()


@pytest.fixture
def mock_session() -> MockSession:
    """模拟美国住宅 IP 的会话"""
    return MockSession()


@pytest.fixture
def mock_session_non_us() -> MockSession:
    """模拟非美国 IP 的会话"""
    return MockSession({
        "ip": "198.51.100.7",
        "country_code": "DE",
        "city": "Frankfurt",
        "region": "Hessen",
        "org": "Deutsche Telekom AG",
        "timezone": "Europe/Berlin",
    })


@pytest.fixture
def mock_session_datacenter() -> MockSession:
    """模拟数据中心 IP 的会话"""
    return MockSession({
        "ip": "54.23.45.67",
        "country_code": "US",
        "city": "Ashburn",
        "region": "Virginia",
        "org": "Amazon.com, Inc. (AWS)",
        "timezone": "America/New_York",
    })


@pytest.fixture
def failing_session() -> FailingSession:
    """模拟全部 API 失败的会话"""
    return FailingSession()
