"""
设备档案数据模型
定义 GPU 和设备配置的数据类
"""

from dataclasses import dataclass
from typing import List, Optional


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
