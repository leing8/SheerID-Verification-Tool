"""
浏览器相关指纹生成模块
包含字体、插件、WebRTC、Navigator 指纹
增强版：添加反自动化检测字段
"""

from typing import List, Optional

from .base import get_seeded_random
from .device_profile import DeviceProfile
from ..config import (
    LANGUAGES,
    COMMON_FONTS_WINDOWS,
    COMMON_FONTS_MAC,
    COMMON_PLUGINS,
    NAVIGATOR_PROPERTIES,
)


def get_fonts_fingerprint(seed: str, os_type: str = "windows", device_profile: Optional[DeviceProfile] = None) -> List[str]:
    """
    生成字体列表指纹
    
    参数:
        seed: verificationId（必须）
        os_type: 操作系统类型 ("windows", "macos", "linux")
        device_profile: 统一设备档案
    
    返回:
        检测到的字体列表（模拟）
    """
    rng = get_seeded_random(seed)
    
    # 如果提供了设备档案，使用其操作系统类型
    if device_profile is not None:
        os_type = device_profile.os_type

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


def get_webrtc_fingerprint(seed: str, device_profile: Optional[DeviceProfile] = None) -> dict:
    """
    生成 WebRTC 指纹数据
    
    参数:
        seed: verificationId（必须）
        device_profile: 统一设备档案
    
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


def get_navigator_fingerprint(seed: str, os_type: str = "windows", device_profile: Optional[DeviceProfile] = None) -> dict:
    """
    生成 Navigator 对象指纹（增强版）
    
    增加反自动化检测所需的关键字段
    
    参数:
        seed: verificationId（必须）
        os_type: 操作系统类型 ("windows", "macos", "linux")
        device_profile: 统一设备档案
    
    返回:
        模拟的 navigator 属性
    """
    rng = get_seeded_random(seed)
    
    # 如果提供了设备档案，使用其配置
    if device_profile is not None:
        os_type = device_profile.os_type
        cpu_cores = device_profile.cpu_cores
        device_memory = device_profile.device_memory
        max_touch_points = device_profile.max_touch_points
        language = device_profile.language
        languages = device_profile.languages
        do_not_track = device_profile.do_not_track
    else:
        nav_props = NAVIGATOR_PROPERTIES.get(os_type, NAVIGATOR_PROPERTIES["windows"])
        cpu_cores = rng.choice(nav_props["hardwareConcurrency"])
        device_memory = rng.choice(nav_props["deviceMemory"])
        max_touch_points = nav_props["maxTouchPoints"]
        language = rng.choice(LANGUAGES).split(",")[0]
        languages = rng.choice(LANGUAGES).split(";")[0].split(",")
        do_not_track = rng.choice([None, "1"])
    
    nav_props = NAVIGATOR_PROPERTIES.get(os_type, NAVIGATOR_PROPERTIES["windows"])
    is_macos = os_type == "macos"

    return {
        # 基础属性
        "platform": nav_props["platform"],
        "appVersion": nav_props["appVersion"],
        "vendor": nav_props["vendor"],
        "vendorSub": "",  # Chrome 始终返回空字符串
        
        # 硬件信息
        "hardwareConcurrency": cpu_cores,
        "deviceMemory": device_memory,
        "maxTouchPoints": max_touch_points,
        
        # 权限和设置
        "cookieEnabled": True,
        "doNotTrack": do_not_track,
        "pdfViewerEnabled": True,  # 现代 Chrome 默认启用
        
        # 语言
        "language": language,
        "languages": languages,
        
        # 🔑 关键反自动化检测字段
        "webdriver": False,  # 必须为 False，自动化工具通常为 True
        
        # 网络信息（NetworkInformation API）
        "connection": {
            "effectiveType": rng.choice(["4g", "4g", "4g", "3g"]),  # 大多数人是 4g
            "rtt": rng.randint(50, 150),
            "downlink": rng.uniform(5.0, 50.0),
            "saveData": False,
        },
        
        # 其他属性
        "userAgentData": {
            "brands": [
                {"brand": "Chromium", "version": "144"},
                {"brand": "Google Chrome", "version": "144"},
                {"brand": "Not A(Brand", "version": "24"},
            ],
            # 高熵 fullVersionList（与 headers sec-ch-ua-full-version-list 一致）
            "fullVersionList": [
                {"brand": "Chromium", "version": "144.0.6778.85"},
                {"brand": "Google Chrome", "version": "144.0.6778.85"},
                {"brand": "Not A(Brand", "version": "24.0.0.0"},
            ],
            "mobile": False,
            "platform": nav_props["platform"].replace("Intel", "").strip() if "Mac" in nav_props["platform"] else "Windows",
            "platformVersion": "15.0.0" if is_macos else "10.0.0",
            "architecture": "arm" if is_macos else "x86",
            "bitness": "64",
        },
    }


def get_screen_fingerprint(seed: str, device_profile: Optional[DeviceProfile] = None) -> dict:
    """
    生成屏幕指纹数据
    
    参数:
        seed: verificationId（必须）
        device_profile: 统一设备档案
    
    返回:
        模拟的屏幕信息
    """
    rng = get_seeded_random(seed)
    
    if device_profile is not None:
        width = device_profile.screen_width
        height = device_profile.screen_height
        color_depth = device_profile.color_depth
        pixel_ratio = device_profile.pixel_ratio
    else:
        from ..config import RESOLUTIONS
        resolution = rng.choice(RESOLUTIONS)
        width, height = map(int, resolution.split("x"))
        color_depth = rng.choice([24, 32])
        pixel_ratio = rng.choice([1, 1.25, 1.5, 2])

    return {
        "width": width,
        "height": height,
        "availWidth": width,
        "availHeight": height - rng.randint(30, 50),  # 减去任务栏高度
        "colorDepth": color_depth,
        "pixelDepth": color_depth,  # 现代浏览器中与 colorDepth 相同
        "pixelRatio": pixel_ratio,
    }


def get_timezone_fingerprint(seed: str, device_profile: Optional[DeviceProfile] = None) -> int:
    """
    生成时区指纹
    
    参数:
        seed: verificationId（必须）
        device_profile: 统一设备档案
    
    返回:
        时区偏移量（分钟）
    """
    rng = get_seeded_random(seed)
    
    if device_profile is not None:
        return device_profile.timezone_offset
    
    from ..config import TIMEZONES
    return rng.choice(TIMEZONES)
