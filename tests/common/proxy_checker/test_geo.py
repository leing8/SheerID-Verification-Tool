"""地理位置检测测试

覆盖:
- detect_geo 成功
- API 源故障转移
- 全部失败默认值
- 主机名国家推断
"""

import pytest
from proxy_checker.geo import detect_geo, infer_country_from_hostname
from proxy_checker.models import GeoResult


class MockResponseOk:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


class MockSessionSingleSource:
    """只对第一个 API 源成功"""

    def __init__(self, data):
        self._data = data
        self._call_count = 0

    def get(self, url, **kwargs):
        self._call_count += 1
        return MockResponseOk(self._data)


class MockSessionFailFirst:
    """第一个 API 失败，第二个成功"""

    def __init__(self, data):
        self._data = data
        self._call_count = 0

    def get(self, url, **kwargs):
        self._call_count += 1
        if self._call_count == 1:
            raise ConnectionError("first source failed")
        return MockResponseOk(self._data)


class MockSessionAllFail:
    """所有 API 源失败"""

    def get(self, url, **kwargs):
        raise ConnectionError("all sources fail")


class TestDetectGeo:
    """detect_geo 检测"""

    def test_success_first_source(self) -> None:
        """第一个 API 源成功"""
        session = MockSessionSingleSource({
            "ip": "1.2.3.4",
            "country_code": "US",
            "city": "Seattle",
            "region": "WA",
            "org": "ISP Co",
            "timezone": "America/Los_Angeles",
        })
        result = detect_geo(session)

        assert isinstance(result, GeoResult)
        assert result.ip == "1.2.3.4"
        assert result.country == "US"
        assert result.city == "Seattle"

    def test_failover_to_second_source(self) -> None:
        """第一个失败，回退到第二个"""
        session = MockSessionFailFirst({
            "ip": "5.6.7.8",
            "country": "DE",
            "city": "Berlin",
            "region": "Berlin",
            "org": "Provider",
            "timezone": "Europe/Berlin",
        })
        result = detect_geo(session)

        assert isinstance(result, GeoResult)
        assert result.ip == "5.6.7.8"

    def test_all_fail_returns_default(self) -> None:
        """全部失败返回默认 GeoResult"""
        session = MockSessionAllFail()
        result = detect_geo(session)

        assert result.ip == "unknown"
        assert result.country == "unknown"

    def test_country_code_uppercase(self) -> None:
        """国家代码自动大写"""
        session = MockSessionSingleSource({
            "ip": "1.2.3.4",
            "country_code": "us",
            "city": "Test",
        })
        result = detect_geo(session)
        assert result.country == "US"


class TestInferCountry:
    """主机名国家推断"""

    @pytest.mark.parametrize("proxy,expected", [
        ("http://us.proxy.example:8080", "US"),
        ("http://proxy-us-east.example:8080", "US"),
        ("http://nl.proxy.example:8080", "NL"),
        ("http://amsterdam.proxy.example:8080", "NL"),
        ("http://uk.proxy.example:8080", "UK"),
        ("http://london.proxy.example:8080", "UK"),
        ("http://de.proxy.example:8080", "DE"),
        ("http://frankfurt.proxy.example:8080", "DE"),
        ("http://jp.proxy.example:8080", "JP"),
        ("http://tokyo.proxy.example:8080", "JP"),
    ])
    def test_known_countries(self, proxy: str, expected: str) -> None:
        """已知国家推断"""
        assert infer_country_from_hostname(proxy) == expected

    def test_unknown_hostname(self) -> None:
        """未知主机名返回 UNKNOWN"""
        assert infer_country_from_hostname("http://random.example:8080") == "UNKNOWN"

    def test_case_insensitive(self) -> None:
        """不区分大小写"""
        assert infer_country_from_hostname("http://US.PROXY.EXAMPLE:8080") == "US"
