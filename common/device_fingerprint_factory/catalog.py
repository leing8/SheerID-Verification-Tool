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

    # 可用屏幕区域 (扣除任务栏/菜单栏, 有默认值的字段放在最后)
    # SheerID learn.js 通过 dth 信号收集 screen.availWidth/availHeight
    avail_screen_width: int = 0   # 0 = 默认等于 screen_width
    avail_screen_height: int = 0  # 0 = 默认根据 OS 自动计算

    # 标签
    tags: List[str] = field(default_factory=list)

    def get_avail_width(self) -> int:
        """获取可用屏幕宽度 (默认等于 screen_width)"""
        return self.avail_screen_width if self.avail_screen_width > 0 else self.screen_width

    def get_avail_height(self) -> int:
        """获取可用屏幕高度 (扣除任务栏/菜单栏)"""
        if self.avail_screen_height > 0:
            return self.avail_screen_height
        # 默认按 OS 自动计算
        if self.os_family == "windows":
            return self.screen_height - 48   # Windows 任务栏默认 48px
        elif self.os_family == "macos":
            return self.screen_height - 25   # macOS 菜单栏默认 25px
        return self.screen_height


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
    color_depth=32,
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
    color_depth=32,
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
    color_depth=32,
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
    color_depth=32,
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
    color_depth=32,
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
    color_depth=32,
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
    color_depth=32,
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
    color_depth=32,
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
    color_depth=32,
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
    color_depth=32,
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
    color_depth=32,
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
    color_depth=32,
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
    color_depth=32,
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
    color_depth=32,
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
    color_depth=32,
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
    color_depth=32,
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
    color_depth=32,
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
    color_depth=32,
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
# 桌面设备 — HP 惠普
# ============================================================

# --- HP Pavilion 15 (2023-2024, 最畅销学生/入门笔记本) ---
# 15.6" FHD IPS 1920x1080, Intel 13th Gen, Intel Iris Xe Graphics

HP_PAVILION_15_I5_8G = DeviceProfile(
    brand="HP",
    model="Pavilion 15",
    config_label="i5-1335U/8GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1080,
    color_depth=32,
    pixel_ratio=1.0,
    cpu_cores=10,
    device_memory=8,
    max_touch_points=0,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) Iris(R) Xe Graphics, D3D11)",
    tags=["popular", "budget", "2023"],
)

HP_PAVILION_15_I5_16G = DeviceProfile(
    brand="HP",
    model="Pavilion 15",
    config_label="i5-1335U/16GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1080,
    color_depth=32,
    pixel_ratio=1.0,
    cpu_cores=10,
    device_memory=16,
    max_touch_points=0,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) Iris(R) Xe Graphics, D3D11)",
    tags=["popular", "2023"],
)

HP_PAVILION_15_I7_16G = DeviceProfile(
    brand="HP",
    model="Pavilion 15",
    config_label="i7-1355U/16GB",
    device_type="desktop",
    os_family="windows",
    screen_width=1920,
    screen_height=1080,
    color_depth=32,
    pixel_ratio=1.25,
    cpu_cores=10,
    device_memory=16,
    max_touch_points=0,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) Iris(R) Xe Graphics, D3D11)",
    tags=["popular", "2023"],
)

# --- HP Spectre x360 14 (2024, 最畅销高端笔记本) ---
# 14" 2880x1800 OLED, Intel Core Ultra (Meteor Lake), Intel Arc Graphics

HP_SPECTRE_X360_14_U5_16G = DeviceProfile(
    brand="HP",
    model="Spectre x360 14",
    config_label="Ultra5-125H/16GB",
    device_type="desktop",
    os_family="windows",
    screen_width=2880,
    screen_height=1800,
    color_depth=32,
    pixel_ratio=2.0,
    cpu_cores=14,
    device_memory=16,
    max_touch_points=10,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) Arc(TM) Graphics, D3D11)",
    tags=["popular", "premium", "2024"],
)

HP_SPECTRE_X360_14_U7_16G = DeviceProfile(
    brand="HP",
    model="Spectre x360 14",
    config_label="Ultra7-155H/16GB",
    device_type="desktop",
    os_family="windows",
    screen_width=2880,
    screen_height=1800,
    color_depth=32,
    pixel_ratio=2.0,
    cpu_cores=16,
    device_memory=16,
    max_touch_points=10,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) Arc(TM) Graphics, D3D11)",
    tags=["popular", "premium", "2024"],
)

HP_SPECTRE_X360_14_U7_32G = DeviceProfile(
    brand="HP",
    model="Spectre x360 14",
    config_label="Ultra7-155H/32GB",
    device_type="desktop",
    os_family="windows",
    screen_width=2880,
    screen_height=1800,
    color_depth=32,
    pixel_ratio=2.0,
    cpu_cores=16,
    device_memory=32,
    max_touch_points=10,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) Arc(TM) Graphics, D3D11)",
    tags=["premium", "2024"],
)

# --- HP Envy 16 (2023-2024, 最畅销创作者笔记本) ---
# 16" 2560x1600 IPS, Intel 13th Gen H-series, Intel Arc A370M

HP_ENVY_16_I7_16G = DeviceProfile(
    brand="HP",
    model="Envy 16",
    config_label="i7-13700H/16GB",
    device_type="desktop",
    os_family="windows",
    screen_width=2560,
    screen_height=1600,
    color_depth=32,
    pixel_ratio=1.5,
    cpu_cores=14,
    device_memory=16,
    max_touch_points=10,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) Arc(TM) A370M Graphics, D3D11)",
    tags=["popular", "creator", "2023"],
)

HP_ENVY_16_I7_32G = DeviceProfile(
    brand="HP",
    model="Envy 16",
    config_label="i7-13700H/32GB",
    device_type="desktop",
    os_family="windows",
    screen_width=2560,
    screen_height=1600,
    color_depth=32,
    pixel_ratio=1.5,
    cpu_cores=14,
    device_memory=32,
    max_touch_points=10,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) Arc(TM) A370M Graphics, D3D11)",
    tags=["creator", "2023"],
)

HP_ENVY_16_I9_32G = DeviceProfile(
    brand="HP",
    model="Envy 16",
    config_label="i9-13900H/32GB",
    device_type="desktop",
    os_family="windows",
    screen_width=2560,
    screen_height=1600,
    color_depth=32,
    pixel_ratio=1.5,
    cpu_cores=14,
    device_memory=32,
    max_touch_points=10,
    platform="Win32",
    ua_template="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36",
    sec_ch_ua_platform='"Windows"',
    webgl_vendor="Google Inc. (Intel)",
    webgl_renderer="ANGLE (Intel, Intel(R) Arc(TM) A370M Graphics, D3D11)",
    tags=["creator", "pro", "2023"],
)


# ============================================================
# 设备集合 (仅桌面端)
# ============================================================

ALL_DEVICES: List[DeviceProfile] = [
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
    # HP
    HP_PAVILION_15_I5_8G, HP_PAVILION_15_I5_16G, HP_PAVILION_15_I7_16G,
    HP_SPECTRE_X360_14_U5_16G, HP_SPECTRE_X360_14_U7_16G, HP_SPECTRE_X360_14_U7_32G,
    HP_ENVY_16_I7_16G, HP_ENVY_16_I7_32G, HP_ENVY_16_I9_32G,
]

# 按品牌索引
DEVICES_BY_BRAND = {}
for _dev in ALL_DEVICES:
    _brand_key = _dev.brand.lower()
    if _brand_key not in DEVICES_BY_BRAND:
        DEVICES_BY_BRAND[_brand_key] = []
    DEVICES_BY_BRAND[_brand_key].append(_dev)

