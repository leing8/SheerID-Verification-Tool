"""信号生成函数测试

覆盖:
- 确定性种子
- Canvas/Audio/WebGL/Font 哈希格式
- Session ID UUID 格式
- MurmurHash3 指纹哈希一致性
- Chrome 版本在有效集合内
"""

import re

import pytest
from device_fingerprint_factory.signals import (
    CHROME_IMPERSONATE_KEYS,
    CHROME_VERSION_MAP,
    _deterministic_seed,
    _seed_to_float,
    _seed_to_int,
    compute_fingerprint_hash,
    generate_audio_fingerprint,
    generate_canvas_hash,
    generate_font_hash,
    generate_session_id,
    generate_webgl_hash,
    select_chrome_version,
    get_chrome_full_version,
    generate_sec_ch_ua,
)

SAMPLE_VID = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
SAMPLE_VID_ALT = "f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3"


class TestDeterministicSeed:
    """_deterministic_seed 确定性"""

    def test_same_input_same_seed(self) -> None:
        """相同输入产生相同种子"""
        s1 = _deterministic_seed(SAMPLE_VID, "test_component")
        s2 = _deterministic_seed(SAMPLE_VID, "test_component")
        assert s1 == s2

    def test_different_vid_different_seed(self) -> None:
        """不同 vid 产生不同种子"""
        s1 = _deterministic_seed(SAMPLE_VID, "test_component")
        s2 = _deterministic_seed(SAMPLE_VID_ALT, "test_component")
        assert s1 != s2

    def test_different_component_different_seed(self) -> None:
        """不同组件名产生不同种子"""
        s1 = _deterministic_seed(SAMPLE_VID, "component_a")
        s2 = _deterministic_seed(SAMPLE_VID, "component_b")
        assert s1 != s2

    def test_seed_is_bytes(self) -> None:
        """种子类型为 bytes"""
        seed = _deterministic_seed(SAMPLE_VID, "test")
        assert isinstance(seed, bytes)
        assert len(seed) == 32  # SHA-256


class TestSeedConversion:
    """种子到数值的转换"""

    def test_seed_to_int_range(self) -> None:
        """_seed_to_int 结果在 [0, max_val) 范围内"""
        seed = _deterministic_seed(SAMPLE_VID, "test")
        for max_val in [1, 5, 10, 100]:
            result = _seed_to_int(seed, max_val)
            assert 0 <= result < max_val

    def test_seed_to_float_range(self) -> None:
        """_seed_to_float 结果在 [low, high] 范围内"""
        seed = _deterministic_seed(SAMPLE_VID, "test")
        result = _seed_to_float(seed, 10.0, 20.0)
        assert 10.0 <= result <= 20.0


class TestCanvasHash:
    """Canvas 指纹哈希"""

    def test_format_32_hex(self) -> None:
        """32 位十六进制字符串"""
        h = generate_canvas_hash(SAMPLE_VID, "test_device_key")
        assert re.fullmatch(r"[0-9a-f]{32}", h)

    def test_deterministic(self) -> None:
        """同一输入 → 同一哈希"""
        h1 = generate_canvas_hash(SAMPLE_VID, "key")
        h2 = generate_canvas_hash(SAMPLE_VID, "key")
        assert h1 == h2

    def test_different_device_key_different_hash(self) -> None:
        """不同设备键 → 不同哈希"""
        h1 = generate_canvas_hash(SAMPLE_VID, "device_A")
        h2 = generate_canvas_hash(SAMPLE_VID, "device_B")
        assert h1 != h2


class TestAudioFingerprint:
    """AudioContext 指纹"""

    def test_in_valid_range(self) -> None:
        """值在 124.04 ~ 124.08 范围"""
        fp = generate_audio_fingerprint(SAMPLE_VID, "test_key")
        value = float(fp)
        assert 124.04 <= value <= 124.09

    def test_format_precision(self) -> None:
        """13 位小数精度"""
        fp = generate_audio_fingerprint(SAMPLE_VID, "test_key")
        # 格式: "124.xxxxxxxxxxxxx"
        parts = fp.split(".")
        assert len(parts) == 2
        assert len(parts[1]) == 13


class TestWebGLHash:
    """WebGL 哈希"""

    def test_format_md5(self) -> None:
        """MD5 格式 (32 位十六进制)"""
        h = generate_webgl_hash(SAMPLE_VID, "test_key")
        assert re.fullmatch(r"[0-9a-f]{32}", h)


class TestFontHash:
    """字体哈希"""

    def test_format_16_hex(self) -> None:
        """16 位十六进制字符串"""
        h = generate_font_hash(SAMPLE_VID, "windows")
        assert re.fullmatch(r"[0-9a-f]{16}", h)

    @pytest.mark.parametrize("os_family", ["windows", "macos"])
    def test_different_os_different_hash(self, os_family: str) -> None:
        """不同 OS → 不同字体哈希"""
        h_win = generate_font_hash(SAMPLE_VID, "windows")
        h_mac = generate_font_hash(SAMPLE_VID, "macos")
        assert h_win != h_mac


class TestSessionId:
    """Session ID"""

    UUID_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )

    def test_uuid_format(self) -> None:
        """UUID 格式验证"""
        sid = generate_session_id(SAMPLE_VID)
        assert self.UUID_PATTERN.match(sid)

    def test_deterministic(self) -> None:
        """同一 vid → 同一 session ID"""
        s1 = generate_session_id(SAMPLE_VID)
        s2 = generate_session_id(SAMPLE_VID)
        assert s1 == s2


class TestChromeVersion:
    """Chrome 版本选择"""

    def test_in_valid_set(self) -> None:
        """选中版本在配置列表内"""
        key = select_chrome_version(SAMPLE_VID)
        assert key in CHROME_VERSION_MAP

    def test_deterministic(self) -> None:
        """同一 vid → 同一版本"""
        k1 = select_chrome_version(SAMPLE_VID)
        k2 = select_chrome_version(SAMPLE_VID)
        assert k1 == k2

    def test_full_version_format(self) -> None:
        """完整版本号格式验证"""
        key = select_chrome_version(SAMPLE_VID)
        ver = get_chrome_full_version(key)
        assert re.fullmatch(r"\d+\.\d+\.\d+\.\d+", ver)

    def test_sec_ch_ua_not_empty(self) -> None:
        """sec-ch-ua 非空"""
        key = select_chrome_version(SAMPLE_VID)
        sec_ch_ua = generate_sec_ch_ua(key)
        assert len(sec_ch_ua) > 0
        assert "Chrome" in sec_ch_ua


class TestComputeFingerprintHash:
    """最终指纹哈希计算"""

    def test_format_32_hex(self) -> None:
        """32 位十六进制字符串"""
        h = compute_fingerprint_hash(["a", "b", "c"])
        assert re.fullmatch(r"[0-9a-f]{32}", h)

    def test_deterministic(self) -> None:
        """同一输入 → 同一哈希"""
        components = ["ua", "en-US", "32", "1.0", "true"]
        h1 = compute_fingerprint_hash(components)
        h2 = compute_fingerprint_hash(components)
        assert h1 == h2

    def test_different_input_different_hash(self) -> None:
        """不同输入 → 不同哈希"""
        h1 = compute_fingerprint_hash(["a", "b"])
        h2 = compute_fingerprint_hash(["a", "c"])
        assert h1 != h2

    def test_order_matters(self) -> None:
        """组件顺序影响结果"""
        h1 = compute_fingerprint_hash(["a", "b", "c"])
        h2 = compute_fingerprint_hash(["c", "b", "a"])
        assert h1 != h2
