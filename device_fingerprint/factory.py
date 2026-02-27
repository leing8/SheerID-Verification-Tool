"""
DeviceIdentityFactory — 确定性设备身份工厂

传入 verificationId 后确定性生成完整的设备身份。
同一 verificationId → 始终返回相同设备和指纹。
不同 verificationId 即使选中同一设备 → 混淆产生差异。
"""

from typing import Optional

from .catalog import (
    ALL_DESKTOP_DEVICES,
    ALL_DEVICES,
    ALL_MOBILE_DEVICES,
    DEVICES_BY_BRAND,
    DeviceProfile,
)
from .identity import DeviceIdentity
from .signals import (
    _deterministic_seed,
    _seed_to_int,
    compute_fingerprint_hash,
    generate_audio_fingerprint,
    generate_canvas_hash,
    generate_font_hash,
    generate_sec_ch_ua,
    generate_session_id,
    generate_webgl_hash,
    select_chrome_version,
)
from .us_timezones import US_MAINLAND_TIMEZONES


class DeviceIdentityFactory:
    """
    确定性设备身份工厂。

    用法:
        factory = DeviceIdentityFactory()
        identity = factory.create("abc123def456")
        headers = identity.get_headers(for_sheerid=True)
        fingerprint = identity.fingerprint_hash
    """

    def create(
        self,
        verification_id: str,
        device_type: str = "desktop",
        brand: Optional[str] = None,
    ) -> DeviceIdentity:
        """
        创建绑定到 verificationId 的设备身份。

        Args:
            verification_id: 唯一验证 ID
            device_type: "desktop" 或 "mobile"
            brand: 可选品牌过滤 ("dell", "lenovo", "apple", "samsung")

        Returns:
            DeviceIdentity: 不可变的设备身份实例
        """
        if not verification_id:
            raise ValueError("verification_id 不能为空")

        # 1. 确定性选择设备
        device = self._select_device(verification_id, device_type, brand)

        # 2. 确定性选择时区
        timezone = self._select_timezone(verification_id)

        # 3. 确定性选择 Chrome 版本
        chrome_ver = select_chrome_version(verification_id)

        # 4. 生成设备唯一键 (用于信号混淆)
        device_key = f"{device.brand}:{device.model}:{device.config_label}"

        # 5. 生成各项信号
        canvas_hash = generate_canvas_hash(verification_id, device_key)
        audio_fp = generate_audio_fingerprint(verification_id, device_key)
        webgl_hash = generate_webgl_hash(verification_id, device_key)
        font_hash = generate_font_hash(verification_id, device.os_family)
        session_id = generate_session_id(verification_id)
        sec_ch_ua = generate_sec_ch_ua(chrome_ver)

        # 6. 生成 User-Agent
        user_agent = device.ua_template.format(chrome_ver=chrome_ver)

        # 7. 计算最终指纹哈希 (15 项信号拼接)
        fingerprint_hash = compute_fingerprint_hash([
            device.platform,                              # 1. 平台
            f"{device.screen_width}x{device.screen_height}",  # 2-3. 屏幕
            str(device.color_depth),                       # 4. 色深
            str(device.pixel_ratio),                       # 5. 像素比
            str(timezone["offset"]),                        # 6. 时区
            "en-US",                                       # 7. 语言
            str(device.cpu_cores),                          # 8. CPU
            str(device.device_memory),                      # 9. 内存
            str(device.max_touch_points),                   # 10. 触屏
            canvas_hash,                                    # 11. Canvas
            device.webgl_vendor,                            # 12. WebGL vendor
            device.webgl_renderer,                          # 13. WebGL renderer
            audio_fp,                                       # 14. Audio
            session_id,                                     # 15. 会话
        ])

        # 8. 构建不可变的 DeviceIdentity
        return DeviceIdentity(
            verification_id=verification_id,
            device=device,
            chrome_version=chrome_ver,
            timezone_name=timezone["name"],
            timezone_offset=timezone["offset"],
            canvas_hash=canvas_hash,
            webgl_vendor=device.webgl_vendor,
            webgl_renderer=device.webgl_renderer,
            audio_fingerprint=audio_fp,
            screen_width=device.screen_width,
            screen_height=device.screen_height,
            color_depth=device.color_depth,
            pixel_ratio=device.pixel_ratio,
            language="en-US",
            platform=device.platform,
            cpu_cores=device.cpu_cores,
            device_memory=device.device_memory,
            max_touch_points=device.max_touch_points,
            session_id=session_id,
            webgl_hash=webgl_hash,
            font_hash=font_hash,
            fingerprint_hash=fingerprint_hash,
            user_agent=user_agent,
            sec_ch_ua=sec_ch_ua,
            sec_ch_ua_platform=device.sec_ch_ua_platform,
        )

    def _select_device(
        self,
        verification_id: str,
        device_type: str,
        brand: Optional[str],
    ) -> DeviceProfile:
        """确定性选择设备"""
        # 确定候选设备集
        if brand:
            brand_lower = brand.lower()
            # 品牌映射: "iphone" → "apple" 的移动设备
            if brand_lower == "iphone":
                candidates = [
                    d for d in DEVICES_BY_BRAND.get("apple", [])
                    if d.os_family == "ios"
                ]
            elif brand_lower in DEVICES_BY_BRAND:
                candidates = DEVICES_BY_BRAND[brand_lower]
                if device_type == "desktop":
                    candidates = [d for d in candidates if d.device_type == "desktop"]
                elif device_type == "mobile":
                    candidates = [d for d in candidates if d.device_type == "mobile"]
            else:
                candidates = ALL_DESKTOP_DEVICES if device_type == "desktop" else ALL_MOBILE_DEVICES
        else:
            if device_type == "mobile":
                candidates = ALL_MOBILE_DEVICES
            elif device_type == "desktop":
                candidates = ALL_DESKTOP_DEVICES
            else:
                candidates = ALL_DEVICES

        if not candidates:
            candidates = ALL_DESKTOP_DEVICES

        # 确定性选择
        seed = _deterministic_seed(verification_id, "device_select")
        idx = _seed_to_int(seed, len(candidates))
        return candidates[idx]

    def _select_timezone(self, verification_id: str) -> dict:
        """确定性选择美国大陆时区"""
        seed = _deterministic_seed(verification_id, "timezone_select")
        idx = _seed_to_int(seed, len(US_MAINLAND_TIMEZONES))
        return US_MAINLAND_TIMEZONES[idx]
