"""
真实设备数据目录

包含 2023-2025 年各品牌畅销机型的真实硬件规格。
所有数据来源于官方产品页面和技术评测。

PC 设备: Dell, Lenovo, Apple
移动设备: Apple iPhone, Samsung Galaxy
"""

from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class DeviceProfile:
    """不可变的设备档案"""

    # 设备标识
    brand: str
    model: str
    config_label: str  # 如 "i7/16G"
    device_type: str  # "desktop" | "mobile"
    os_family: str  # "windows" | "macos" | "ios" | "android"

    # 屏幕
    screen_width: int
    screen_height: int
    color_depth: int
    pixel_ratio: float

    # 硬件
    cpu_cores: int
    device_memory: int  # GB
    max_touch_points: int

    # 浏览器身份
    platform: str  # navigator.platform
    ua_template: str  # User-Agent 模板，{chrome_ver} 占位
    sec_ch_ua_platform: str  # "Windows" / "macOS" / "iOS" / "Android"

    # WebGL
    webgl_vendor: str
    webgl_renderer: str

    # 标签
    tags: List[str] = field(default_factory=list)


# ============================================================
# PC 设备 — Dell
# ============================================================

DELL_XPS_15_9530_I7 = DeviceProfile(
    brand="Dell",
    model="XPS 15 9530",
    config_label="i7-13700H/16GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1200,
    color_depth=24,
    pixel_ratio=1.25,
    cpu_cores=14,
    device_memory=16,
    max_touch_points=0,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (NVIDIA)",
    webgl_renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 Laptop GPU Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["popular", "2023"],
)

DELL_XPS_15_9530_I9 = DeviceProfile(
    brand="Dell",
    model="XPS 15 9530",
    config_label="i9-13900H/32GB",
    device_type="desktop",
    os_family="windows",
    screen_width=3456,
    screen_height=2160,
    color_depth=24,
    pixel_ratio=2.0,
    cpu_cores=14,
    device_memory=32,
    max_touch_points=10,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (NVIDIA)",
    webgl_renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Laptop GPU Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["2023"],
)

DELL_XPS_15_9530_I5 = DeviceProfile(
    brand="Dell",
    model="XPS 15 9530",
    config_label="i5-13500H/8GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1200,
    color_depth=24,
    pixel_ratio=1.25,
    cpu_cores=12,
    device_memory=8,
    max_touch_points=0,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) Arc(TM) A370M Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["2023"],
)

DELL_INSPIRON_15_R5_8G = DeviceProfile(
    brand="Dell",
    model="Inspiron 15 3535",
    config_label="Ryzen5-7530U/8GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1080,
    color_depth=24,
    pixel_ratio=1.0,
    cpu_cores=6,
    device_memory=8,
    max_touch_points=0,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (AMD)",
    webgl_renderer="ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["popular", "budget", "2024"],
)

DELL_INSPIRON_15_R5_16G = DeviceProfile(
    brand="Dell",
    model="Inspiron 15 3535",
    config_label="Ryzen5-7530U/16GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1080,
    color_depth=24,
    pixel_ratio=1.0,
    cpu_cores=6,
    device_memory=16,
    max_touch_points=0,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (AMD)",
    webgl_renderer="ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["popular", "2024"],
)

DELL_INSPIRON_15_R7_16G = DeviceProfile(
    brand="Dell",
    model="Inspiron 15 3535",
    config_label="Ryzen7-7730U/16GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1080,
    color_depth=24,
    pixel_ratio=1.25,
    cpu_cores=8,
    device_memory=16,
    max_touch_points=0,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (AMD)",
    webgl_renderer="ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["2024"],
)

DELL_LATITUDE_7440_I5 = DeviceProfile(
    brand="Dell",
    model="Latitude 7440",
    config_label="i5-1345U/16GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1200,
    color_depth=24,
    pixel_ratio=1.25,
    cpu_cores=12,
    device_memory=16,
    max_touch_points=0,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["business", "2023"],
)

DELL_LATITUDE_7440_I7 = DeviceProfile(
    brand="Dell",
    model="Latitude 7440",
    config_label="i7-1370P/16GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1200,
    color_depth=24,
    pixel_ratio=1.25,
    cpu_cores=14,
    device_memory=16,
    max_touch_points=0,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["business", "popular", "2023"],
)

