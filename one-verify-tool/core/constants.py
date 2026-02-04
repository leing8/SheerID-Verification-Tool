"""
核心常量模块 - 所有配置常量

包含:
- Chrome 版本配置
- User-Agent 列表
- 屏幕分辨率、时区、语言等浏览器特征
- WebGL 配置
- Navigator 属性
- API 配置
"""

# ============ curl_cffi 检查 ============
try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

# ============ API 配置 ============
PROGRAM_ID = "67c8c14f5f17a83b745e3f82"
SHEERID_API_URL = "https://services.sheerid.com/rest/v2"

# ============ 延迟配置 ============
MIN_DELAY = 500   # 增加最小延迟
MAX_DELAY = 1500  # 增加最大延迟
TYPING_MIN_DELAY = 50   # 打字最小延迟 (ms)
TYPING_MAX_DELAY = 150  # 打字最大延迟 (ms)
PAGE_READ_DELAY = (2000, 5000)  # 页面阅读延迟范围 (ms)

# ============ Chrome 版本配置 ============
CHROME_VERSIONS = [
    "chrome133",
    "chrome132",
    "chrome131",
    "chrome130",
    "chrome124",
]

IMPERSONATE_OPTIONS = {
    "chrome": ["chrome133", "chrome132", "chrome131", "chrome130", "chrome124"],
    "edge": ["edge133", "edge131", "edge127", "edge101"],
    "safari": ["safari18", "safari17_2_ios", "safari17_0"],
}

DEFAULT_IMPERSONATE = "chrome133"

# ============ User-Agent 列表 (按版本分组) ============
USER_AGENTS_CHROME = {
    "133": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    ],
    "132": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    ],
    "131": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    ],
    "130": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    ],
    "124": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    ],
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
]

# ============ 屏幕分辨率 (按常见度排序) ============
RESOLUTIONS = [
    "1920x1080",  # 最常见
    "1366x768",
    "1536x864",
    "1440x900",
    "2560x1440",
    "1280x720",
    "1600x900",
    "1680x1050",
    "2560x1080",
    "3840x2160",  # 4K
]

# ============ 屏幕详细配置 ============
SCREEN_CONFIGS = {
    "1920x1080": {"availWidth": 1920, "availHeight": 1040, "colorDepth": 24, "pixelRatio": 1},
    "1366x768": {"availWidth": 1366, "availHeight": 728, "colorDepth": 24, "pixelRatio": 1},
    "1536x864": {"availWidth": 1536, "availHeight": 824, "colorDepth": 24, "pixelRatio": 1.25},
    "1440x900": {"availWidth": 1440, "availHeight": 860, "colorDepth": 24, "pixelRatio": 1},
    "2560x1440": {"availWidth": 2560, "availHeight": 1400, "colorDepth": 24, "pixelRatio": 1},
    "3840x2160": {"availWidth": 3840, "availHeight": 2120, "colorDepth": 30, "pixelRatio": 2},
}

# ============ 时区 ============
US_TIMEZONES = [-8, -7, -6, -5, -4]  # PST, MST, CST, EST, AST
US_TIMEZONE_NAMES = {
    -8: "America/Los_Angeles",
    -7: "America/Denver",
    -6: "America/Chicago",
    -5: "America/New_York",
    -4: "America/Puerto_Rico",
}
ALL_TIMEZONES = [-8, -7, -6, -5, -4, -3, 0, 1, 2, 3, 5.5, 8, 9, 10]

# ============ 语言 ============
LANGUAGES = [
    "en-US,en;q=0.9",
    "en-US,en;q=0.9,es;q=0.8",
    "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "en-GB,en;q=0.9,en-US;q=0.8",
    "en-US,en;q=0.9,fr;q=0.8",
]

