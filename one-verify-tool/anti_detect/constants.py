"""
反检测模块 - 浏览器数据常量

包含 Chrome 模拟版本、User-Agent 列表、屏幕分辨率、时区、
语言、平台信息、WebGL 厂商与渲染器等常量数据。
"""

# ============ Chrome 模拟版本 ============
# curl_cffi 可模拟的 Chrome 版本 (2026年1月更新)
CHROME_VERSIONS = [
    "chrome131",  # Chrome 131 (stable)
    "chrome130",  # Chrome 130
    "chrome124",  # Chrome 124
    "chrome123",  # Chrome 123
    "chrome120",  # Chrome 120
    "chrome119",  # Chrome 119
    "chrome116",  # Chrome 116
    "chrome110",  # Chrome 110
    "chrome107",  # Chrome 107
    "chrome104",  # Chrome 104
    "chrome101",  # Chrome 101
    "chrome100",  # Chrome 100
    "chrome99",  # Chrome 99
]

# 多浏览器轮换选项 (curl_cffi 支持)
IMPERSONATE_OPTIONS = {
    "chrome": ["chrome131", "chrome130", "chrome124", "chrome120"],
    "edge": ["edge131", "edge127", "edge101"],
    "safari": ["safari18", "safari17_2_ios", "safari17_0"],
}

# 默认模拟版本 - 使用最新稳定版
DEFAULT_IMPERSONATE = "chrome131"

# ============ User-Agent 列表 ============
# 真实浏览器 User-Agent (2026年1月更新)
# 重要: 必须与模拟的 Chrome 版本匹配
USER_AGENTS_CHROME = [
    # Chrome 131 Windows (匹配 chrome131 模拟)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Chrome 131 Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Chrome 130 Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Chrome 130 Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]

# 兼容旧版的 User-Agent 列表
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Edge Windows (基于 Chromium)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
]

# ============ 屏幕分辨率 ============
RESOLUTIONS = [
    "1920x1080",
    "1366x768",
    "1536x864",
    "1440x900",
    "1280x720",
    "2560x1440",
    "1600x900",
    "1680x1050",
    "1280x800",
    "1024x768",
]

# ============ 时区 ============
TIMEZONES = [-8, -7, -6, -5, -4, -3, 0, 1, 2, 3, 5.5, 8, 9, 10]

# ============ 语言 ============
LANGUAGES = [
    "en-US,en;q=0.9",
    "en-US,en;q=0.9,es;q=0.8",
    "en-GB,en;q=0.9",
    "en-CA,en;q=0.9",
    "en-AU,en;q=0.9",
]

# ============ 平台信息 ============
# 必须与 User-Agent 保持一致
PLATFORMS = [
    (
        "Windows",
        '"Windows"',
        '"Chromium";v="131", "Google Chrome";v="131", "Not_A Brand";v="24"',
    ),
    (
        "Windows",
        '"Windows"',
        '"Chromium";v="130", "Google Chrome";v="130", "Not_A Brand";v="24"',
    ),
    (
        "macOS",
        '"macOS"',
        '"Chromium";v="131", "Google Chrome";v="131", "Not_A Brand";v="24"',
    ),
    (
        "Linux",
        '"Linux"',
        '"Chromium";v="131", "Google Chrome";v="131", "Not_A Brand";v="24"',
    ),
]

# ============ WebGL 厂商与渲染器 ============
WEBGL_VENDORS = [
    "Google Inc. (NVIDIA)",
    "Google Inc. (Intel)",
    "Google Inc. (AMD)",
    "Google Inc. (Apple)",
]

WEBGL_RENDERERS = [
    "ANGLE (NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)",
    "ANGLE (Apple M1 Pro)",
]
