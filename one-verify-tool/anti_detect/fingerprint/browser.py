"""
浏览器相关指纹生成模块
包含字体、插件、WebRTC、Navigator 指纹
"""

from typing import List

from .base import get_seeded_random
from ..config import (
    RESOLUTIONS,
    TIMEZONES,
    LANGUAGES,
    COMMON_FONTS_WINDOWS,
    COMMON_FONTS_MAC,
    COMMON_PLUGINS,
    NAVIGATOR_PROPERTIES,
)


def get_fonts_fingerprint(seed: str, os_type: str = "windows") -> List[str]:
    """
    生成字体列表指纹
    
    参数:
        seed: verificationId（必须）
        os_type: 操作系统类型 ("windows", "macos", "linux")
    
    返回:
        检测到的字体列表（模拟）
    """
    rng = get_seeded_random(seed)

    # 根据操作系统选择字体库
    if os_type == "macos":
        base_fonts = COMMON_FONTS_MAC.copy()
    else:
        base_fonts = COMMON_FONTS_WINDOWS.copy()

    # 随机移除少量字体以增加多样性
    num_remove = rng.randint(0, 3)
    for _ in range(num_remove):
        if len(base_fonts) > 10:
            base_fonts.pop(rng.randint(0, len(base_fonts) - 1))

    return base_fonts


def get_plugins_fingerprint(seed: str) -> List[dict]:
    """
    生成插件列表指纹
    
    参数:
        seed: verificationId（必须）
    
    返回:
        检测到的插件列表（模拟）
    """
    rng = get_seeded_random(seed)

    # 现代 Chrome 通常只有 PDF 相关插件
    plugins = COMMON_PLUGINS.copy()

    # 随机选择 3-5 个插件
    num_plugins = rng.randint(3, min(5, len(plugins)))
    return rng.sample(plugins, num_plugins)


def get_webrtc_fingerprint(seed: str) -> dict:
    """
    生成 WebRTC 指纹数据
    
    参数:
        seed: verificationId（必须）
    
    返回:
        模拟的 WebRTC 信息
    """
    rng = get_seeded_random(seed)

    # 生成模拟的本地 IP（私网地址）
    local_ip = f"192.168.{rng.randint(0, 255)}.{rng.randint(1, 254)}"

    return {
        "localIP": local_ip,
        "publicIP": None,
        "stunEnabled": True,
        "turnEnabled": False,
    }


def get_navigator_fingerprint(seed: str, os_type: str = "windows") -> dict:
    """
    生成 Navigator 对象指纹
    
    参数:
        seed: verificationId（必须）
        os_type: 操作系统类型 ("windows", "macos", "linux")
    
    返回:
        模拟的 navigator 属性
    """
    rng = get_seeded_random(seed)

    nav_props = NAVIGATOR_PROPERTIES.get(os_type, NAVIGATOR_PROPERTIES["windows"])

    return {
        "platform": nav_props["platform"],
        "appVersion": nav_props["appVersion"],
        "vendor": nav_props["vendor"],
        "maxTouchPoints": nav_props["maxTouchPoints"],
        "hardwareConcurrency": rng.choice(nav_props["hardwareConcurrency"]),
        "deviceMemory": rng.choice(nav_props["deviceMemory"]),
        "cookieEnabled": True,
        "doNotTrack": rng.choice([None, "1"]),
        "language": rng.choice(LANGUAGES).split(",")[0],
        "languages": rng.choice(LANGUAGES).split(";")[0].split(","),
    }


def get_screen_fingerprint(seed: str) -> dict:
    """
    生成屏幕指纹数据
    
    参数:
        seed: verificationId（必须）
    
    返回:
        模拟的屏幕信息
    """
    rng = get_seeded_random(seed)

    resolution = rng.choice(RESOLUTIONS)
    width, height = resolution.split("x")

    return {
        "width": int(width),
        "height": int(height),
        "colorDepth": rng.choice([24, 32]),
        "pixelRatio": rng.choice([1, 1.25, 1.5, 2]),
    }


def get_timezone_fingerprint(seed: str) -> int:
    """
    生成时区指纹
    
    参数:
        seed: verificationId（必须）
    
    返回:
        时区偏移量（分钟）
    """
    rng = get_seeded_random(seed)
    return rng.choice(TIMEZONES)