DELL_LATITUDE_7440_I7_32G = DeviceProfile(
    brand="Dell",
    model="Latitude 7440",
    config_label="i7-1370P/32GB",
    device_type="desktop",
    os_family="windows",
    screen_width=2560,
    screen_height=1600,
    color_depth=24,
    pixel_ratio=1.5,
    cpu_cores=14,
    device_memory=32,
    max_touch_points=10,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["business", "2023"],
)

# ============================================================
# PC 设备 — Lenovo
# ============================================================

LENOVO_X1_CARBON_G12_U7_16G = DeviceProfile(
    brand="Lenovo",
    model="ThinkPad X1 Carbon Gen 12",
    config_label="Ultra7-155H/16GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1200,
    color_depth=24,
    pixel_ratio=1.25,
    cpu_cores=16,
    device_memory=16,
    max_touch_points=0,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) Arc(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["business", "popular", "2024"],
)

LENOVO_X1_CARBON_G12_U7_32G = DeviceProfile(
    brand="Lenovo",
    model="ThinkPad X1 Carbon Gen 12",
    config_label="Ultra7-155H/32GB",
    device_type="desktop",
    os_family="windows",
    screen_width=2880,
    screen_height=1800,
    color_depth=24,
    pixel_ratio=2.0,
    cpu_cores=16,
    device_memory=32,
    max_touch_points=10,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) Arc(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["business", "2024"],
)

LENOVO_X1_CARBON_G12_U5_16G = DeviceProfile(
    brand="Lenovo",
    model="ThinkPad X1 Carbon Gen 12",
    config_label="Ultra5-125H/16GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1200,
    color_depth=24,
    pixel_ratio=1.25,
    cpu_cores=14,
    device_memory=16,
    max_touch_points=0,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) Arc(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["business", "2024"],
)

LENOVO_IDEAPAD_SLIM3_I5_8G = DeviceProfile(
    brand="Lenovo",
    model="IdeaPad Slim 3 15",
    config_label="i5-1335U/8GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1080,
    color_depth=24,
    pixel_ratio=1.0,
    cpu_cores=10,
    device_memory=8,
    max_touch_points=0,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["budget", "popular", "2024"],
)

LENOVO_IDEAPAD_SLIM3_I5_16G = DeviceProfile(
    brand="Lenovo",
    model="IdeaPad Slim 3 15",
    config_label="i5-1335U/16GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1080,
    color_depth=24,
    pixel_ratio=1.0,
    cpu_cores=10,
    device_memory=16,
    max_touch_points=0,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["budget", "2024"],
)

LENOVO_IDEAPAD_SLIM3_R5_8G = DeviceProfile(
    brand="Lenovo",
    model="IdeaPad Slim 3 15",
    config_label="Ryzen5-7520U/8GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1080,
    color_depth=24,
    pixel_ratio=1.0,
    cpu_cores=4,
    device_memory=8,
    max_touch_points=0,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (AMD)",
    webgl_renderer="ANGLE (AMD, AMD Radeon(TM) Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["budget", "2023"],
)

LENOVO_YOGA7_R7_16G = DeviceProfile(
    brand="Lenovo",
    model="Yoga 7 14 2-in-1",
    config_label="Ryzen7-7840HS/16GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1200,
    color_depth=24,
    pixel_ratio=1.25,
    cpu_cores=8,
    device_memory=16,
    max_touch_points=10,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (AMD)",
    webgl_renderer="ANGLE (AMD, AMD Radeon(TM) 780M Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["2024"],
)

LENOVO_YOGA7_R5_8G = DeviceProfile(
    brand="Lenovo",
    model="Yoga 7 14 2-in-1",
    config_label="Ryzen5-7535HS/8GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1200,
    color_depth=24,
    pixel_ratio=1.25,
    cpu_cores=6,
    device_memory=8,
    max_touch_points=10,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (AMD)",
    webgl_renderer="ANGLE (AMD, AMD Radeon(TM) 760M Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["2024"],
)

LENOVO_YOGA7_R7_16G_OLED = DeviceProfile(
    brand="Lenovo",
    model="Yoga 7 14 2-in-1",
    config_label="Ryzen7-7840HS/16GB-OLED",
    device_type="desktop",
    os_family="windows",
    screen_width=2880,
    screen_height=1800,
    color_depth=24,
    pixel_ratio=2.0,
    cpu_cores=8,
    device_memory=16,
    max_touch_points=10,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (AMD)",
    webgl_renderer="ANGLE (AMD, AMD Radeon(TM) 780M Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
    tags=["2024"],
)

