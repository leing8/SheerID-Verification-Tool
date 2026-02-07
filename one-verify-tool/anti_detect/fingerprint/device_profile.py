"""
统一设备档案生成模块
确保所有设备指纹属性逻辑一致

根据 SheerID 欺诈检测技术优化：
- GPU 型号与参数精确匹配
- 操作系统与字体/分辨率一致
- 时区与语言地区一致
- CPU/内存配置合理
"""

from dataclasses import dataclass
from typing import List, Optional

from .base import get_seeded_random


@dataclass
class GPUProfile:
    """GPU 配置档案"""
    vendor: str
    renderer: str
    # WebGL 参数
    max_texture_size: int
    max_viewport_dims: List[int]
    max_renderbuffer_size: int
    max_cube_map_texture_size: int
    max_texture_image_units: int
    max_vertex_texture_image_units: int
    max_combined_texture_image_units: int
    max_vertex_attribs: int
    max_vertex_uniform_vectors: int
    max_fragment_uniform_vectors: int
    max_varying_vectors: int
    max_samples: int
    # 着色器精度
    high_float_precision: int = 23
    high_int_precision: int = 16


@dataclass
class DeviceProfile:
    """统一设备档案"""
    # 操作系统
    os_type: str  # windows, macos, linux
    platform: str  # Win32, MacIntel, Linux x86_64
    
    # GPU 配置
    gpu: GPUProfile
    
    # 硬件配置
    cpu_cores: int
    device_memory: int  # GB
    
    # 屏幕配置
    screen_width: int
    screen_height: int
    color_depth: int
    pixel_ratio: float
    
    # 区域设置（针对美国大学优化）
    timezone_offset: int  # 分钟
    language: str
    languages: List[str]
    
    # 音频配置
    audio_sample_rate: int
    
    # 触摸支持
    max_touch_points: int
    
    # Navigator 属性
    vendor: str = "Google Inc."
    do_not_track: Optional[str] = None


# ============ GPU 配置库 ============
# 真实设备参数，确保 WebGL 指纹与 GPU 型号完全匹配

