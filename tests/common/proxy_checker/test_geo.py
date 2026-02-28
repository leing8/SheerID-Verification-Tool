"""
test_geo.py — 地理位置检测测试

使用 mock 代替真实网络请求，测试 detect_geo 和 infer_country_from_hostname。
"""

from unittest.mock import MagicMock

import pytest
from proxy_checker.geo import detect_geo, infer_country_from_hostname


# ── detect_geo 测试 ──────────────────────────


class TestDetectGeo:
    """detect_geo 正常流程 (mock session)"""

    def test_ipapi_success(self):
        """ipapi.co 返回正常 → 解析为 GeoResult"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "ip": "1.2.3.4",
            "country_code": "US",
            "city": "Los Angeles",
            "region": "California",
            "org": "Spectrum Cable",
            "timezone": "America/Los_Angeles",
        }
        session = MagicMock()
        session.get.return_value = mock_resp

        geo = detect_geo(session, timeout=5)

        assert geo.ip == "1.2.3.4"
        assert geo.country == "US"
        assert geo.city == "Los Angeles"
        assert geo.org == "Spectrum Cable"
        assert geo.timezone == "America/Los_Angeles"

    def test_country_code_uppercased(self):
        """小写 country_code 应被标准化为大写"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "ip": "1.2.3.4",
            "country_code": "nl",
            "city": "Amsterdam",
        }
        session = MagicMock()
        session.get.return_value = mock_resp

        geo = detect_geo(session)
        assert geo.country == "NL"


class TestDetectGeoFallback:
    """API 源故障转移"""

    def test_first_api_fail_fallback_to_second(self):
        """第一个 API 异常 → 自动回退到第二个"""
        mock_resp_ok = MagicMock()
        mock_resp_ok.json.return_value = {
            "ip": "5.6.7.8",
            "country": "DE",
            "city": "Frankfurt",
            "region": "Hessen",
            "org": "Hetzner",
            "timezone": "Europe/Berlin",
        }
        session = MagicMock()
        # 第一次 get 抛异常，第二次成功
        session.get.side_effect = [Exception("ipapi.co down"), mock_resp_ok]

        geo = detect_geo(session)

        assert geo.ip == "5.6.7.8"
        assert geo.country == "DE"
        assert session.get.call_count == 2

    def test_all_apis_fail_returns_default(self):
        """所有 API 均失败 → 返回默认 GeoResult"""
        session = MagicMock()
        session.get.side_effect = Exception("All APIs down")

        geo = detect_geo(session)

        assert geo.ip == "unknown"
        assert geo.country == "unknown"
        assert geo.city == "unknown"


# ── infer_country_from_hostname 测试 ──────────


class TestInferCountryFromHostname:
    """从代理主机名推断国家代码"""

    @pytest.mark.parametrize("hostname, expected_country", [
        ("us.proxy.example.com:8080", "US"),
        ("proxy-us-west.example.com", "US"),
        ("http://nl.proxy.io:3128", "NL"),
        ("amsterdam.proxy.net:8080", "NL"),
        ("proxy-uk-london.example.com", "UK"),
        ("london.proxy.example.com", "UK"),
        ("de.proxy.example.com:8080", "DE"),
        ("frankfurt.proxy.net:1080", "DE"),
        ("fr.proxy.example.com", "FR"),
        ("paris.cdn.example.com", "FR"),
        ("ca.proxy.example.com", "CA"),
        ("toronto.proxy.net", "CA"),
        ("au.proxy.example.com", "AU"),
        ("sydney.proxy.net", "AU"),
        ("jp.proxy.example.com", "JP"),
        ("tokyo.proxy.net", "JP"),
        ("sg.proxy.example.com", "SG"),
        ("singapore.proxy.net", "SG"),
        ("kr.proxy.example.com", "KR"),
        ("seoul.proxy.net", "KR"),
    ])
    def test_known_countries(self, hostname, expected_country):
        """已知国家标识应被正确识别"""
        assert infer_country_from_hostname(hostname) == expected_country

    @pytest.mark.parametrize("hostname", [
        "proxy.example.com:8080",
        "192.168.1.1:3128",
        "random-proxy.net",
        "",
    ])
    def test_unknown_returns_unknown(self, hostname):
        """无国家标识 → UNKNOWN"""
        assert infer_country_from_hostname(hostname) == "UNKNOWN"

    def test_case_insensitive(self):
        """大小写不敏感"""
        assert infer_country_from_hostname("US.PROXY.COM:8080") == "US"
        assert infer_country_from_hostname("AMSTERDAM.PROXY.NET") == "NL"
