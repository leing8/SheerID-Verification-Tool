"""
test_factory.py — DeviceIdentityFactory 核心行为测试

测试确定性生成、信号自洽性、哈希正确性等关键属性。
"""

import re

import pytest


class TestDeterministicGeneration:
    """确定性生成: 同一 VID → 同一指纹"""

    def test_same_vid_produces_identical_hash(self, factory):
        """同一 VID 多次调用产生完全相同的 fingerprint_hash"""
        vid = "test-deterministic-001"
        identity1 = factory.create(vid)
        identity2 = factory.create(vid)
        assert identity1.fingerprint_hash == identity2.fingerprint_hash

    def test_same_vid_produces_identical_device(self, factory):
        """同一 VID 多次调用选择同一设备"""
        vid = "test-deterministic-002"
        identity1 = factory.create(vid)
        identity2 = factory.create(vid)
        assert identity1.device.brand == identity2.device.brand
        assert identity1.device.model == identity2.device.model
        assert identity1.device.config_label == identity2.device.config_label

    def test_same_vid_produces_identical_chrome_version(self, factory):
        """同一 VID 多次调用选择同一 Chrome 版本"""
        vid = "test-deterministic-003"
        identity1 = factory.create(vid)
        identity2 = factory.create(vid)
        assert identity1.chrome_version == identity2.chrome_version
        assert identity1.impersonate_key == identity2.impersonate_key

    def test_same_vid_produces_identical_all_signals(self, factory):
        """同一 VID 多次调用产生完全相同的所有信号"""
        vid = "test-deterministic-004"
        identity1 = factory.create(vid)
        identity2 = factory.create(vid)
        assert identity1.canvas_hash == identity2.canvas_hash
        assert identity1.audio_fingerprint == identity2.audio_fingerprint
        assert identity1.webgl_hash == identity2.webgl_hash
        assert identity1.font_hash == identity2.font_hash
        assert identity1.session_id == identity2.session_id

    def test_different_vid_produces_different_hash(self, factory):
        """不同 VID 产生不同的 fingerprint_hash"""
        identity1 = factory.create("vid-aaa-111-xxx")
        identity2 = factory.create("vid-bbb-222-yyy")
        assert identity1.fingerprint_hash != identity2.fingerprint_hash


class TestFingerprintHashFormat:
    """fingerprint_hash 格式校验"""

    def test_hash_is_32_hex_chars(self, sample_identity):
        """fingerprint_hash 应为 32 字符十六进制字符串 (128-bit MurmurHash3)"""
        assert len(sample_identity.fingerprint_hash) == 32
        assert re.match(r'^[0-9a-f]{32}$', sample_identity.fingerprint_hash)

    def test_canvas_hash_is_32_hex_chars(self, sample_identity):
        """canvas_hash 应为 32 字符十六进制字符串"""
        assert len(sample_identity.canvas_hash) == 32
        assert re.match(r'^[0-9a-f]{32}$', sample_identity.canvas_hash)

    def test_webgl_hash_is_32_hex_chars(self, sample_identity):
        """webgl_hash 应为 32 字符十六进制字符串"""
        assert len(sample_identity.webgl_hash) == 32
        assert re.match(r'^[0-9a-f]{32}$', sample_identity.webgl_hash)

    def test_all_devices_produce_valid_hashes(self, factory, all_devices):
        """所有 36 个设备都能生成有效的 32 字符哈希"""
        for i, dev in enumerate(all_devices):
            identity = factory.create(f"test-device-{i:03d}")
            assert len(identity.fingerprint_hash) == 32, (
                f"{dev.brand} {dev.model} [{dev.config_label}] "
                f"hash length = {len(identity.fingerprint_hash)}"
            )
            assert re.match(r'^[0-9a-f]{32}$', identity.fingerprint_hash)


class TestSignalConsistency:
    """信号自洽性: UA ↔ platform ↔ sec-ch-ua ↔ WebGL 等"""

    def test_windows_device_ua_contains_windows(self, factory):
        """Windows 设备的 UA 应包含 'Windows NT'"""
        for i in range(5):
            identity = factory.create(f"test-win-{i}", brand="dell")
            assert "Windows NT" in identity.user_agent
            assert identity.platform == "Win32"

    def test_macos_device_ua_contains_mac(self, factory):
        """macOS 设备的 UA 应包含 'Macintosh'"""
        for i in range(5):
            identity = factory.create(f"test-mac-{i}", brand="apple")
            assert "Macintosh" in identity.user_agent
            assert identity.platform == "MacIntel"

    def test_chrome_version_in_user_agent(self, sample_identity):
        """Chrome 版本号应出现在 User-Agent 中"""
        assert sample_identity.chrome_version in sample_identity.user_agent

    def test_sec_ch_ua_matches_chrome_major(self, sample_identity):
        """sec-ch-ua 应包含正确的 Chrome 主版本号"""
        major = sample_identity.chrome_version.split(".")[0]
        assert f'v="{major}"' in sample_identity.sec_ch_ua

    def test_color_depth_matches_os(self, all_devices):
        """Windows=32, macOS=30 (直接检查设备目录)"""
        for dev in all_devices:
            if dev.os_family == "windows":
                assert dev.color_depth == 32, f"{dev.model} color_depth != 32"
            elif dev.os_family == "macos":
                assert dev.color_depth == 30, f"{dev.model} color_depth != 30"


class TestAvailScreenDimensions:
    """可用屏幕尺寸 (dth 信号)"""

    def test_avail_width_equals_screen_width_by_default(self, all_devices):
        """默认情况下 avail_width = screen_width"""
        for dev in all_devices:
            assert dev.get_avail_width() == dev.screen_width

    def test_windows_avail_height_subtracts_taskbar(self, devices_by_brand):
        """Windows: avail_height = screen_height - 48 (任务栏)"""
        for dev in devices_by_brand.get("dell", []):
            expected = dev.screen_height - 48
            assert dev.get_avail_height() == expected, (
                f"{dev.model} avail_height {dev.get_avail_height()} != {expected}"
            )

    def test_macos_avail_height_subtracts_menubar(self, devices_by_brand):
        """macOS: avail_height = screen_height - 25 (菜单栏)"""
        for dev in devices_by_brand.get("apple", []):
            expected = dev.screen_height - 25
            assert dev.get_avail_height() == expected, (
                f"{dev.model} avail_height {dev.get_avail_height()} != {expected}"
            )


class TestInputValidation:
    """输入验证"""

    def test_empty_vid_raises_value_error(self, factory):
        """空 VID 应抛出 ValueError"""
        with pytest.raises(ValueError, match="不能为空"):
            factory.create("")

    def test_brand_filter(self, factory):
        """品牌过滤应只返回该品牌的设备"""
        identity = factory.create("test-brand-filter", brand="dell")
        assert identity.device.brand == "Dell"

    def test_invalid_brand_falls_back(self, factory):
        """无效品牌应回退到全部设备"""
        identity = factory.create("test-invalid-brand", brand="nonexistent")
        assert identity.device is not None
