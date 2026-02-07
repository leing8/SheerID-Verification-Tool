"""
Canvas 指纹生成模块
模拟真实浏览器 Canvas 渲染
使用 DeviceProfile 确保配置一致
"""

import hashlib
from typing import Optional

from .base import get_seeded_random, generate_deterministic_hash
from .device_profile import DeviceProfile


def get_canvas_fingerprint(seed: str, device_profile: Optional[DeviceProfile] = None) -> dict:
    """
    生成 Canvas 指纹（模拟真实浏览器渲染）
    
    真实浏览器中，Canvas 指纹通过以下方式生成：
    1. 绘制特定文本和图形
    2. 读取像素数据
    3. 由于字体渲染、抗锯齿、GPU 差异等，不同设备产生不同结果
    
    参数:
        seed: verificationId（必须）
        device_profile: 统一设备档案
    
    返回:
        包含渲染数据和哈希的字典
    """
    rng = get_seeded_random(seed)

    # 根据操作系统选择字体
    if device_profile is not None:
        os_type = device_profile.os_type
        if os_type == "macos":
            font_choices = [
                "14px 'Helvetica Neue'",
                "14px -apple-system",
                "14px San Francisco",
                "bold 14px Helvetica",
            ]
        else:
            font_choices = [
                "14px Arial",
                "14px 'Arial'",
                "14px Arial, sans-serif",
                "bold 14px Arial",
            ]
    else:
        font_choices = [
            "14px Arial",
            "14px 'Arial'",
            "14px Arial, sans-serif",
            "bold 14px Arial",
        ]

    # 模拟 Canvas 渲染参数（这些会影响最终像素数据）
    # 真实浏览器中这些差异来自：字体渲染引擎、抗锯齿算法、GPU 驱动
    canvas_params = {
        # 文本渲染参数
        "textBaseline": rng.choice(["alphabetic", "top", "middle"]),
        "font": rng.choice(font_choices),
        # 抗锯齿相关（不同浏览器/GPU 有差异）
        "imageSmoothingEnabled": rng.choice([True, False]),
        "imageSmoothingQuality": rng.choice(["low", "medium", "high"]),
        # 模拟像素级差异（真实环境中来自硬件差异）
        "pixelNoise": [rng.randint(0, 255) for _ in range(16)],
        # 渲染文本（FingerprintJS 常用测试文本）
        "testText": "Cwm fjordbank glyphs vext quiz, 😃",
        # 颜色和样式
        "fillStyle": f"rgba({rng.randint(0, 255)},{rng.randint(0, 255)},{rng.randint(0, 255)},0.5)",
        "shadowBlur": rng.uniform(0, 2),
        "shadowColor": f"rgba(0,0,0,{rng.uniform(0.1, 0.3):.2f})",
    }

    # 生成模拟的像素数据哈希（真实环境中是 toDataURL() 的结果）
    pixel_data = "|".join([
        seed,
        canvas_params["font"],
        canvas_params["testText"],
        str(canvas_params["pixelNoise"]),
        canvas_params["fillStyle"],
    ])

    return {
        "params": canvas_params,
        "hash": hashlib.sha256(pixel_data.encode()).hexdigest()[:32],
        # 模拟 winding 测试（用于检测 Canvas 是否支持特定渲染模式）
        "winding": rng.choice([True, False]),
        # 几何图形渲染结果
        "geometry": generate_deterministic_hash(seed, "_canvas_geometry"),
    }