# ============ 平台配置 (与 User-Agent 匹配) ============
PLATFORMS = {
    "windows": {
        "platform": "Win32",
        "sec_ch_ua_platform": '"Windows"',
        "os_version": ["10.0.0", "10.0.19041", "10.0.19042", "10.0.19043", "10.0.22000", "10.0.22621"],
        "arch": "x86",
        "bitness": "64",
    },
    "macos": {
        "platform": "MacIntel",
        "sec_ch_ua_platform": '"macOS"',
        "os_version": ["14.0.0", "14.1.0", "14.2.0", "14.3.0", "14.4.0", "15.0.0"],
        "arch": "arm",
        "bitness": "64",
    },
    "linux": {
        "platform": "Linux x86_64",
        "sec_ch_ua_platform": '"Linux"',
        "os_version": ["6.1.0", "6.2.0", "6.5.0", "6.6.0"],
        "arch": "x86",
        "bitness": "64",
    },
}

# Chrome 版本对应的 sec-ch-ua 格式
SEC_CH_UA_TEMPLATES = {
    "133": '"Chromium";v="133", "Google Chrome";v="133", "Not-A.Brand";v="24"',
    "132": '"Chromium";v="132", "Google Chrome";v="132", "Not-A.Brand";v="24"',
    "131": '"Chromium";v="131", "Google Chrome";v="131", "Not_A Brand";v="24"',
    "130": '"Chromium";v="130", "Google Chrome";v="130", "Not_A Brand";v="24"',
    "124": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
}

# 旧格式兼容
PLATFORMS_LEGACY = [
    ("Windows", '"Windows"', '"Chromium";v="133", "Google Chrome";v="133", "Not-A.Brand";v="24"'),
    ("Windows", '"Windows"', '"Chromium";v="132", "Google Chrome";v="132", "Not-A.Brand";v="24"'),
    ("Windows", '"Windows"', '"Chromium";v="131", "Google Chrome";v="131", "Not_A Brand";v="24"'),
    ("macOS", '"macOS"', '"Chromium";v="133", "Google Chrome";v="133", "Not-A.Brand";v="24"'),
    ("Linux", '"Linux"', '"Chromium";v="133", "Google Chrome";v="133", "Not-A.Brand";v="24"'),
]

# ============ WebGL 配置 (按平台分组) ============
WEBGL_CONFIGS = {
    "windows": {
        "vendors": ["Google Inc. (NVIDIA)", "Google Inc. (Intel)", "Google Inc. (AMD)"],
        "renderers": {
            "NVIDIA": [
                "ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0, D3D11)",
                "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)",
                "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0, D3D11)",
                "ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Direct3D11 vs_5_0 ps_5_0, D3D11)",
                "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0, D3D11)",
            ],
            "Intel": [
                "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)",
                "ANGLE (Intel, Intel(R) UHD Graphics 770 Direct3D11 vs_5_0 ps_5_0, D3D11)",
                "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
            ],
            "AMD": [
                "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0, D3D11)",
                "ANGLE (AMD, AMD Radeon RX 6600 Direct3D11 vs_5_0 ps_5_0, D3D11)",
                "ANGLE (AMD, AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0, D3D11)",
            ],
        },
    },
    "macos": {
        "vendors": ["Google Inc. (Apple)"],
        "renderers": {
            "Apple": [
                "ANGLE (Apple, Apple M1, OpenGL 4.1)",
                "ANGLE (Apple, Apple M1 Pro, OpenGL 4.1)",
                "ANGLE (Apple, Apple M1 Max, OpenGL 4.1)",
                "ANGLE (Apple, Apple M2, OpenGL 4.1)",
                "ANGLE (Apple, Apple M2 Pro, OpenGL 4.1)",
                "ANGLE (Apple, Apple M3, OpenGL 4.1)",
                "ANGLE (Apple, Apple M3 Pro, OpenGL 4.1)",
            ],
        },
    },
    "linux": {
        "vendors": ["Google Inc. (NVIDIA)", "Google Inc. (Intel)", "Google Inc. (AMD)"],
        "renderers": {
            "NVIDIA": [
                "ANGLE (NVIDIA, NVIDIA GeForce GTX 1080, OpenGL 4.5)",
                "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060, OpenGL 4.6)",
            ],
            "Intel": [
                "ANGLE (Intel, Mesa Intel(R) UHD Graphics 630, OpenGL 4.6)",
            ],
            "AMD": [
                "ANGLE (AMD, AMD Radeon RX 580, OpenGL 4.6)",
            ],
        },
    },
}