# ============================================================
# PC 设备 — Apple
# ============================================================

APPLE_MBA13_M3_8G = DeviceProfile(
    brand="Apple",
    model="MacBook Air 13 M3",
    config_label="M3-8C/8GB",
    device_type="desktop",
    os_family="macos",
    screen_width=2560,
    screen_height=1664,
    color_depth=30,
    pixel_ratio=2.0,
    cpu_cores=8,
    device_memory=8,
    max_touch_points=0,
    platform="MacIntel",
    ua_template="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"macOS"',
    webgl_vendor="Google Inc. (Apple)",
    webgl_renderer="ANGLE (Apple, ANGLE Metal Renderer: Apple M3, Unspecified Version)",
    tags=["popular", "2024"],
)

APPLE_MBA13_M3_16G = DeviceProfile(
    brand="Apple",
    model="MacBook Air 13 M3",
    config_label="M3-10C/16GB",
    device_type="desktop",
    os_family="macos",
    screen_width=2560,
    screen_height=1664,
    color_depth=30,
    pixel_ratio=2.0,
    cpu_cores=8,
    device_memory=16,
    max_touch_points=0,
    platform="MacIntel",
    ua_template="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"macOS"',
    webgl_vendor="Google Inc. (Apple)",
    webgl_renderer="ANGLE (Apple, ANGLE Metal Renderer: Apple M3, Unspecified Version)",
    tags=["popular", "2024"],
)

APPLE_MBA13_M3_24G = DeviceProfile(
    brand="Apple",
    model="MacBook Air 13 M3",
    config_label="M3-10C/24GB",
    device_type="desktop",
    os_family="macos",
    screen_width=2560,
    screen_height=1664,
    color_depth=30,
    pixel_ratio=2.0,
    cpu_cores=8,
    device_memory=24,
    max_touch_points=0,
    platform="MacIntel",
    ua_template="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"macOS"',
    webgl_vendor="Google Inc. (Apple)",
    webgl_renderer="ANGLE (Apple, ANGLE Metal Renderer: Apple M3, Unspecified Version)",
    tags=["2024"],
)

APPLE_MBA15_M3_16G = DeviceProfile(
    brand="Apple",
    model="MacBook Air 15 M3",
    config_label="M3-10C/16GB",
    device_type="desktop",
    os_family="macos",
    screen_width=2880,
    screen_height=1864,
    color_depth=30,
    pixel_ratio=2.0,
    cpu_cores=8,
    device_memory=16,
    max_touch_points=0,
    platform="MacIntel",
    ua_template="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"macOS"',
    webgl_vendor="Google Inc. (Apple)",
    webgl_renderer="ANGLE (Apple, ANGLE Metal Renderer: Apple M3, Unspecified Version)",
    tags=["popular", "2024"],
)

APPLE_MBA15_M3_24G = DeviceProfile(
    brand="Apple",
    model="MacBook Air 15 M3",
    config_label="M3-10C/24GB",
    device_type="desktop",
    os_family="macos",
    screen_width=2880,
    screen_height=1864,
    color_depth=30,
    pixel_ratio=2.0,
    cpu_cores=8,
    device_memory=24,
    max_touch_points=0,
    platform="MacIntel",
    ua_template="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"macOS"',
    webgl_vendor="Google Inc. (Apple)",
    webgl_renderer="ANGLE (Apple, ANGLE Metal Renderer: Apple M3, Unspecified Version)",
    tags=["2024"],
)

APPLE_MBA15_M3_8G = DeviceProfile(
    brand="Apple",
    model="MacBook Air 15 M3",
    config_label="M3-10C/8GB",
    device_type="desktop",
    os_family="macos",
    screen_width=2880,
    screen_height=1864,
    color_depth=30,
    pixel_ratio=2.0,
    cpu_cores=8,
    device_memory=8,
    max_touch_points=0,
    platform="MacIntel",
    ua_template="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"macOS"',
    webgl_vendor="Google Inc. (Apple)",
    webgl_renderer="ANGLE (Apple, ANGLE Metal Renderer: Apple M3, Unspecified Version)",
    tags=["2024"],
)

