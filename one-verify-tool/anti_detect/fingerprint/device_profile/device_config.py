"""
设备配置模板
按操作系统分类的典型设备配置和区域设置
"""

# ============ 设备配置模板 ============
# 按操作系统分类的典型设备配置

DEVICE_TEMPLATES = {
    "windows_gaming": {
        "os_type": "windows",
        "platform": "Win32",
        "gpu_options": ["rtx_4090", "rtx_4080", "rtx_4070_ti", "rtx_3080", "rtx_3070"],
        "cpu_cores_range": (8, 16),
        "memory_range": (16, 32),
        "resolutions": ["2560x1440", "1920x1080", "3840x2160"],
        "pixel_ratios": [1, 1.25],
    },
    "windows_mainstream": {
        "os_type": "windows",
        "platform": "Win32",
        "gpu_options": ["rtx_3060", "rtx_4060", "intel_uhd_770", "intel_iris_xe"],
        "cpu_cores_range": (4, 12),
        "memory_range": (8, 16),
        "resolutions": ["1920x1080", "1366x768", "1536x864"],
        "pixel_ratios": [1, 1.25, 1.5],
    },
    "windows_office": {
        "os_type": "windows",
        "platform": "Win32",
        "gpu_options": ["intel_uhd_630", "intel_iris_xe"],
        "cpu_cores_range": (4, 8),
        "memory_range": (8, 16),
        "resolutions": ["1920x1080", "1366x768"],
        "pixel_ratios": [1],
    },
    "macos_pro": {
        "os_type": "macos",
        "platform": "MacIntel",
        "gpu_options": ["apple_m3", "apple_m2"],
        "cpu_cores_range": (8, 12),
        "memory_range": (16, 32),
        "resolutions": ["2560x1440", "1920x1080"],
        "pixel_ratios": [2],
    },
    "macos_air": {
        "os_type": "macos",
        "platform": "MacIntel",
        "gpu_options": ["apple_m2", "apple_m1"],
        "cpu_cores_range": (8, 10),
        "memory_range": (8, 16),
        "resolutions": ["1440x900", "1680x1050"],
        "pixel_ratios": [2],
    },
    "linux_workstation": {
        "os_type": "linux",
        "platform": "Linux x86_64",
        "gpu_options": ["rtx_3080", "rtx_3070", "rtx_4060"],
        "cpu_cores_range": (8, 16),
        "memory_range": (16, 32),
        "resolutions": ["1920x1080", "2560x1440"],
        "pixel_ratios": [1],
    },
}

# ============ 美国地区配置 ============
# 针对美国大学验证优化

US_TIMEZONES = [
    -480,  # PST (太平洋标准时间) UTC-8
    -420,  # MST (山地标准时间) UTC-7
    -360,  # CST (中部标准时间) UTC-6
    -300,  # EST (东部标准时间) UTC-5
    -240,  # EDT (东部夏令时间) UTC-4
]

US_LANGUAGES = [
    "en-US",
    "en-US,en",
]
