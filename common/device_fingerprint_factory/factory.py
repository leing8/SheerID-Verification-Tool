"""
DeviceIdentityFactory — 确定性设备身份工厂 (仅桌面端)

传入 verificationId 后确定性生成完整的桌面设备身份。
同一 verificationId → 始终返回相同设备和指纹。
不同 verificationId 即使选中同一设备 → 混淆产生差异。
"""

from typing import Optional

from .catalog import (
    ALL_DEVICES,
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
    get_chrome_full_version,
    select_chrome_version,
)
from .us_timezones import select_timezone


class DeviceIdentityFactory:
    """
    确定性桌面设备身份工厂。

    用法:
        factory = DeviceIdentityFactory()
        identity = factory.create("abc123def456")
        headers = identity.get_headers(for_sheerid=True)
        fingerprint = identity.fingerprint_hash
    """

    def create(
        self,
        verification_id: str,
        brand: Optional[str] = None,
    ) -> DeviceIdentity:
        """
        创建绑定到 verificationId 的桌面设备身份。

        Args:
            verification_id: 唯一验证 ID
            brand: 可选品牌过滤 ("dell", "lenovo", "apple")

        Returns:
            DeviceIdentity: 不可变的设备身份实例
        """
        if not verification_id:
            raise ValueError("verification_id 不能为空")

        # 1. 确定性选择桌面设备
        device = self._select_device(verification_id, brand)

        # 2. 确定性选择时区 (自动处理 DST)
        timezone = select_timezone(verification_id)

        # 3. 确定性选择 Chrome 版本 (返回 curl_cffi impersonate 键)
        impersonate_key = select_chrome_version(verification_id)
        chrome_ver = get_chrome_full_version(impersonate_key)

        # 4. 生成设备唯一键 (用于信号混淆)
        device_key = f"{device.brand}:{device.model}:{device.config_label}"

        # 5. 生成各项信号
        canvas_hash = generate_canvas_hash(verification_id, device_key)
        audio_fp = generate_audio_fingerprint(verification_id, device_key)
        webgl_hash = generate_webgl_hash(verification_id, device_key)
        font_hash = generate_font_hash(verification_id, device.os_family)
        session_id = generate_session_id(verification_id)
        sec_ch_ua = generate_sec_ch_ua(impersonate_key)

        # 6. 生成 User-Agent
        user_agent = device.ua_template.format(chrome_ver=chrome_ver)

        # 7. 计算最终指纹哈希
        #    使用 MurmurHash3 x64_128 (seed=31), 分隔符 ~~~
        #    信号项与 SheerID learn.js GFPItems 对齐
        fingerprint_hash = compute_fingerprint_hash([
            user_agent,                                       # dtb: User-Agent
            "en-US",                                          # dtc: 语言
            str(device.color_depth),                          # dtd: 色深
            str(device.pixel_ratio),                          # dte: 设备像素比
            str(device.cpu_cores),                            # dtf: 硬件并发数
            str(device.screen_width),                         # dtg: 屏幕宽度
            str(device.screen_height),                        # dth: 屏幕高度
            str(timezone["offset"] * -60),                    # dti: 时区偏移 (分钟, 正值)
            device.platform,                                  # dtj: navigator.platform
            str(device.max_touch_points),                     # dtk: 触屏点数
            str(device.device_memory),                        # dtl: 设备内存
            device.webgl_vendor,                              # dtn: WebGL vendor
            device.webgl_renderer,                            # dto: WebGL renderer
            canvas_hash,                                      # dtr: Canvas 指纹哈希
            webgl_hash,                                       # dtt: WebGL 扩展哈希
            audio_fp,                                         # dtll: AudioContext 指纹
            font_hash,                                        # 字体哈希
        ])

        # 8. 构建不可变的 DeviceIdentity
        return DeviceIdentity(
            verification_id=verification_id,
            device=device,
            chrome_version=chrome_ver,
            impersonate_key=impersonate_key,
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
        brand: Optional[str],
    ) -> DeviceProfile:
        """确定性选择桌面设备"""
        if brand:
            brand_lower = brand.lower()
            candidates = DEVICES_BY_BRAND.get(brand_lower, ALL_DEVICES)
        else:
            candidates = ALL_DEVICES

        if not candidates:
            candidates = ALL_DEVICES

        # 确定性选择
        seed = _deterministic_seed(verification_id, "device_select")
        idx = _seed_to_int(seed, len(candidates))
        return candidates[idx]