APPLE_MBP14_M3PRO_18G = DeviceProfile(
    brand="Apple",
    model="MacBook Pro 14 M3 Pro",
    config_label="M3Pro-12C/18GB",
    device_type="desktop",
    os_family="macos",
    screen_width=3024,
    screen_height=1964,
    color_depth=30,
    pixel_ratio=2.0,
    cpu_cores=12,
    device_memory=18,
    max_touch_points=0,
    platform="MacIntel",
    ua_template="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"macOS"',
    webgl_vendor="Google Inc. (Apple)",
    webgl_renderer="ANGLE (Apple, ANGLE Metal Renderer: Apple M3 Pro, Unspecified Version)",
    tags=["pro", "2023"],
)

APPLE_MBP14_M3PRO_36G = DeviceProfile(
    brand="Apple",
    model="MacBook Pro 14 M3 Pro",
    config_label="M3Pro-12C/36GB",
    device_type="desktop",
    os_family="macos",
    screen_width=3024,
    screen_height=1964,
    color_depth=30,
    pixel_ratio=2.0,
    cpu_cores=12,
    device_memory=36,
    max_touch_points=0,
    platform="MacIntel",
    ua_template="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"macOS"',
    webgl_vendor="Google Inc. (Apple)",
    webgl_renderer="ANGLE (Apple, ANGLE Metal Renderer: Apple M3 Pro, Unspecified Version)",
    tags=["pro", "2023"],
)

APPLE_MBP14_M4_16G = DeviceProfile(
    brand="Apple",
    model="MacBook Pro 14 M4",
    config_label="M4-10C/16GB",
    device_type="desktop",
    os_family="macos",
    screen_width=3024,
    screen_height=1964,
    color_depth=30,
    pixel_ratio=2.0,
    cpu_cores=10,
    device_memory=16,
    max_touch_points=0,
    platform="MacIntel",
    ua_template="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"macOS"',
    webgl_vendor="Google Inc. (Apple)",
    webgl_renderer="ANGLE (Apple, ANGLE Metal Renderer: Apple M4, Unspecified Version)",
    tags=["pro", "popular", "2024"],
)

# ============================================================
# 移动设备 — Apple iPhone
# ============================================================

IPHONE_15 = DeviceProfile(
    brand="Apple",
    model="iPhone 15",
    config_label="A16/6GB",
    device_type="mobile",
    os_family="ios",
    screen_width=393,
    screen_height=852,
    color_depth=32,
    pixel_ratio=3.0,
    cpu_cores=6,
    device_memory=6,
    max_touch_points=5,
    platform="iPhone",
    ua_template="Mozilla/5.0 (iPhone; CPU iPhone OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/{chrome_ver} Mobile/15E148 Safari/604.1",
    sec_ch_ua_platform='"iOS"',
    webgl_vendor="Apple Inc.",
    webgl_renderer="Apple GPU",
    tags=["popular", "2023"],
)

IPHONE_15_PRO = DeviceProfile(
    brand="Apple",
    model="iPhone 15 Pro",
    config_label="A17Pro/8GB",
    device_type="mobile",
    os_family="ios",
    screen_width=393,
    screen_height=852,
    color_depth=32,
    pixel_ratio=3.0,
    cpu_cores=6,
    device_memory=8,
    max_touch_points=5,
    platform="iPhone",
    ua_template="Mozilla/5.0 (iPhone; CPU iPhone OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/{chrome_ver} Mobile/15E148 Safari/604.1",
    sec_ch_ua_platform='"iOS"',
    webgl_vendor="Apple Inc.",
    webgl_renderer="Apple GPU",
    tags=["popular", "2023"],
)

IPHONE_15_PRO_MAX = DeviceProfile(
    brand="Apple",
    model="iPhone 15 Pro Max",
    config_label="A17Pro/8GB",
    device_type="mobile",
    os_family="ios",
    screen_width=430,
    screen_height=932,
    color_depth=32,
    pixel_ratio=3.0,
    cpu_cores=6,
    device_memory=8,
    max_touch_points=5,
    platform="iPhone",
    ua_template="Mozilla/5.0 (iPhone; CPU iPhone OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/{chrome_ver} Mobile/15E148 Safari/604.1",
    sec_ch_ua_platform='"iOS"',
    webgl_vendor="Apple Inc.",
    webgl_renderer="Apple GPU",
    tags=["popular", "2023"],
)

