"""
反检测模块配置常量
包含浏览器版本、User-Agent、平台等配置
"""

# ============ Chrome 模拟版本 ============
# 这些是 curl_cffi 可以模拟的 Chrome 版本
# 2026年1月更新 - 使用最新稳定版本
CHROME_VERSIONS = [
    "chrome131",  # Chrome 131（稳定版）
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

# 多浏览器类型轮换（curl_cffi 支持这些）
IMPERSONATE_OPTIONS = {
    "chrome": ["chrome131", "chrome130", "chrome124", "chrome120"],
    "edge": ["edge131", "edge127", "edge101"],
    "safari": ["safari18", "safari17_2_ios", "safari17_0"],
}

# 默认模拟 - 使用最新稳定版
DEFAULT_IMPERSONATE = "chrome131"

# ============ User-Agent 列表 ============
# 真实浏览器 User-Agent（2026年1月更新）
# 重要: 这些必须与我们模拟的 Chrome 版本匹配
USER_AGENTS_CHROME = [
    # Chrome 131 Windows（匹配 chrome131 模拟）
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Chrome 131 Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Chrome 130 Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Chrome 130 Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Chrome 131 Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

# 向后兼容别名
USER_AGENTS = USER_AGENTS_CHROME

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
TIMEZONES = [-8, -7, -6, -5, -4, -3, 0, 1, 2, 3, 5, 8, 9, 10]

# ============ 语言 ============
LANGUAGES = [
    "en-US,en;q=0.9",
    "en-US,en;q=0.9,es;q=0.8",
    "en-GB,en;q=0.9",
    "en-CA,en;q=0.9",
    "en-AU,en;q=0.9",
]

# ============ 平台常量 ============
# 用于指纹生成的平台标识符
PLATFORMS = ("Win32", "MacIntel", "Linux x86_64")

# ============ WebGL 厂商 ============
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

# ============ User-Agent 与平台映射 ============
# 确保 UA 与 sec-ch-ua-platform 一致性
UA_PLATFORM_MAP = {
    # Windows UA -> Windows 平台
    "Windows NT 10.0": (
        "Windows",
        '"Windows"',
        '"Chromium";v="131", "Google Chrome";v="131", "Not_A Brand";v="24"',
    ),
    # macOS UA -> macOS 平台
    "Macintosh": (
        "macOS",
        '"macOS"',
        '"Chromium";v="131", "Google Chrome";v="131", "Not_A Brand";v="24"',
    ),
    # Linux UA -> Linux 平台
    "X11; Linux": (
        "Linux",
        '"Linux"',
        '"Chromium";v="131", "Google Chrome";v="131", "Not_A Brand";v="24"',
    ),
}

# Chrome 版本对应的 sec-ch-ua 值
CHROME_VERSION_SEC_CH_UA = {
    "131": '"Chromium";v="131", "Google Chrome";v="131", "Not_A Brand";v="24"',
    "130": '"Chromium";v="130", "Google Chrome";v="130", "Not_A Brand";v="24"',
    "129": '"Chromium";v="129", "Google Chrome";v="129", "Not_A Brand";v="24"',
    "124": '"Chromium";v="124", "Google Chrome";v="124", "Not_A Brand";v="24"',
    "120": '"Chromium";v="120", "Google Chrome";v="120", "Not_A Brand";v="24"',
}

# ============ 常见字体列表 ============
# 用于更真实的指纹生成
COMMON_FONTS_WINDOWS = [
    "Arial", "Arial Black", "Calibri", "Cambria", "Candara", "Comic Sans MS",
    "Consolas", "Constantia", "Corbel", "Courier New", "Georgia", "Impact",
    "Lucida Console", "Lucida Sans Unicode", "Microsoft Sans Serif", "Palatino Linotype",
    "Segoe UI", "Tahoma", "Times New Roman", "Trebuchet MS", "Verdana",
]

COMMON_FONTS_MAC = [
    "Arial", "Arial Black", "Courier New", "Georgia", "Helvetica", "Helvetica Neue",
    "Impact", "Lucida Grande", "Monaco", "Palatino", "Times New Roman", "Trebuchet MS",
    "Verdana", "San Francisco", "SF Pro", "SF Mono",
]

# ============ 常见浏览器插件 ============
COMMON_PLUGINS = [
    {"name": "PDF Viewer", "filename": "internal-pdf-viewer"},
    {"name": "Chrome PDF Viewer", "filename": "internal-pdf-viewer"},
    {"name": "Chromium PDF Viewer", "filename": "internal-pdf-viewer"},
    {"name": "Microsoft Edge PDF Viewer", "filename": "internal-pdf-viewer"},
    {"name": "WebKit built-in PDF", "filename": "internal-pdf-viewer"},
]

# ============ Navigator 属性 ============
# 用于完整模拟浏览器 navigator 对象
NAVIGATOR_PROPERTIES = {
    "windows": {
        "platform": "Win32",
        "appVersion": "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "vendor": "Google Inc.",
        "maxTouchPoints": 0,
        "hardwareConcurrency": [4, 8, 12, 16],
        "deviceMemory": [4, 8, 16, 32],
    },
    "macos": {
        "platform": "MacIntel",
        "appVersion": "5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "vendor": "Google Inc.",
        "maxTouchPoints": 0,
        "hardwareConcurrency": [4, 8, 10, 12],
        "deviceMemory": [8, 16, 32],
    },
    "linux": {
        "platform": "Linux x86_64",
        "appVersion": "5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "vendor": "Google Inc.",
        "maxTouchPoints": 0,
        "hardwareConcurrency": [4, 8, 16],
        "deviceMemory": [4, 8, 16, 32],
    },
}
