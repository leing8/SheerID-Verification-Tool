"""
指纹生成包
生成各类浏览器指纹用于反检测

模块结构：
- base: 基础工具函数（种子随机数、哈希生成）
- canvas: Canvas 渲染指纹
- webgl: WebGL GPU 指纹
- audio: AudioContext 音频指纹
- browser: 浏览器相关指纹（字体、插件、WebRTC、Navigator）
"""

import hashlib

from .audio import get_audio_fingerprint
from .base import (
    get_seeded_random,
    generate_session_id,
    generate_deterministic_hash,
)
from .browser import (
    get_fonts_fingerprint,
    get_plugins_fingerprint,
    get_webrtc_fingerprint,
    get_navigator_fingerprint,
    get_screen_fingerprint,
    get_timezone_fingerprint,
)
from .canvas import get_canvas_fingerprint
from .webgl import get_webgl_fingerprint
from ..config import RESOLUTIONS, TIMEZONES, LANGUAGES, PLATFORMS


def get_fingerprint(seed: str) -> str:
    """
    生成浏览器指纹哈希
    
    整合所有指纹组件（包括 Canvas、WebGL、Audio 渲染结果）生成最终哈希
    
    参数:
        seed: verificationId（必须），确保同一验证会话中指纹一致
    """
    rng = get_seeded_random(seed)
    
    # 获取渲染指纹的哈希值
    canvas_data = get_canvas_fingerprint(seed)
    webgl_data = get_webgl_fingerprint(seed)
    audio_data = get_audio_fingerprint(seed)
    
    components = [
        seed,
        str(rng.random()),
        rng.choice(RESOLUTIONS),
        str(rng.choice(TIMEZONES)),
        rng.choice(LANGUAGES).split(",")[0],
        rng.choice(PLATFORMS),
        rng.choice(["Google Inc.", "Apple Computer, Inc.", ""]),
        str(rng.randint(2, 16)),  # CPU cores
        str(rng.randint(4, 32)),  # Device memory
        str(rng.randint(0, 1)),   # Touch support
        generate_session_id(seed, "_session"),
        # 整合渲染指纹哈希
        canvas_data["hash"],
        webgl_data["hash"],
        audio_data["hash"],
    ]
    return hashlib.sha256("|".join(components).encode()).hexdigest()[:32]


def get_full_fingerprint(seed: str, os_type: str = None) -> dict:
    """
    生成完整的浏览器指纹
    
    参数:
        seed: verificationId（必须），确保同一验证会话中所有指纹一致
        os_type: 操作系统类型，如为 None 则随机选择
    """
    rng = get_seeded_random(seed)
    
    # 确定操作系统类型
    if os_type is None:
        os_type = rng.choice(["windows", "macos", "linux"])
    
    # 获取渲染指纹（仅调用一次，用于 hash 计算和返回）
    canvas_data = get_canvas_fingerprint(seed)
    webgl_data = get_webgl_fingerprint(seed)
    audio_data = get_audio_fingerprint(seed)
    
    # 预计算共享值，避免重复 rng 调用
    language = rng.choice(LANGUAGES).split(",")[0]
    platform = rng.choice(PLATFORMS)
    cpu_cores = rng.randint(2, 16)
    memory = rng.randint(4, 32)
    touch_support = rng.choice([True, False])
    
    # 直接计算 hash，避免重复调用 get_fingerprint()
    components = [
        seed,
        str(rng.random()),
        rng.choice(RESOLUTIONS),
        str(rng.choice(TIMEZONES)),
        language,
        platform,
        rng.choice(["Google Inc.", "Apple Computer, Inc.", ""]),
        str(cpu_cores),
        str(memory),
        str(1 if touch_support else 0),
        generate_session_id(seed, "_session"),
        canvas_data["hash"],
        webgl_data["hash"],
        audio_data["hash"],
    ]
    fingerprint_hash = hashlib.sha256("|".join(components).encode()).hexdigest()[:32]

    return {
        "hash": fingerprint_hash,
        "canvas": canvas_data,
        "webgl": webgl_data,
        "audio": audio_data,
        "fonts": get_fonts_fingerprint(seed, os_type),
        "plugins": get_plugins_fingerprint(seed),
        "webrtc": get_webrtc_fingerprint(seed),
        "navigator": get_navigator_fingerprint(seed, os_type),
        "screen": get_screen_fingerprint(seed),
        "timezone": get_timezone_fingerprint(seed),
        "language": language,
        "platform": platform,
        "cpuCores": cpu_cores,
        "memory": memory,
        "touchSupport": touch_support,
        "sessionId": generate_session_id(seed, "_full_session"),
        "osType": os_type,
    }


__all__ = [
    # 基础函数
    "get_seeded_random",
    "generate_session_id",
    "generate_deterministic_hash",
    # 渲染指纹
    "get_fingerprint",
    "get_canvas_fingerprint",
    "get_webgl_fingerprint",
    "get_audio_fingerprint",
    # 浏览器指纹
    "get_fonts_fingerprint",
    "get_plugins_fingerprint",
    "get_webrtc_fingerprint",
    "get_navigator_fingerprint",
    "get_screen_fingerprint",
    "get_timezone_fingerprint",
    # 完整指纹
    "get_full_fingerprint",
]
