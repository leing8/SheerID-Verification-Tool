"""
test_identity.py — DeviceIdentity 行为测试

测试 HTTP 头生成、NewRelic 追踪头、硬编码常量等。
"""

import base64
import json
import re

import pytest


class TestHTTPHeaders:
    """HTTP 头生成"""

    def test_headers_contain_user_agent(self, sample_identity):
        """请求头包含正确的 User-Agent"""
        headers = sample_identity.get_headers(for_sheerid=True)
        assert headers["user-agent"] == sample_identity.user_agent

    def test_headers_contain_sec_ch_ua(self, sample_identity):
        """请求头包含 sec-ch-ua"""
        headers = sample_identity.get_headers(for_sheerid=True)
        assert "sec-ch-ua" in headers
        assert headers["sec-ch-ua"] == sample_identity.sec_ch_ua

    def test_sheerid_headers_include_client_info(self, sample_identity):
        """SheerID 请求头包含 clientversion 和 clientname"""
        from device_fingerprint_factory.identity import (
            SHEERID_CLIENT_NAME,
            SHEERID_CLIENT_VERSION,
        )
        headers = sample_identity.get_headers(for_sheerid=True)
        assert headers["clientversion"] == SHEERID_CLIENT_VERSION
        assert headers["clientname"] == SHEERID_CLIENT_NAME

    def test_sheerid_headers_include_origin(self, sample_identity):
        """SheerID 请求头包含正确的 origin 和 referer"""
        from device_fingerprint_factory.identity import SHEERID_ORIGIN
        headers = sample_identity.get_headers(for_sheerid=True)
        assert headers["origin"] == SHEERID_ORIGIN
        assert headers["referer"] == f"{SHEERID_ORIGIN}/"

    def test_non_sheerid_headers_exclude_client_info(self, sample_identity):
        """非 SheerID 请求头不包含 clientversion"""
        headers = sample_identity.get_headers(for_sheerid=False)
        assert "clientversion" not in headers
        assert "clientname" not in headers
        assert "newrelic" not in headers

    def test_headers_accept_language_consistent(self, sample_identity):
        """accept-language 应与 device identity 的 language 一致"""
        headers = sample_identity.get_headers(for_sheerid=True)
        assert sample_identity.language in headers["accept-language"]


class TestNewRelicTracing:
    """NewRelic 追踪头"""

    def test_newrelic_header_is_valid_base64_json(self, sample_identity):
        """newrelic 头应为有效的 Base64 编码 JSON"""
        headers = sample_identity.get_headers(for_sheerid=True)
        decoded = json.loads(base64.b64decode(headers["newrelic"]))
        assert decoded["v"] == [0, 1]
        assert decoded["d"]["ty"] == "Browser"

    def test_newrelic_uses_correct_account_ids(self, sample_identity):
        """NewRelic 使用正确的 account/app ID"""
        from device_fingerprint_factory.identity import (
            NEWRELIC_ACCOUNT_ID,
            NEWRELIC_APP_ID,
        )
        headers = sample_identity.get_headers(for_sheerid=True)
        decoded = json.loads(base64.b64decode(headers["newrelic"]))
        assert decoded["d"]["ac"] == NEWRELIC_ACCOUNT_ID
        assert decoded["d"]["ap"] == NEWRELIC_APP_ID

    def test_trace_id_reused_across_requests(self, sample_identity):
        """同一 identity 多次调用应复用相同的 trace_id"""
        headers1 = sample_identity.get_headers(for_sheerid=True)
        headers2 = sample_identity.get_headers(for_sheerid=True)
        payload1 = json.loads(base64.b64decode(headers1["newrelic"]))
        payload2 = json.loads(base64.b64decode(headers2["newrelic"]))
        assert payload1["d"]["tr"] == payload2["d"]["tr"]

    def test_span_id_changes_across_requests(self, sample_identity):
        """同一 identity 多次调用应产生不同的 span_id"""
        headers1 = sample_identity.get_headers(for_sheerid=True)
        headers2 = sample_identity.get_headers(for_sheerid=True)
        payload1 = json.loads(base64.b64decode(headers1["newrelic"]))
        payload2 = json.loads(base64.b64decode(headers2["newrelic"]))
        assert payload1["d"]["id"] != payload2["d"]["id"]

    def test_traceparent_format(self, sample_identity):
        """traceparent 应符合 W3C Trace Context 格式"""
        headers = sample_identity.get_headers(for_sheerid=True)
        pattern = r'^00-[0-9a-f]{32}-[0-9a-f]{16}-01$'
        assert re.match(pattern, headers["traceparent"])


class TestConfigConstants:
    """配置常量合理性"""

    def test_client_version_format(self):
        """clientversion 应为有效的语义化版本号"""
        from device_fingerprint_factory.identity import SHEERID_CLIENT_VERSION
        assert re.match(r'^\d+\.\d+\.\d+$', SHEERID_CLIENT_VERSION)

    def test_newrelic_ids_are_numeric(self):
        """NewRelic ID 应为纯数字字符串"""
        from device_fingerprint_factory.identity import (
            NEWRELIC_ACCOUNT_ID,
            NEWRELIC_APP_ID,
        )
        assert NEWRELIC_ACCOUNT_ID.isdigit()
        assert NEWRELIC_APP_ID.isdigit()

    def test_origin_is_https(self):
        """origin 应为 HTTPS URL"""
        from device_fingerprint_factory.identity import SHEERID_ORIGIN
        assert SHEERID_ORIGIN.startswith("https://")
