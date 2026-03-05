"""DeviceIdentity 行为测试

覆盖:
- HTTP 请求头生成 (基础 + SheerID)
- frozen dataclass 不可变性
- __str__ 输出格式
- NewRelic span 递增
"""

import re

import pytest
from device_fingerprint_factory import DeviceIdentity
from device_fingerprint_factory.identity import (
    SHEERID_CLIENT_VERSION,
    SHEERID_CLIENT_NAME,
)


class TestGetHeaders:
    """请求头生成"""

    def test_basic_headers(self, sample_identity: DeviceIdentity) -> None:
        """基础请求头包含必要字段"""
        headers = sample_identity.get_headers(for_sheerid=False)

        assert "user-agent" in headers
        assert "sec-ch-ua" in headers
        assert "sec-ch-ua-platform" in headers
        assert "accept" in headers
        assert "accept-language" in headers

    def test_user_agent_matches_identity(
        self, sample_identity: DeviceIdentity
    ) -> None:
        """请求头中的 UA 与 identity 属性一致"""
        headers = sample_identity.get_headers(for_sheerid=False)
        assert headers["user-agent"] == sample_identity.user_agent

    def test_sheerid_headers(self, sample_identity: DeviceIdentity) -> None:
        """SheerID 模式包含额外字段"""
        headers = sample_identity.get_headers(for_sheerid=True)

        assert headers["clientversion"] == SHEERID_CLIENT_VERSION
        assert headers["clientname"] == SHEERID_CLIENT_NAME
        assert "newrelic" in headers
        assert "traceparent" in headers
        assert "tracestate" in headers
        assert headers["content-type"] == "application/json"

    def test_no_sheerid_headers_when_disabled(
        self, sample_identity: DeviceIdentity
    ) -> None:
        """非 SheerID 模式不包含额外字段"""
        headers = sample_identity.get_headers(for_sheerid=False)

        assert "clientversion" not in headers
        assert "newrelic" not in headers
        assert "traceparent" not in headers

    def test_traceparent_format(
        self, sample_identity: DeviceIdentity
    ) -> None:
        """traceparent 格式: 00-{trace_id}-{span_id}-01"""
        headers = sample_identity.get_headers(for_sheerid=True)
        tp = headers["traceparent"]
        assert re.fullmatch(r"00-[0-9a-f]{32}-[0-9a-f]{16}-01", tp)


class TestNewRelicSpanIncrement:
    """NewRelic span 递增验证"""

    def test_span_id_changes_across_calls(
        self, sample_identity: DeviceIdentity
    ) -> None:
        """多次 get_headers() 调用产生不同 span_id"""
        h1 = sample_identity.get_headers(for_sheerid=True)
        h2 = sample_identity.get_headers(for_sheerid=True)

        tp1 = h1["traceparent"]
        tp2 = h2["traceparent"]

        # trace_id 相同
        trace_id_1 = tp1.split("-")[1]
        trace_id_2 = tp2.split("-")[1]
        assert trace_id_1 == trace_id_2

        # span_id 不同
        span_id_1 = tp1.split("-")[2]
        span_id_2 = tp2.split("-")[2]
        assert span_id_1 != span_id_2


class TestFrozenDataclass:
    """不可变性验证"""

    def test_cannot_set_attribute(
        self, sample_identity: DeviceIdentity
    ) -> None:
        """frozen dataclass 属性不可修改"""
        with pytest.raises(AttributeError):
            sample_identity.fingerprint_hash = "modified"  # type: ignore[misc]

    def test_cannot_set_verification_id(
        self, sample_identity: DeviceIdentity
    ) -> None:
        """verification_id 不可修改"""
        with pytest.raises(AttributeError):
            sample_identity.verification_id = "new_vid"  # type: ignore[misc]


class TestStrRepresentation:
    """__str__ 输出"""

    def test_str_contains_key_info(
        self, sample_identity: DeviceIdentity
    ) -> None:
        """字符串表示包含关键信息"""
        output = str(sample_identity)
        assert "DeviceIdentity" in output
        assert sample_identity.device.brand in output
        assert sample_identity.device.model in output
        assert sample_identity.fingerprint_hash in output
        assert sample_identity.timezone_name in output
