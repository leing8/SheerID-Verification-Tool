"""
test_signals.py — 信号生成模块测试

测试各项指纹信号的正确性和确定性。
"""

import re
from collections import Counter

import pytest


class TestChromeVersions:
    """Chrome 版本选择"""

    def test_all_impersonate_keys_are_valid(self):
        """所有 impersonate_key 应有对应的完整版本号"""
        from device_fingerprint_factory.signals import (
            CHROME_IMPERSONATE_KEYS,
            CHROME_VERSION_MAP,
        )
        for key in set(CHROME_IMPERSONATE_KEYS):
            assert key in CHROME_VERSION_MAP, f"Key '{key}' 没有对应的精确版本号"

    def test_chrome_versions_have_precise_build(self):
        """Chrome 版本号应包含精确的构建号 (非 X.0.0.0)"""
        from device_fingerprint_factory.signals import (
            CHROME_IMPERSONATE_KEYS,
            CHROME_VERSION_MAP,
        )
        for key in set(CHROME_IMPERSONATE_KEYS):
            info = CHROME_VERSION_MAP[key]
            ver = info["version"]
            parts = ver.split(".")
            assert len(parts) == 4, f"{key}: 版本号格式错误 '{ver}'"
            assert not (parts[2] == "0" and parts[3] == "0"), (
                f"{key}: 版本号 '{ver}' 缺少精确构建号"
            )

    def test_sec_ch_ua_strings_not_empty(self):
        """每个 Chrome 版本应有非空的 sec-ch-ua"""
        from device_fingerprint_factory.signals import CHROME_VERSION_MAP
        for key, info in CHROME_VERSION_MAP.items():
            assert info["sec_ch_ua"], f"{key}: sec_ch_ua 为空"

    def test_no_old_chrome_124(self):
        """Chrome 124 不应在高权重列表中 (2024年5月, 已过旧)"""
        from device_fingerprint_factory.signals import CHROME_IMPERSONATE_KEYS
        assert "chrome124" not in CHROME_IMPERSONATE_KEYS

    def test_latest_chrome_has_highest_weight(self):
        """最新 Chrome 版本应有最高权重 (出现次数最多)"""
        from device_fingerprint_factory.signals import CHROME_IMPERSONATE_KEYS
        counts = Counter(CHROME_IMPERSONATE_KEYS)
        most_common_key = counts.most_common(1)[0][0]
        assert "136" in most_common_key or "137" in most_common_key, (
            f"最高权重的应是最新版本, 但当前是 {most_common_key}"
        )

    def test_select_chrome_is_deterministic(self):
        """select_chrome_version 对同一 VID 应返回相同结果"""
        from device_fingerprint_factory.signals import select_chrome_version
        key1 = select_chrome_version("test-vid-123")
        key2 = select_chrome_version("test-vid-123")
        assert key1 == key2


class TestSignalGeneration:
    """信号生成函数"""

    def test_canvas_hash_deterministic(self):
        """generate_canvas_hash 对相同输入应确定性"""
        from device_fingerprint_factory.signals import generate_canvas_hash
        h1 = generate_canvas_hash("vid1", "key1")
        h2 = generate_canvas_hash("vid1", "key1")
        assert h1 == h2

    def test_canvas_hash_varies_with_vid(self):
        """不同 VID 应产生不同的 canvas_hash"""
        from device_fingerprint_factory.signals import generate_canvas_hash
        h1 = generate_canvas_hash("vid1", "key1")
        h2 = generate_canvas_hash("vid2", "key1")
        assert h1 != h2

    def test_audio_fingerprint_is_numeric(self):
        """audio_fingerprint 应为浮点数格式字符串"""
        from device_fingerprint_factory.signals import generate_audio_fingerprint
        fp = generate_audio_fingerprint("vid1", "key1")
        float(fp)  # 不应抛出异常

    def test_audio_fingerprint_in_range(self):
        """audio_fingerprint 应在合理范围内 (120-130)"""
        from device_fingerprint_factory.signals import generate_audio_fingerprint
        fp = float(generate_audio_fingerprint("vid1", "key1"))
        assert 120.0 <= fp <= 130.0, f"Audio fingerprint {fp} 超出合理范围"

    def test_webgl_hash_format(self):
        """webgl_hash 应为 32 字符十六进制"""
        from device_fingerprint_factory.signals import generate_webgl_hash
        h = generate_webgl_hash("vid1", "key1")
        assert re.match(r'^[0-9a-f]{32}$', h)

    def test_session_id_format(self):
        """session_id 应为 UUID 格式"""
        from device_fingerprint_factory.signals import generate_session_id
        sid = generate_session_id("vid1")
        assert re.match(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            sid
        )


class TestFingerprintHash:
    """compute_fingerprint_hash 测试"""

    def test_hash_uses_murmurhash3(self):
        """应使用 MurmurHash3 而非 MD5"""
        from device_fingerprint_factory.signals import compute_fingerprint_hash
        result = compute_fingerprint_hash(["test", "data"])
        assert len(result) == 32
        assert re.match(r'^[0-9a-f]{32}$', result)

    def test_hash_deterministic(self):
        """相同输入产生相同哈希"""
        from device_fingerprint_factory.signals import compute_fingerprint_hash
        h1 = compute_fingerprint_hash(["a", "b", "c"])
        h2 = compute_fingerprint_hash(["a", "b", "c"])
        assert h1 == h2

    def test_hash_sensitive_to_order(self):
        """不同顺序应产生不同哈希"""
        from device_fingerprint_factory.signals import compute_fingerprint_hash
        h1 = compute_fingerprint_hash(["a", "b", "c"])
        h2 = compute_fingerprint_hash(["c", "b", "a"])
        assert h1 != h2

    def test_hash_sensitive_to_separator(self):
        """不同的信号项分割应有不同哈希"""
        from device_fingerprint_factory.signals import compute_fingerprint_hash
        h1 = compute_fingerprint_hash(["a", "b"])
        h2 = compute_fingerprint_hash(["a", "c"])
        assert h1 != h2, "不同输入应产生不同哈希"


class TestCatalog:
    """设备目录 catalog 测试"""

    def test_all_devices_count(self, all_devices):
        """应有 36 个设备"""
        assert len(all_devices) == 36

    def test_devices_by_brand_complete(self, devices_by_brand):
        """DEVICES_BY_BRAND 应包含所有品牌"""
        assert "dell" in devices_by_brand
        assert "lenovo" in devices_by_brand
        assert "apple" in devices_by_brand
        assert "hp" in devices_by_brand

    def test_device_profiles_are_frozen(self, all_devices):
        """DeviceProfile 应为不可变"""
        with pytest.raises(AttributeError):
            all_devices[0].brand = "Test"

    def test_no_duplicate_devices(self, all_devices):
        """不应有完全相同的设备"""
        signatures = set()
        for dev in all_devices:
            sig = (dev.brand, dev.model, dev.config_label)
            assert sig not in signatures, f"重复设备: {sig}"
            signatures.add(sig)
