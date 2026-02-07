"""
反检测模块配置常量
包含浏览器版本、User-Agent、平台等配置
"""

# ============ Chrome 模拟版本 ============
# 这些是 curl_cffi 可以模拟的 Chrome 版本
# 2026年2月更新 - 使用最新稳定版本
CHROME_VERSIONS = [
    "chrome131",  # Chrome 131（curl_cffi 最新支持版本）
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
# 真实浏览器 User-Agent（2026年2月更新）
# 注意: curl_cffi 最新支持 chrome131，因此 User-Agent 使用 Chrome 131 版本
# 但 sec-ch-ua 可以声称更高版本以匹配真实浏览器行为
USER_AGENTS_CHROME = [
    # Chrome 144 Windows（当前最新稳定版 2026年2月）
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    # Chrome 144 Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    # Chrome 144 Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    # Chrome 143 Windows（备用上一版本）
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    # Chrome 143 Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
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
# 2026年2月更新 - 使用最新显卡信息
WEBGL_VENDORS = [
    "Google Inc. (NVIDIA)",
    "Google Inc. (Intel)",
    "Google Inc. (AMD)",
    "Google Inc. (Apple)",
]

# WebGL 渲染器列表 - 2026年2月更新
# 格式: ANGLE (厂商, GPU型号 (设备ID) Direct3D11 vs_5_0 ps_5_0, D3D11)
WEBGL_RENDERERS = [
    # NVIDIA RTX 40 系列（最新一代）
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 4090 (0x00002684) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 4080 SUPER (0x00002702) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 4080 (0x00002704) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Ti SUPER (0x00002705) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Ti (0x00002782) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 (0x00002786) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Ti (0x00002803) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 (0x00002882) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    # NVIDIA RTX 30 系列（主流使用）
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 3090 (0x00002204) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Ti (0x00002208) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 (0x00002206) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Ti (0x00002482) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 (0x00002484) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Ti (0x00002486) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 (0x00002503) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    # Intel 集成显卡（常见笔记本配置）
    "ANGLE (Intel, Intel(R) UHD Graphics 770 (0x00004680) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (Intel, Intel(R) UHD Graphics 730 (0x00004692) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (Intel, Intel(R) Iris Xe Graphics (0x00009A49) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (Intel, Intel(R) UHD Graphics 630 (0x00003E92) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    # AMD 显卡
    "ANGLE (AMD, AMD Radeon RX 7900 XTX (0x0000744C) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (AMD, AMD Radeon RX 7900 XT (0x0000744C) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (AMD, AMD Radeon RX 6800 XT (0x000073BF) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (AMD, AMD Radeon RX 6700 XT (0x000073DF) Direct3D11 vs_5_0 ps_5_0, D3D11)",
    # Apple Silicon（Mac 平台）
    "ANGLE (Apple, Apple M3 Max, OpenGL 4.1)",
    "ANGLE (Apple, Apple M3 Pro, OpenGL 4.1)",
    "ANGLE (Apple, Apple M3, OpenGL 4.1)",
    "ANGLE (Apple, Apple M2 Pro, OpenGL 4.1)",
    "ANGLE (Apple, Apple M2, OpenGL 4.1)",
    "ANGLE (Apple, Apple M1 Pro, OpenGL 4.1)",
    "ANGLE (Apple, Apple M1, OpenGL 4.1)",
]

# ============ User-Agent 与平台映射 ============
# 确保 UA 与 sec-ch-ua-platform 一致性
# 2026年2月更新 - Chrome 144 版本
UA_PLATFORM_MAP = {
    # Windows UA -> Windows 平台
    "Windows NT 10.0": (
        "Windows",
        '"Windows"',
        '"Chromium";v="144", "Google Chrome";v="144", "Not A(Brand";v="24"',
    ),
    # macOS UA -> macOS 平台
    "Macintosh": (
        "macOS",
        '"macOS"',
        '"Chromium";v="144", "Google Chrome";v="144", "Not A(Brand";v="24"',
    ),
    # Linux UA -> Linux 平台
    "X11; Linux": (
        "Linux",
        '"Linux"',
        '"Chromium";v="144", "Google Chrome";v="144", "Not A(Brand";v="24"',
    ),
}

# Chrome 版本对应的 sec-ch-ua 值
# 2026年2月更新
CHROME_VERSION_SEC_CH_UA = {
    "144": '"Chromium";v="144", "Google Chrome";v="144", "Not A(Brand";v="24"',
    "143": '"Chromium";v="143", "Google Chrome";v="143", "Not A(Brand";v="24"',
    "142": '"Chromium";v="142", "Google Chrome";v="142", "Not A(Brand";v="24"',
    "141": '"Chromium";v="141", "Google Chrome";v="141", "Not A(Brand";v="24"',
    "140": '"Chromium";v="140", "Google Chrome";v="140", "Not A(Brand";v="24"',
    "131": '"Chromium";v="131", "Google Chrome";v="131", "Not A(Brand";v="24"',
    "130": '"Chromium";v="130", "Google Chrome";v="130", "Not A(Brand";v="24"',
    "129": '"Chromium";v="129", "Google Chrome";v="129", "Not A(Brand";v="24"',
    "124": '"Chromium";v="124", "Google Chrome";v="124", "Not A(Brand";v="24"',
    "120": '"Chromium";v="120", "Google Chrome";v="120", "Not A(Brand";v="24"',
}

# ============ 常见字体列表 ============
# 用于更真实的指纹生成（扩展至 FingerprintJS 完整测试范围）
COMMON_FONTS_WINDOWS = [
    # 核心 Windows 字体
    "Arial", "Arial Black", "Arial Narrow", "Arial Unicode MS",
    "Calibri", "Calibri Light", "Cambria", "Cambria Math", "Candara",
    "Comic Sans MS", "Consolas", "Constantia", "Corbel", "Courier New",
    # Office 字体
    "Franklin Gothic Medium", "Gabriola", "Garamond", "Georgia",
    "Impact", "Lucida Console", "Lucida Sans Unicode",
    # Microsoft 字体
    "Microsoft Sans Serif", "Microsoft YaHei", "Microsoft JhengHei",
    "Palatino Linotype", "Segoe UI", "Segoe UI Light", "Segoe UI Semibold",
    "Segoe Script", "Segoe Print", "SimSun", "Sylfaen",
    # 其他常见字体
    "Tahoma", "Times New Roman", "Trebuchet MS", "Verdana",
    "Webdings", "Wingdings", "Wingdings 2", "Wingdings 3",
    # 扩展字体
    "Book Antiqua", "Bookman Old Style", "Century", "Century Gothic",
    "Century Schoolbook", "Copperplate Gothic Bold", "Copperplate Gothic Light",
    "Ebrima", "Leelawadee UI", "Malgun Gothic", "Marlett",
    "Meiryo", "Meiryo UI", "MS Gothic", "MS Mincho", "MS PGothic",
    "MS PMincho", "MS UI Gothic", "MV Boli", "Myanmar Text",
    "Nirmala UI", "Palatino", "PMingLiU", "SimHei", "Yu Gothic",
]

COMMON_FONTS_MAC = [
    # 核心 macOS 字体
    "Arial", "Arial Black", "Arial Narrow", "Arial Unicode MS",
    "Courier New", "Georgia", "Helvetica", "Helvetica Neue",
    "Impact", "Lucida Grande", "Monaco", "Palatino",
    # Apple 系统字体
    "San Francisco", "SF Pro", "SF Pro Display", "SF Pro Text",
    "SF Mono", "SF Compact", "New York",
    # macOS 默认字体
    "Menlo", "American Typewriter", "Andale Mono", "Apple Chancery",
    "Apple Color Emoji", "Apple SD Gothic Neo", "Apple Symbols",
    "Avenir", "Avenir Next", "Avenir Next Condensed",
    "Baskerville", "Big Caslon", "Brush Script MT",
    "Chalkboard", "Chalkboard SE", "Charter", "Cochin",
    "Copperplate", "Didot", "Futura", "Geneva", "Gill Sans",
    "Hoefler Text", "Iowan Old Style", "Marker Felt",
    "Noteworthy", "Optima", "Papyrus", "Phosphate",
    "Rockwell", "Savoye LET", "SignPainter", "Snell Roundhand",
    "Times New Roman", "Trebuchet MS", "Verdana", "Zapfino",
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
# 2026年2月更新 - Chrome 144 版本
NAVIGATOR_PROPERTIES = {
    "windows": {
        "platform": "Win32",
        "appVersion": "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "vendor": "Google Inc.",
        "maxTouchPoints": 0,
        "hardwareConcurrency": [4, 8, 12, 16],
        "deviceMemory": [4, 8, 16, 32],
    },
    "macos": {
        "platform": "MacIntel",
        "appVersion": "5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "vendor": "Google Inc.",
        "maxTouchPoints": 0,
        "hardwareConcurrency": [4, 8, 10, 12],
        "deviceMemory": [8, 16, 32],
    },
    "linux": {
        "platform": "Linux x86_64",
        "appVersion": "5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "vendor": "Google Inc.",
        "maxTouchPoints": 0,
        "hardwareConcurrency": [4, 8, 16],
        "deviceMemory": [4, 8, 16, 32],
    },
}
