"""
反检测模块 - 浏览器数据常量

包含 curl_cffi Chrome 模拟版本、User-Agent 列表等常量。
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
