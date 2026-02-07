"""
Audio 指纹生成模块
模拟 AudioContext 音频处理
使用 DeviceProfile 确保采样率一致
"""

import hashlib
from typing import Optional

from .base import get_seeded_random
from .device_profile import DeviceProfile


def get_audio_fingerprint(seed: str, device_profile: Optional[DeviceProfile] = None) -> dict:
    """
    生成 AudioContext 指纹（模拟真实音频处理）
    
    真实浏览器中，Audio 指纹通过以下方式生成：
    1. 创建 AudioContext
    2. 创建 OscillatorNode 和 DynamicsCompressorNode
    3. 处理音频信号并读取浮点数据
    4. 不同的音频硬件和驱动产生微小差异
    
    参数:
        seed: verificationId（必须）
        device_profile: 统一设备档案
    
    返回:
        包含音频处理参数和结果的字典
    """
    rng = get_seeded_random(seed)

    # AudioContext 基础参数（使用设备档案配置）
    if device_profile is not None:
        sample_rate = device_profile.audio_sample_rate
    else:
        sample_rate = rng.choice([44100, 48000])

    # OscillatorNode 参数
    oscillator = {
        "type": "triangle",  # FingerprintJS 使用 triangle 波
        "frequency": 10000,
    }

    # DynamicsCompressorNode 参数
    compressor = {
        "threshold": -50,
        "knee": 40,
        "ratio": 12,
        "attack": 0.003,
        "release": 0.25,
    }

    # 模拟音频处理结果的浮点数值
    # 真实环境中，这是 AnalyserNode.getFloatFrequencyData() 的结果
    # 不同设备的音频硬件和驱动会产生 ~0.0001 级别的差异
    base_value = 124.04347527516074  # FingerprintJS 典型基准值
    noise = rng.uniform(-0.00001, 0.00001)
    audio_sum = base_value + noise

    # 模拟多个采样点的差异
    frequency_data = [
        audio_sum + rng.uniform(-0.00001, 0.00001) for _ in range(128)
    ]

    # OfflineAudioContext 渲染结果
    buffer_data = "|".join([
        seed,
        str(sample_rate),
        str(audio_sum),
        str(frequency_data[:8]),
    ])

    return {
        # AudioContext 参数
        "sampleRate": sample_rate,
        "channelCount": 2,
        "channelCountMode": "max",
        "channelInterpretation": "speakers",
        "state": "running",

        # 节点参数
        "oscillator": oscillator,
        "compressor": compressor,

        # 处理结果
        "audioSum": f"{audio_sum:.14f}",
        "frequencyData": frequency_data[:8],

        # 最终哈希
        "hash": hashlib.sha256(buffer_data.encode()).hexdigest()[:32],
    }