IPHONE_14 = DeviceProfile(
    brand="Apple",
    model="iPhone 14",
    config_label="A15/6GB",
    device_type="mobile",
    os_family="ios",
    screen_width=390,
    screen_height=844,
    color_depth=32,
    pixel_ratio=3.0,
    cpu_cores=6,
    device_memory=6,
    max_touch_points=5,
    platform="iPhone",
    ua_template="Mozilla/5.0 (iPhone; CPU iPhone OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/{chrome_ver} Mobile/15E148 Safari/604.1",
    sec_ch_ua_platform='"iOS"',
    webgl_vendor="Apple Inc.",
    webgl_renderer="Apple GPU",
    tags=["popular", "2023"],
)

IPHONE_14_PRO = DeviceProfile(
    brand="Apple",
    model="iPhone 14 Pro",
    config_label="A16/6GB",
    device_type="mobile",
    os_family="ios",
    screen_width=393,
    screen_height=852,
    color_depth=32,
    pixel_ratio=3.0,
    cpu_cores=6,
    device_memory=6,
    max_touch_points=5,
    platform="iPhone",
    ua_template="Mozilla/5.0 (iPhone; CPU iPhone OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/{chrome_ver} Mobile/15E148 Safari/604.1",
    sec_ch_ua_platform='"iOS"',
    webgl_vendor="Apple Inc.",
    webgl_renderer="Apple GPU",
    tags=["2023"],
)

IPHONE_14_PRO_MAX = DeviceProfile(
    brand="Apple",
    model="iPhone 14 Pro Max",
    config_label="A16/6GB",
    device_type="mobile",
    os_family="ios",
    screen_width=430,
    screen_height=932,
    color_depth=32,
    pixel_ratio=3.0,
    cpu_cores=6,
    device_memory=6,
    max_touch_points=5,
    platform="iPhone",
    ua_template="Mozilla/5.0 (iPhone; CPU iPhone OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/{chrome_ver} Mobile/15E148 Safari/604.1",
    sec_ch_ua_platform='"iOS"',
    webgl_vendor="Apple Inc.",
    webgl_renderer="Apple GPU",
    tags=["2023"],
)

# ============================================================
# 移动设备 — Samsung Galaxy
# ============================================================

SAMSUNG_S24 = DeviceProfile(
    brand="Samsung",
    model="Galaxy S24",
    config_label="SD8Gen3/8GB",
    device_type="mobile",
    os_family="android",
    screen_width=360,
    screen_height=780,
    color_depth=24,
    pixel_ratio=3.0,
    cpu_cores=8,
    device_memory=8,
    max_touch_points=5,
    platform="Linux armv81",
    ua_template="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Mobile Safari/537.36",
    sec_ch_ua_platform='"Android"',
    webgl_vendor="Qualcomm",
    webgl_renderer="Adreno (TM) 750",
    tags=["popular", "2024"],
)

SAMSUNG_S24_ULTRA = DeviceProfile(
    brand="Samsung",
    model="Galaxy S24 Ultra",
    config_label="SD8Gen3/12GB",
    device_type="mobile",
    os_family="android",
    screen_width=360,
    screen_height=780,
    color_depth=24,
    pixel_ratio=3.5,
    cpu_cores=8,
    device_memory=12,
    max_touch_points=5,
    platform="Linux armv81",
    ua_template="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Mobile Safari/537.36",
    sec_ch_ua_platform='"Android"',
    webgl_vendor="Qualcomm",
    webgl_renderer="Adreno (TM) 750",
    tags=["popular", "2024"],
)

SAMSUNG_A54 = DeviceProfile(
    brand="Samsung",
    model="Galaxy A54 5G",
    config_label="Exynos1380/8GB",
    device_type="mobile",
    os_family="android",
    screen_width=360,
    screen_height=780,
    color_depth=24,
    pixel_ratio=3.0,
    cpu_cores=8,
    device_memory=8,
    max_touch_points=5,
    platform="Linux armv81",
    ua_template="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Mobile Safari/537.36",
    sec_ch_ua_platform='"Android"',
    webgl_vendor="ARM",
    webgl_renderer="Mali-G68",
    tags=["popular", "budget", "2023"],
)