# 旧格式兼容
WEBGL_VENDORS = [
    "Google Inc. (NVIDIA)",
    "Google Inc. (Intel)",
    "Google Inc. (AMD)",
    "Google Inc. (Apple)",
]

WEBGL_RENDERERS = [
    "ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (AMD, AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    "ANGLE (Apple, Apple M1 Pro, OpenGL 4.1)",
]

# ============ WebGL Extensions ============
WEBGL_EXTENSIONS = [
    "ANGLE_instanced_arrays",
    "EXT_blend_minmax",
    "EXT_color_buffer_half_float",
    "EXT_disjoint_timer_query",
    "EXT_float_blend",
    "EXT_frag_depth",
    "EXT_shader_texture_lod",
    "EXT_texture_compression_bptc",
    "EXT_texture_compression_rgtc",
    "EXT_texture_filter_anisotropic",
    "EXT_sRGB",
    "KHR_parallel_shader_compile",
    "OES_element_index_uint",
    "OES_fbo_render_mipmap",
    "OES_standard_derivatives",
    "OES_texture_float",
    "OES_texture_float_linear",
    "OES_texture_half_float",
    "OES_texture_half_float_linear",
    "OES_vertex_array_object",
    "WEBGL_color_buffer_float",
    "WEBGL_compressed_texture_s3tc",
    "WEBGL_compressed_texture_s3tc_srgb",
    "WEBGL_debug_renderer_info",
    "WEBGL_debug_shaders",
    "WEBGL_depth_texture",
    "WEBGL_draw_buffers",
    "WEBGL_lose_context",
    "WEBGL_multi_draw",
]

# ============ Navigator 属性 ============
NAVIGATOR_PROPS = {
    "hardwareConcurrency": [4, 6, 8, 12, 16],
    "deviceMemory": [4, 8, 16, 32],
    "maxTouchPoints": [0, 0, 0, 0, 0, 1, 5, 10],  # 桌面通常为 0
    "pdfViewerEnabled": True,
    "cookieEnabled": True,
    "doNotTrack": None,  # 大多数用户未设置
    "webdriver": False,  # 重要：必须为 False
}

# ============ Navigator Plugins (Chrome 特有) ============
NAVIGATOR_PLUGINS = [
    {"name": "PDF Viewer", "filename": "internal-pdf-viewer", "description": "Portable Document Format"},
    {"name": "Chrome PDF Viewer", "filename": "internal-pdf-viewer", "description": "Portable Document Format"},
    {"name": "Chromium PDF Viewer", "filename": "internal-pdf-viewer", "description": "Portable Document Format"},
    {"name": "Microsoft Edge PDF Viewer", "filename": "internal-pdf-viewer", "description": "Portable Document Format"},
    {"name": "WebKit built-in PDF", "filename": "internal-pdf-viewer", "description": "Portable Document Format"},
]

# ============ Audio 配置 ============
AUDIO_CONTEXT_CONFIG = {
    "sampleRate": [44100, 48000],
    "channelCount": [2],
    "state": "running",
    "baseLatency": [0.005333333333333333, 0.01, 0.02],
}

# ============ 欺诈处理帮助信息 ============
FRAUD_ERROR_HELP = """\
🚨 SheerID 欺诈检测触发 (fraudRulesReject)

风险信号可能包括:
- TLS 指纹不匹配（Python vs 真实浏览器）
- 数据中心 IP / IP 信誉差
- 设备指纹重复或不一致
- 高频重试 / 请求模式异常
- IP 地理位置与学校不匹配
- 文档模板重复使用

✅ 解决方案（按顺序尝试）:
  1) 确保已安装 curl_cffi: pip install curl_cffi
  2) 使用住宅代理替代数据中心代理
  3) 确保代理 IP 与学校在同一地区
  4) 等待 24-48 小时后重试
  5) 更换大学/组织
  6) 更换 IP 和设备指纹
"""

# ============ 速率限制配置 ============
RATE_LIMIT_CONFIG = {
    "max_requests_per_minute": 8,
    "min_interval_ms": 800,
    "burst_limit": 3,
    "cooldown_after_burst_ms": 5000,
}
