"""
设备档案模块
提供统一的设备配置生成功能

模块结构：
- models: 数据类定义 (GPUProfile, DeviceProfile)
- gpu_config: GPU 配置数据 (GPU_PROFILES)
- device_config: 设备模板和区域配置 (DEVICE_TEMPLATES, US_TIMEZONES, US_LANGUAGES)
- generator: 设备档案生成函数 (generate_device_profile)
"""

from .device_config import DEVICE_TEMPLATES, US_LANGUAGES, US_TIMEZONES
from .generator import generate_device_profile
from .gpu_config import GPU_PROFILES
from .models import DeviceProfile, GPUProfile

__all__ = [
    # 数据类
    "GPUProfile",
    "DeviceProfile",
    # 配置数据
    "GPU_PROFILES",
    "DEVICE_TEMPLATES",
    "US_TIMEZONES",
    "US_LANGUAGES",
    # 生成函数
    "generate_device_profile",
]