SAMSUNG_S23 = DeviceProfile(
    brand="Samsung",
    model="Galaxy S23",
    config_label="SD8Gen2/8GB",
    device_type="mobile",
    os_family="android",
    screen_width=360,
    screen_height=780,
    color_depth=24,
    pixel_ratio=3.0,
    cpu_cores=8,
    device_memory=8,
    max_touch_points=5,
    platform="Linux armv81",
    ua_template="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Mobile Safari/537.36",
    sec_ch_ua_platform='"Android"',
    webgl_vendor="Qualcomm",
    webgl_renderer="Adreno (TM) 740",
    tags=["popular", "2023"],
)

SAMSUNG_S23_ULTRA = DeviceProfile(
    brand="Samsung",
    model="Galaxy S23 Ultra",
    config_label="SD8Gen2/12GB",
    device_type="mobile",
    os_family="android",
    screen_width=360,
    screen_height=780,
    color_depth=24,
    pixel_ratio=3.5,
    cpu_cores=8,
    device_memory=12,
    max_touch_points=5,
    platform="Linux armv81",
    ua_template="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Mobile Safari/537.36",
    sec_ch_ua_platform='"Android"',
    webgl_vendor="Qualcomm",
    webgl_renderer="Adreno (TM) 740",
    tags=["2023"],
)

SAMSUNG_A15 = DeviceProfile(
    brand="Samsung",
    model="Galaxy A15",
    config_label="Helio-G99/6GB",
    device_type="mobile",
    os_family="android",
    screen_width=360,
    screen_height=780,
    color_depth=24,
    pixel_ratio=3.0,
    cpu_cores=8,
    device_memory=6,
    max_touch_points=5,
    platform="Linux armv81",
    ua_template="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Mobile Safari/537.36",
    sec_ch_ua_platform='"Android"',
    webgl_vendor="ARM",
    webgl_renderer="Mali-G57 MC2",
    tags=["popular", "budget", "2024"],
)

# ============================================================
# 设备集合
# ============================================================

ALL_DESKTOP_DEVICES: List[DeviceProfile] = [
    # Dell
    DELL_XPS_15_9530_I7, DELL_XPS_15_9530_I9, DELL_XPS_15_9530_I5,
    DELL_INSPIRON_15_R5_8G, DELL_INSPIRON_15_R5_16G, DELL_INSPIRON_15_R7_16G,
    DELL_LATITUDE_7440_I5, DELL_LATITUDE_7440_I7, DELL_LATITUDE_7440_I7_32G,
    # Lenovo
    LENOVO_X1_CARBON_G12_U7_16G, LENOVO_X1_CARBON_G12_U7_32G, LENOVO_X1_CARBON_G12_U5_16G,
    LENOVO_IDEAPAD_SLIM3_I5_8G, LENOVO_IDEAPAD_SLIM3_I5_16G, LENOVO_IDEAPAD_SLIM3_R5_8G,
    LENOVO_YOGA7_R7_16G, LENOVO_YOGA7_R5_8G, LENOVO_YOGA7_R7_16G_OLED,
    # Apple Mac
    APPLE_MBA13_M3_8G, APPLE_MBA13_M3_16G, APPLE_MBA13_M3_24G,
    APPLE_MBA15_M3_16G, APPLE_MBA15_M3_24G, APPLE_MBA15_M3_8G,
    APPLE_MBP14_M3PRO_18G, APPLE_MBP14_M3PRO_36G, APPLE_MBP14_M4_16G,
]

ALL_MOBILE_DEVICES: List[DeviceProfile] = [
    # iPhone
    IPHONE_15, IPHONE_15_PRO, IPHONE_15_PRO_MAX,
    IPHONE_14, IPHONE_14_PRO, IPHONE_14_PRO_MAX,
    # Samsung
    SAMSUNG_S24, SAMSUNG_S24_ULTRA, SAMSUNG_A54,
    SAMSUNG_S23, SAMSUNG_S23_ULTRA, SAMSUNG_A15,
]

ALL_DEVICES: List[DeviceProfile] = ALL_DESKTOP_DEVICES + ALL_MOBILE_DEVICES

# 按品牌索引
DEVICES_BY_BRAND = {}
for _dev in ALL_DEVICES:
    _brand_key = _dev.brand.lower()
    if _brand_key not in DEVICES_BY_BRAND:
        DEVICES_BY_BRAND[_brand_key] = []
    DEVICES_BY_BRAND[_brand_key].append(_dev)

# 按类型索引
DEVICES_BY_TYPE = {
    "desktop": ALL_DESKTOP_DEVICES,
    "mobile": ALL_MOBILE_DEVICES,
}
