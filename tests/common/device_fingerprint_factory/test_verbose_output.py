"""
test_verbose_output.py — 设备指纹完整信息输出测试

运行时使用 -s 参数查看完整输出:
    pytest tests/common/device_fingerprint_factory/test_verbose_output.py -v -s
    pytest tests/common/device_fingerprint_factory/test_verbose_output.py -v -s --vid=your-id
"""

import pytest


class TestDeviceFingerprintVerboseOutput:
    """输出完整设备指纹信息，便于人工检查"""

    def test_full_fingerprint_output(self, factory, sample_vid):
        """输出完整的设备指纹信息"""
        identity = factory.create(sample_vid)

        print("\n" + "=" * 72)
        print(f"  设备指纹完整信息 (VID: {sample_vid})")
        print("=" * 72)

        # 基本信息
        print(f"\n── 基本信息 ──")
        print(f"  Verification ID     : {identity.verification_id}")
        print(f"  Fingerprint Hash    : {identity.fingerprint_hash}")

        # 设备信息
        dev = identity.device
        print(f"\n── 设备信息 ──")
        print(f"  Brand               : {dev.brand}")
        print(f"  Model               : {dev.model}")
        print(f"  Config Label        : {dev.config_label}")
        print(f"  OS Family           : {dev.os_family}")
        print(f"  Platform            : {identity.platform}")

        # 屏幕信息
        print(f"\n── 屏幕信息 ──")
        print(f"  Screen              : {identity.screen_width}x{identity.screen_height}")
        print(f"  Avail Screen        : {dev.get_avail_width()}x{dev.get_avail_height()}")
        print(f"  Color Depth         : {identity.color_depth}")
        print(f"  Pixel Ratio         : {identity.pixel_ratio}")

        # 硬件信息
        print(f"\n── 硬件信息 ──")
        print(f"  CPU Cores           : {identity.cpu_cores}")
        print(f"  Device Memory       : {identity.device_memory} GB")
        print(f"  Max Touch Points    : {identity.max_touch_points}")

        # Chrome / 浏览器
        print(f"\n── 浏览器信息 ──")
        print(f"  Chrome Version      : {identity.chrome_version}")
        print(f"  Impersonate Key     : {identity.impersonate_key}")
        print(f"  Sec-CH-UA           : {identity.sec_ch_ua}")
        print(f"  Sec-CH-UA-Platform  : {identity.sec_ch_ua_platform}")
        print(f"  Language            : {identity.language}")

        # 时区
        print(f"\n── 时区信息 ──")
        print(f"  Timezone Name       : {identity.timezone_name}")
        print(f"  Timezone Offset     : UTC{identity.timezone_offset:+d}")

        # 信号哈希
        print(f"\n── 指纹信号 ──")
        print(f"  Canvas Hash         : {identity.canvas_hash}")
        print(f"  WebGL Vendor        : {identity.webgl_vendor}")
        print(f"  WebGL Renderer      : {identity.webgl_renderer}")
        print(f"  WebGL Hash          : {identity.webgl_hash}")
        print(f"  Audio Fingerprint   : {identity.audio_fingerprint}")
        print(f"  Font Hash           : {identity.font_hash}")
        print(f"  Session ID          : {identity.session_id}")

        # User-Agent
        print(f"\n── User-Agent ──")
        print(f"  {identity.user_agent}")

        # HTTP 请求头
        headers = identity.get_headers(for_sheerid=True)
        print(f"\n── HTTP 请求头 ({len(headers)} 项) ──")
        for key, value in headers.items():
            display_val = value if len(value) <= 100 else value[:100] + "..."
            print(f"  {key}: {display_val}")

        print("\n" + "=" * 72)

    def test_multiple_devices_summary(self, factory, sample_vid):
        """输出基于当前 VID 衍生的 10 个设备摘要对比"""
        print("\n" + "=" * 72)
        print(f"  多 VID 设备指纹摘要对比 (base: {sample_vid})")
        print("=" * 72)
        print(f"\n  {'VID':<40} {'Device':<35} {'Screen':<14} {'FP Hash'}")
        print(f"  {'-'*40} {'-'*35} {'-'*14} {'-'*32}")

        for i in range(10):
            vid = f"{sample_vid}-{i}"
            identity = factory.create(vid)
            dev = identity.device
            device_name = f"{dev.brand} {dev.model}"
            screen = f"{identity.screen_width}x{identity.screen_height}"
            vid_display = vid if len(vid) <= 38 else vid[:35] + "..."
            print(
                f"  {vid_display:<40} {device_name:<35} {screen:<14} "
                f"{identity.fingerprint_hash}"
            )

        print()
