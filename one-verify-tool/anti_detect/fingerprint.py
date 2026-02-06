"""
指纹生成模块
生成各类浏览器指纹用于反检测

指纹一致性策略（高通过率模式）：
- 强制使用 verificationId 作为随机种子
- 同一个 verificationId 始终生成相同的指纹组件
- 确保整个验证流程中设备指纹保持一致
- 无降级方案：缺少 verificationId 将直接报错
"""

import hashlib
import random
import uuid

from .config import (
    RESOLUTIONS,
    TIMEZONES,
    LANGUAGES,
    WEBGL_VENDORS,
    WEBGL_RENDERERS,
)

# 平台常量（避免重复定义）
_PLATFORMS = ("Win32", "MacIntel", "Linux x86_64")


def _get_seeded_random(seed: str) -> random.Random:
    """
    获取基于种子的随机数生成器（强制要求种子）
    
    参数:
        seed: 必须提供的随机种子（verificationId）
    
    异常:
        ValueError: 如果 seed 为空
    """
    if not seed:
        raise ValueError("[指纹错误] verificationId 是必须的，无法生成一致性指纹")
    
    rng = random.Random()
    rng.seed(int(hashlib.md5(seed.encode()).hexdigest(), 16))
    return rng


def _generate_session_id(seed: str, suffix: str = "") -> str:
    """基于种子生成确定性 UUID"""
    return str(uuid.UUID(hashlib.md5(f"{seed}{suffix}".encode()).hexdigest()))


def get_fingerprint(seed: str) -> str:
    """
    生成逼真的浏览器指纹哈希（高通过率模式）
    
    参数:
        seed: verificationId（必须），确保同一验证会话中指纹一致
    """
    rng = _get_seeded_random(seed)
    
    components = [
        seed,
        str(rng.random()),
        rng.choice(RESOLUTIONS),
        str(rng.choice(TIMEZONES)),
        rng.choice(LANGUAGES).split(",")[0],
        rng.choice(_PLATFORMS),
        rng.choice(["Google Inc.", "Apple Computer, Inc.", ""]),
        str(rng.randint(2, 16)),
        str(rng.randint(4, 32)),
        str(rng.randint(0, 1)),
        _generate_session_id(seed, "_session"),
    ]
    return hashlib.md5("|".join(components).encode()).hexdigest()


def get_canvas_fingerprint(seed: str) -> str:
    """生成 Canvas 指纹哈希（高通过率模式）"""
    _get_seeded_random(seed)  # 仅用于校验 seed
    return hashlib.sha256(f"{seed}_canvas".encode()).hexdigest()[:32]


def get_webgl_fingerprint(seed: str) -> dict:
    """生成 WebGL 指纹数据（高通过率模式）"""
    rng = _get_seeded_random(seed)
    return {
        "vendor": rng.choice(WEBGL_VENDORS),
        "renderer": rng.choice(WEBGL_RENDERERS),
        "hash": hashlib.md5(f"{seed}_webgl".encode()).hexdigest(),
    }


def get_audio_fingerprint(seed: str) -> str:
    """生成音频上下文指纹（高通过率模式）"""
    rng = _get_seeded_random(seed)
    return f"{124.0 + rng.random() * 0.1:.13f}"


def get_full_fingerprint(seed: str) -> dict:
    """
    生成完整的浏览器指纹用于反检测（高通过率模式）
    
    参数:
        seed: verificationId（必须），确保同一验证会话中所有指纹一致
    """
    rng = _get_seeded_random(seed)
    width, height = rng.choice(RESOLUTIONS).split("x")

    return {
        "hash": get_fingerprint(seed),
        "canvas": get_canvas_fingerprint(seed),
        "webgl": get_webgl_fingerprint(seed),
        "audio": get_audio_fingerprint(seed),
        "screen": {
            "width": int(width),
            "height": int(height),
            "colorDepth": rng.choice([24, 32]),
            "pixelRatio": rng.choice([1, 1.25, 1.5, 2]),
        },
        "timezone": rng.choice(TIMEZONES),
        "language": rng.choice(LANGUAGES).split(",")[0],
        "platform": rng.choice(_PLATFORMS),
        "cpuCores": rng.randint(2, 16),
        "memory": rng.randint(4, 32),
        "touchSupport": rng.choice([True, False]),
        "sessionId": _generate_session_id(seed, "_full_session"),
    }