GPU_PROFILES = {
    # NVIDIA RTX 40 系列
    "rtx_4090": GPUProfile(
        vendor="Google Inc. (NVIDIA)",
        renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 4090 (0x00002684) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        max_texture_size=32768,
        max_viewport_dims=[32768, 32768],
        max_renderbuffer_size=32768,
        max_cube_map_texture_size=32768,
        max_texture_image_units=32,
        max_vertex_texture_image_units=32,
        max_combined_texture_image_units=192,
        max_vertex_attribs=16,
        max_vertex_uniform_vectors=4096,
        max_fragment_uniform_vectors=4096,
        max_varying_vectors=31,
        max_samples=16,
        high_float_precision=23,
        high_int_precision=16,
    ),
    "rtx_4080": GPUProfile(
        vendor="Google Inc. (NVIDIA)",
        renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 4080 (0x00002704) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        max_texture_size=32768,
        max_viewport_dims=[32768, 32768],
        max_renderbuffer_size=32768,
        max_cube_map_texture_size=32768,
        max_texture_image_units=32,
        max_vertex_texture_image_units=32,
        max_combined_texture_image_units=192,
        max_vertex_attribs=16,
        max_vertex_uniform_vectors=4096,
        max_fragment_uniform_vectors=4096,
        max_varying_vectors=31,
        max_samples=16,
    ),
    "rtx_4070_ti": GPUProfile(
        vendor="Google Inc. (NVIDIA)",
        renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Ti (0x00002782) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        max_texture_size=32768,
        max_viewport_dims=[32768, 32768],
        max_renderbuffer_size=32768,
        max_cube_map_texture_size=32768,
        max_texture_image_units=32,
        max_vertex_texture_image_units=32,
        max_combined_texture_image_units=192,
        max_vertex_attribs=16,
        max_vertex_uniform_vectors=4096,
        max_fragment_uniform_vectors=4096,
        max_varying_vectors=31,
        max_samples=16,
    ),
    "rtx_4060": GPUProfile(
        vendor="Google Inc. (NVIDIA)",
        renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 4060 (0x00002882) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        max_texture_size=32768,
        max_viewport_dims=[32768, 32768],
        max_renderbuffer_size=16384,
        max_cube_map_texture_size=32768,
        max_texture_image_units=32,
        max_vertex_texture_image_units=32,
        max_combined_texture_image_units=192,
        max_vertex_attribs=16,
        max_vertex_uniform_vectors=4096,
        max_fragment_uniform_vectors=4096,
        max_varying_vectors=31,
        max_samples=16,
    ),
    # NVIDIA RTX 30 系列
    "rtx_3080": GPUProfile(
        vendor="Google Inc. (NVIDIA)",
        renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 (0x00002206) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        max_texture_size=32768,
        max_viewport_dims=[32768, 32768],
        max_renderbuffer_size=32768,
        max_cube_map_texture_size=32768,
        max_texture_image_units=32,
        max_vertex_texture_image_units=32,
        max_combined_texture_image_units=192,
        max_vertex_attribs=16,
        max_vertex_uniform_vectors=4096,
        max_fragment_uniform_vectors=4096,
        max_varying_vectors=31,
        max_samples=16,
    ),
    "rtx_3070": GPUProfile(
        vendor="Google Inc. (NVIDIA)",
        renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 (0x00002484) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        max_texture_size=32768,
        max_viewport_dims=[32768, 32768],
        max_renderbuffer_size=16384,
        max_cube_map_texture_size=32768,
        max_texture_image_units=32,
        max_vertex_texture_image_units=32,
        max_combined_texture_image_units=192,
        max_vertex_attribs=16,
        max_vertex_uniform_vectors=4096,
        max_fragment_uniform_vectors=4096,
        max_varying_vectors=31,
        max_samples=16,
    ),
    "rtx_3060": GPUProfile(
        vendor="Google Inc. (NVIDIA)",
        renderer="ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 (0x00002503) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        max_texture_size=16384,
        max_viewport_dims=[32768, 32768],
        max_renderbuffer_size=16384,
        max_cube_map_texture_size=16384,
        max_texture_image_units=32,
        max_vertex_texture_image_units=32,
        max_combined_texture_image_units=192,
        max_vertex_attribs=16,
        max_vertex_uniform_vectors=4096,
        max_fragment_uniform_vectors=4096,
        max_varying_vectors=31,
        max_samples=8,
    ),
    # Intel 集成显卡
    "intel_uhd_770": GPUProfile(
        vendor="Google Inc. (Intel)",
        renderer="ANGLE (Intel, Intel(R) UHD Graphics 770 (0x00004680) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        max_texture_size=16384,
        max_viewport_dims=[16384, 16384],
        max_renderbuffer_size=16384,
        max_cube_map_texture_size=16384,
        max_texture_image_units=16,
        max_vertex_texture_image_units=16,
        max_combined_texture_image_units=80,
        max_vertex_attribs=16,
        max_vertex_uniform_vectors=4096,
        max_fragment_uniform_vectors=4096,
        max_varying_vectors=31,
        max_samples=8,
    ),
    "intel_iris_xe": GPUProfile(
        vendor="Google Inc. (Intel)",
        renderer="ANGLE (Intel, Intel(R) Iris Xe Graphics (0x00009A49) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        max_texture_size=16384,
        max_viewport_dims=[16384, 16384],
        max_renderbuffer_size=16384,
        max_cube_map_texture_size=16384,
        max_texture_image_units=16,
        max_vertex_texture_image_units=16,
        max_combined_texture_image_units=80,
        max_vertex_attribs=16,
        max_vertex_uniform_vectors=4096,
        max_fragment_uniform_vectors=4096,
        max_varying_vectors=31,
        max_samples=8,
    ),
    "intel_uhd_630": GPUProfile(
        vendor="Google Inc. (Intel)",
        renderer="ANGLE (Intel, Intel(R) UHD Graphics 630 (0x00003E92) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        max_texture_size=16384,
        max_viewport_dims=[16384, 16384],
        max_renderbuffer_size=16384,
        max_cube_map_texture_size=16384,
        max_texture_image_units=16,
        max_vertex_texture_image_units=16,
        max_combined_texture_image_units=48,
        max_vertex_attribs=16,
        max_vertex_uniform_vectors=1024,
        max_fragment_uniform_vectors=1024,
        max_varying_vectors=15,
        max_samples=4,
    ),
    # Apple Silicon（Mac 平台专用）
    "apple_m3": GPUProfile(
        vendor="Google Inc. (Apple)",
        renderer="ANGLE (Apple, Apple M3, OpenGL 4.1)",
        max_texture_size=16384,
        max_viewport_dims=[16384, 16384],
        max_renderbuffer_size=16384,
        max_cube_map_texture_size=16384,
        max_texture_image_units=16,
        max_vertex_texture_image_units=16,
        max_combined_texture_image_units=80,
        max_vertex_attribs=16,
        max_vertex_uniform_vectors=4096,
        max_fragment_uniform_vectors=4096,
        max_varying_vectors=31,
        max_samples=8,
    ),
    "apple_m2": GPUProfile(
        vendor="Google Inc. (Apple)",
        renderer="ANGLE (Apple, Apple M2, OpenGL 4.1)",
        max_texture_size=16384,
        max_viewport_dims=[16384, 16384],
        max_renderbuffer_size=16384,
        max_cube_map_texture_size=16384,
        max_texture_image_units=16,
        max_vertex_texture_image_units=16,
        max_combined_texture_image_units=80,
        max_vertex_attribs=16,
        max_vertex_uniform_vectors=4096,
        max_fragment_uniform_vectors=4096,
        max_varying_vectors=31,
        max_samples=8,
    ),
    "apple_m1": GPUProfile(
        vendor="Google Inc. (Apple)",
        renderer="ANGLE (Apple, Apple M1, OpenGL 4.1)",
        max_texture_size=16384,
        max_viewport_dims=[16384, 16384],
        max_renderbuffer_size=16384,
        max_cube_map_texture_size=16384,
        max_texture_image_units=16,
        max_vertex_texture_image_units=16,
        max_combined_texture_image_units=80,
        max_vertex_attribs=16,
        max_vertex_uniform_vectors=4096,
        max_fragment_uniform_vectors=4096,
        max_varying_vectors=31,
        max_samples=8,
    ),
    # AMD 显卡
    "amd_rx_6800_xt": GPUProfile(
        vendor="Google Inc. (AMD)",
        renderer="ANGLE (AMD, AMD Radeon RX 6800 XT (0x000073BF) Direct3D11 vs_5_0 ps_5_0, D3D11)",
        max_texture_size=16384,
        max_viewport_dims=[16384, 16384],
        max_renderbuffer_size=16384,
        max_cube_map_texture_size=16384,
        max_texture_image_units=32,
        max_vertex_texture_image_units=16,
        max_combined_texture_image_units=80,
        max_vertex_attribs=16,
        max_vertex_uniform_vectors=4096,
        max_fragment_uniform_vectors=4096,
        max_varying_vectors=31,
        max_samples=8,
    ),
}

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


