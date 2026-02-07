"""
设备档案生成函数
根据种子生成一致的设备配置
"""

from typing import Optional

from .device_config import DEVICE_TEMPLATES, US_LANGUAGES, US_TIMEZONES
from .gpu_config import GPU_PROFILES
from .models import DeviceProfile
from ..base import get_seeded_random

# 模板权重配置（优先 Windows 主流配置，最符合学生用户）
_TEMPLATE_WEIGHTS = [
    ("windows_mainstream", 40),
    ("windows_gaming", 20),
    ("windows_office", 15),
    ("macos_pro", 10),
    ("macos_air", 10),
    ("linux_workstation", 5),
]


def _weighted_choice(rng, weights: list) -> str:
    """加权随机选择（内部函数）"""
    total = sum(w for _, w in weights)
    r = rng.randint(0, total - 1)
    cumulative = 0
    for name, weight in weights:
        cumulative += weight
        if r < cumulative:
            return name
    return weights[0][0]


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
        filtered = [(n, w) for n, w in _TEMPLATE_WEIGHTS if DEVICE_TEMPLATES[n]["os_type"] == os_type]
        template_weights = filtered if filtered else [("windows_mainstream", 100)]
    else:
        template_weights = _TEMPLATE_WEIGHTS
    
    selected_template = _weighted_choice(rng, template_weights)
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
