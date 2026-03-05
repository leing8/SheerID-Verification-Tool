"""模拟 verifier.py 调用链的集成测试

验证 device_fingerprint_factory 生成的设备指纹信息
可以正确用于 verifier.py 中的 SheerID API 请求。

覆盖:
- 完整调用链模拟 (DeviceIdentityFactory → DeviceIdentity → headers/fingerprint)
- fingerprint_hash 作为 deviceFingerprintHash 字段
- headers 自洽性 (UA ↔ sec-ch-ua ↔ platform)
- 所有字段非空验证
- 多次 get_headers() 调用一致性
"""

import re

import pytest
from device_fingerprint_factory import DeviceIdentityFactory, DeviceIdentity
from device_fingerprint_factory.signals import CHROME_VERSION_MAP

SAMPLE_VID = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"


class TestVerifierFingerprintFlow:
    """模拟 verifier.py 的完整调用链"""

    def test_full_flow(self) -> None:
        """
        模拟 verifier.py 中的调用:
            factory = DeviceIdentityFactory()
            identity = factory.create(vid)
            fingerprint = identity.fingerprint_hash
            headers = identity.get_headers(for_sheerid=True)
        """
        # 1. 创建工厂 (与 verifier.py 一致)
        factory = DeviceIdentityFactory()

        # 2. 生成设备身份
        identity = factory.create(SAMPLE_VID)

        # 3. 获取指纹哈希 (用于 API body 中的 deviceFingerprintHash)
        fingerprint = identity.fingerprint_hash
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 32
        assert re.fullmatch(r"[0-9a-f]{32}", fingerprint)

        # 4. 获取请求头 (用于 HTTP 请求)
        headers = identity.get_headers(for_sheerid=True)
        assert isinstance(headers, dict)
        assert "user-agent" in headers
        assert "clientversion" in headers

        # 5. impersonate_key 用于 TLS 会话
        assert identity.impersonate_key in CHROME_VERSION_MAP

    def test_fingerprint_hash_in_request_body(self) -> None:
        """fingerprint_hash 可作为 deviceFingerprintHash 字段"""
        factory = DeviceIdentityFactory()
        identity = factory.create(SAMPLE_VID)

        # 构建与 verifier.py 一致的请求体
        body = {
            "firstName": "Test",
            "lastName": "User",
            "deviceFingerprintHash": identity.fingerprint_hash,
        }

        # 验证字段存在且格式正确
        assert "deviceFingerprintHash" in body
        assert re.fullmatch(r"[0-9a-f]{32}", body["deviceFingerprintHash"])


class TestHeadersSelfConsistency:
    """请求头自洽性 — 与 verifier.py 中的一致性检查对齐"""

    def test_ua_contains_chrome_version(
        self, sample_identity: DeviceIdentity
    ) -> None:
        """User-Agent 包含对应的 Chrome 版本号"""
        ua = sample_identity.user_agent
        assert sample_identity.chrome_version in ua

    def test_sec_ch_ua_matches_chrome_version(
        self, sample_identity: DeviceIdentity
    ) -> None:
        """sec-ch-ua 与 Chrome 版本一致"""
        # 从 impersonate_key 提取主版本号
        major_ver = sample_identity.chrome_version.split(".")[0]
        assert f'v="{major_ver}"' in sample_identity.sec_ch_ua

    def test_platform_matches_ua(
        self, sample_identity: DeviceIdentity
    ) -> None:
        """platform 与 User-Agent 中的 OS 一致"""
        ua = sample_identity.user_agent
        platform = sample_identity.platform

        if platform == "Win32":
            assert "Windows" in ua
        elif platform == "MacIntel":
            assert "Macintosh" in ua

    def test_sec_ch_ua_platform_consistent(
        self, sample_identity: DeviceIdentity
    ) -> None:
        """sec-ch-ua-platform 与 device.os_family 一致"""
        os_family = sample_identity.device.os_family
        sec_platform = sample_identity.sec_ch_ua_platform

        if os_family == "windows":
            assert sec_platform == '"Windows"'
        elif os_family == "macos":
            assert sec_platform == '"macOS"'


class TestAllFieldsPopulated:
    """验证所有字段非空"""

    def test_identity_all_fields_populated(
        self, sample_identity: DeviceIdentity
    ) -> None:
        """所有字段非空非 None"""
        assert sample_identity.verification_id
        assert sample_identity.device is not None
        assert sample_identity.chrome_version
        assert sample_identity.impersonate_key
        assert sample_identity.timezone_name
        assert sample_identity.timezone_offset is not None
        assert sample_identity.canvas_hash
        assert sample_identity.webgl_vendor
        assert sample_identity.webgl_renderer
        assert sample_identity.audio_fingerprint
        assert sample_identity.screen_width > 0
        assert sample_identity.screen_height > 0
        assert sample_identity.color_depth > 0
        assert sample_identity.pixel_ratio > 0
        assert sample_identity.language
        assert sample_identity.platform
        assert sample_identity.cpu_cores > 0
        assert sample_identity.device_memory > 0
        assert sample_identity.session_id
        assert sample_identity.webgl_hash
        assert sample_identity.font_hash
        assert sample_identity.fingerprint_hash
        assert sample_identity.user_agent
        assert sample_identity.sec_ch_ua
        assert sample_identity.sec_ch_ua_platform

    def test_device_fields_populated(
        self, sample_identity: DeviceIdentity
    ) -> None:
        """设备档案字段完整"""
        device = sample_identity.device
        assert device.brand
        assert device.model
        assert device.config_label
        assert device.device_type == "desktop"
        assert device.os_family in ("windows", "macos")


class TestMultipleHeadersCalls:
    """多次请求头调用的行为"""

    def test_ua_stable_across_calls(
        self, sample_identity: DeviceIdentity
    ) -> None:
        """多次调用返回相同 User-Agent"""
        h1 = sample_identity.get_headers(for_sheerid=True)
        h2 = sample_identity.get_headers(for_sheerid=True)
        assert h1["user-agent"] == h2["user-agent"]

    def test_sec_ch_ua_stable(
        self, sample_identity: DeviceIdentity
    ) -> None:
        """sec-ch-ua 在多次调用间不变"""
        h1 = sample_identity.get_headers(for_sheerid=True)
        h2 = sample_identity.get_headers(for_sheerid=True)
        assert h1["sec-ch-ua"] == h2["sec-ch-ua"]

    def test_newrelic_trace_id_stable(
        self, sample_identity: DeviceIdentity
    ) -> None:
        """NewRelic trace_id 在同一 identity 内不变"""
        h1 = sample_identity.get_headers(for_sheerid=True)
        h2 = sample_identity.get_headers(for_sheerid=True)

        trace1 = h1["traceparent"].split("-")[1]
        trace2 = h2["traceparent"].split("-")[1]
        assert trace1 == trace2
