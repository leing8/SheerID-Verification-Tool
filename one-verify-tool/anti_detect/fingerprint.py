"""
指纹生成模块
生成各类浏览器指纹用于反检测
"""

import hashlib
import random
import time
import uuid

from .config import (
    RESOLUTIONS,
    TIMEZONES,
    LANGUAGES,
    WEBGL_VENDORS,
    WEBGL_RENDERERS,
)


def get_fingerprint() -> str:
    """生成逼真的浏览器指纹哈希"""
    components = [
        str(int(time.time() * 1000)),
        str(random.random()),
        random.choice(RESOLUTIONS),
        str(random.choice(TIMEZONES)),
        random.choice(LANGUAGES).split(",")[0],
        random.choice(["Win32", "MacIntel", "Linux x86_64"]),
        random.choice(["Google Inc.", "Apple Computer, Inc.", ""]),
        str(random.randint(2, 16)),  # CPU 核心数
        str(random.randint(4, 32)),  # 设备内存
        str(random.randint(0, 1)),  # 触摸屏支持
        str(uuid.uuid4()),  # 会话 ID
    ]
    return hashlib.md5("|".join(components).encode()).hexdigest()


def get_canvas_fingerprint() -> str:
    """生成逼真的 Canvas 指纹哈希"""
    # 模拟 canvas toDataURL 哈希
    seed = str(time.time()) + str(random.random())
    return hashlib.sha256(seed.encode()).hexdigest()[:32]


def get_webgl_fingerprint() -> dict:
    """生成 WebGL 指纹数据"""
    return {
        "vendor": random.choice(WEBGL_VENDORS),
        "renderer": random.choice(WEBGL_RENDERERS),
        "hash": hashlib.md5(str(random.random()).encode()).hexdigest(),
    }


def get_audio_fingerprint() -> str:
    """生成音频上下文指纹"""
    # 模拟 AudioContext 指纹
    return str(random.uniform(124.0, 124.1))[:15]


def get_full_fingerprint() -> dict:
    """生成完整的浏览器指纹用于反检测"""
    screen = random.choice(RESOLUTIONS)
    width, height = screen.split("x")

    return {
        "hash": get_fingerprint(),
        "canvas": get_canvas_fingerprint(),
        "webgl": get_webgl_fingerprint(),
        "audio": get_audio_fingerprint(),
        "screen": {
            "width": int(width),
            "height": int(height),
            "colorDepth": random.choice([24, 32]),
            "pixelRatio": random.choice([1, 1.25, 1.5, 2]),
        },
        "timezone": random.choice(TIMEZONES),
        "language": random.choice(LANGUAGES).split(",")[0],
        "platform": random.choice(["Win32", "MacIntel", "Linux x86_64"]),
        "cpuCores": random.randint(2, 16),
        "memory": random.randint(4, 32),
        "touchSupport": random.choice([True, False]),
        "sessionId": str(uuid.uuid4()),
    }
