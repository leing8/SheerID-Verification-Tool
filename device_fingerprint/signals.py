"""
指纹信号生成器

基于真实设备档案 + verificationId HMAC 种子生成 15 项浏览器指纹信号。
同一设备 + 不同 verificationId → 不同信号值 (Canvas/Audio/WebGL 哈希)
"""

import hashlib
import hmac
import struct

# 用于 HMAC 的固定密钥 (可配置)
_HMAC_KEY = b"device-fingerprint-salt-v1"

# Chrome 版本 (保持较新)
CHROME_VERSIONS = [
    "131.0.0.0",
    "130.0.0.0",
    "129.0.0.0",
    "128.0.0.0",
]


def _deterministic_seed(verification_id: str, component: str) -> bytes:
    """
    从 verificationId + 组件名生成确定性种子。
    同一组合始终返回相同值。
    """
    msg = f"{verification_id}:{component}".encode("utf-8")
    return hmac.new(_HMAC_KEY, msg, hashlib.sha256).digest()


def _seed_to_int(seed: bytes, max_val: int) -> int:
    """将种子转为 [0, max_val) 范围内的整数"""
    value = struct.unpack(">I", seed[:4])[0]
    return value % max_val


def _seed_to_float(seed: bytes, low: float, high: float) -> float:
    """将种子转为 [low, high] 范围内的浮点数"""
    value = struct.unpack(">I", seed[:4])[0]
    ratio = value / 0xFFFFFFFF
    return low + ratio * (high - low)


def select_chrome_version(verification_id: str) -> str:
    """确定性选择 Chrome 版本"""
    seed = _deterministic_seed(verification_id, "chrome_version")
    idx = _seed_to_int(seed, len(CHROME_VERSIONS))
    return CHROME_VERSIONS[idx]


def generate_canvas_hash(verification_id: str, device_key: str) -> str:
    """
    生成 Canvas 指纹哈希。

    同一 verificationId + 同一设备 → 相同哈希
    不同 verificationId + 同一设备 → 不同哈希
    """
    seed = _deterministic_seed(verification_id, f"canvas:{device_key}")
    return hashlib.sha256(seed).hexdigest()[:32]


def generate_audio_fingerprint(verification_id: str, device_key: str) -> str:
    """
    生成 AudioContext 指纹值。

    真实浏览器中此值在 124.04 ~ 124.08 范围内。
    """
    seed = _deterministic_seed(verification_id, f"audio:{device_key}")
    value = _seed_to_float(seed, 124.04347527516074, 124.08075396683452)
    return f"{value:.13f}"


def generate_webgl_hash(verification_id: str, device_key: str) -> str:
    """生成 WebGL 扩展/参数的哈希"""
    seed = _deterministic_seed(verification_id, f"webgl:{device_key}")
    return hashlib.md5(seed).hexdigest()


def generate_font_hash(verification_id: str, os_family: str) -> str:
    """基于操作系统生成字体列表哈希"""
    seed = _deterministic_seed(verification_id, f"fonts:{os_family}")
    return hashlib.md5(seed).hexdigest()[:16]


def generate_session_id(verification_id: str) -> str:
    """从 verificationId 确定性生成唯一会话标识"""
    seed = _deterministic_seed(verification_id, "session_id")
    # 格式化为 UUID 形式
    hex_str = seed.hex()[:32]
    return f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:32]}"


def generate_sec_ch_ua(chrome_version: str) -> str:
    """生成与 Chrome 版本一致的 sec-ch-ua 请求头"""
    major = chrome_version.split(".")[0]
    return f'"Chromium";v="{major}", "Google Chrome";v="{major}", "Not-A.Brand";v="99"'


def compute_fingerprint_hash(components: list) -> str:
    """将所有信号组件拼接并计算 MD5 哈希"""
    raw = "|".join(str(c) for c in components)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()
