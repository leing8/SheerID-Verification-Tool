"""
指纹生成包
生成各类浏览器指纹用于反检测

模块结构：
- base: 基础工具函数（种子随机数、哈希生成）
- device_profile: 统一设备档案（确保配置一致性）
- canvas: Canvas 渲染指纹
- webgl: WebGL GPU 指纹
- audio: AudioContext 音频指纹
- browser: 浏览器相关指纹（字体、插件、WebRTC、Navigator）
"""

import hashlib
from typing import Optional

from .audio import get_audio_fingerprint
from .base import (
    get_seeded_random,
    generate_session_id,
    generate_deterministic_hash,
)
from .browser import (
    get_fonts_fingerprint,
    get_plugins_fingerprint,
    get_webrtc_fingerprint,
    get_navigator_fingerprint,
    get_screen_fingerprint,
    get_timezone_fingerprint,
)
from .canvas import get_canvas_fingerprint
from .device_profile import (
    DeviceProfile,
    GPUProfile,
    GPU_PROFILES,
    DEVICE_TEMPLATES,
    US_TIMEZONES,
    US_LANGUAGES,
    generate_device_profile,
)
from .webgl import get_webgl_fingerprint


def _compute_fingerprint_hash(
    seed: str,
    device: DeviceProfile,
    canvas_hash: str,
    webgl_hash: str,
    audio_hash: str,
) -> str:
    """
    计算指纹哈希（内部函数，避免重复代码）
    """
    components = [
        seed,
        f"{device.screen_width}x{device.screen_height}",
        str(device.timezone_offset),
        device.language,
        device.platform,
        device.gpu.vendor,
        str(device.cpu_cores),
        str(device.device_memory),
        str(device.max_touch_points),
        generate_session_id(seed, "_session"),
        canvas_hash,
        webgl_hash,
        audio_hash,
    ]
    return hashlib.sha256("|".join(components).encode()).hexdigest()[:32]


def get_fingerprint(seed: str) -> str:
    """
    生成浏览器指纹哈希
    
    参数:
        seed: verificationId（必须），确保同一验证会话中指纹一致
    """
    device = generate_device_profile(seed, prefer_us=True)
    
    canvas_data = get_canvas_fingerprint(seed, device)
    webgl_data = get_webgl_fingerprint(seed, device)
    audio_data = get_audio_fingerprint(seed, device)

    return _compute_fingerprint_hash(
        seed, device,
        canvas_data["hash"], webgl_data["hash"], audio_data["hash"]
    )


def get_full_fingerprint(seed: str, os_type: Optional[str] = None) -> dict:
    """
    生成完整的浏览器指纹
    
    参数:
        seed: verificationId（必须）
        os_type: 操作系统类型，如为 None 则由 DeviceProfile 随机选择
    """
    device = generate_device_profile(seed, prefer_us=True, os_type=os_type)

    canvas_data = get_canvas_fingerprint(seed, device)
    webgl_data = get_webgl_fingerprint(seed, device)
    audio_data = get_audio_fingerprint(seed, device)

    fingerprint_hash = _compute_fingerprint_hash(
        seed, device,
        canvas_data["hash"], webgl_data["hash"], audio_data["hash"]
    )

    return {
        "hash": fingerprint_hash,
        # 渲染指纹
        "canvas": canvas_data,
        "webgl": webgl_data,
        "audio": audio_data,
        # 浏览器指纹
        "fonts": get_fonts_fingerprint(seed, device.os_type, device),
        "plugins": get_plugins_fingerprint(seed),
        "webrtc": get_webrtc_fingerprint(seed, device),
        "navigator": get_navigator_fingerprint(seed, device.os_type, device),
        "screen": get_screen_fingerprint(seed, device),
        "timezone": get_timezone_fingerprint(seed, device),
        # 设备档案属性
        "language": device.language,
        "languages": device.languages,
        "platform": device.platform,
        "cpuCores": device.cpu_cores,
        "memory": device.device_memory,
        "touchSupport": device.max_touch_points > 0,
        "sessionId": generate_session_id(seed, "_full_session"),
        "osType": device.os_type,
        "gpuVendor": device.gpu.vendor,
        "gpuRenderer": device.gpu.renderer,
    }


__all__ = [
    # 基础函数
    "get_seeded_random",
    "generate_session_id",
    "generate_deterministic_hash",
    # 设备档案
    "DeviceProfile",
    "GPUProfile",
    "GPU_PROFILES",
    "DEVICE_TEMPLATES",
    "US_TIMEZONES",
    "US_LANGUAGES",
    "generate_device_profile",
    # 渲染指纹
    "get_fingerprint",
    "get_canvas_fingerprint",
    "get_webgl_fingerprint",
    "get_audio_fingerprint",
    # 浏览器指纹
    "get_fonts_fingerprint",
    "get_plugins_fingerprint",
    "get_webrtc_fingerprint",
    "get_navigator_fingerprint",
    "get_screen_fingerprint",
    "get_timezone_fingerprint",
    # 完整指纹
    "get_full_fingerprint",
]