def generate_device_profile(seed: str, prefer_us: bool = True, os_type: Optional[str] = None) -> DeviceProfile:
    """
    生成统一的设备档案
    
    参数:
        seed: verificationId，确保同一验证会话中设备配置一致
        prefer_us: 是否优先使用美国配置（用于美国大学验证）
        os_type: 指定操作系统类型（windows/macos/linux），为 None 时随机选择
    
    返回:
        DeviceProfile 实例，包含完整的一致设备配置
    """
    rng = get_seeded_random(seed)
    
    # 根据 os_type 筛选可用模板
    if os_type:
        os_templates = [(name, w) for name, w in [
            ("windows_mainstream", 40),
            ("windows_gaming", 20),
            ("windows_office", 15),
            ("macos_pro", 10),
            ("macos_air", 10),
            ("linux_workstation", 5),
        ] if DEVICE_TEMPLATES[name]["os_type"] == os_type]
        template_weights = os_templates if os_templates else [("windows_mainstream", 100)]
    else:
        # 选择设备模板（优先 Windows 主流配置，最符合学生用户）
        template_weights = [
            ("windows_mainstream", 40),
            ("windows_gaming", 20),
            ("windows_office", 15),
            ("macos_pro", 10),
            ("macos_air", 10),
            ("linux_workstation", 5),
        ]
    
    # 加权随机选择
    total_weight = sum(w for _, w in template_weights)
    r = rng.randint(0, total_weight - 1)
    cumulative = 0
    selected_template = template_weights[0][0]
    for name, weight in template_weights:
        cumulative += weight
        if r < cumulative:
            selected_template = name
            break
    
    template = DEVICE_TEMPLATES[selected_template]
    
    # 选择 GPU
    gpu_key = rng.choice(template["gpu_options"])
    gpu = GPU_PROFILES[gpu_key]
    
    # 选择硬件配置（确保与 GPU 类型一致）
    min_cores, max_cores = template["cpu_cores_range"]
    min_mem, max_mem = template["memory_range"]
    cpu_cores = rng.randint(min_cores, max_cores)
    # 基于模板范围筛选有效内存选项
    memory_options = [m for m in [8, 16, 32] if min_mem <= m <= max_mem]
    device_memory = rng.choice(memory_options) if memory_options else min_mem
    
    # 选择分辨率
    resolution = rng.choice(template["resolutions"])
    width, height = map(int, resolution.split("x"))
    pixel_ratio = rng.choice(template["pixel_ratios"])
    
    # 选择区域配置
    if prefer_us:
        timezone_offset = rng.choice(US_TIMEZONES)
        language = rng.choice(US_LANGUAGES)
        languages = ["en-US", "en"]
    else:
        timezone_offset = rng.choice([-480, -420, -360, -300, 0, 60, 120])
        language = "en-US"
        languages = ["en-US", "en"]
    
    # 音频采样率
    audio_sample_rate = rng.choice([44100, 48000])
    
    # 触摸支持（桌面设备通常为 0）
    max_touch_points = 0
    
    # DNT 设置
    do_not_track = rng.choice([None, "1", None, None])  # 大多数用户不设置
    
    return DeviceProfile(
        os_type=template["os_type"],
        platform=template["platform"],
        gpu=gpu,
        cpu_cores=cpu_cores,
        device_memory=device_memory,
        screen_width=width,
        screen_height=height,
        color_depth=24,
        pixel_ratio=pixel_ratio,
        timezone_offset=timezone_offset,
        language=language,
        languages=languages,
        audio_sample_rate=audio_sample_rate,
        max_touch_points=max_touch_points,
        do_not_track=do_not_track,
    )
