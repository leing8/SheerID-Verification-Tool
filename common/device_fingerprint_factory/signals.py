"""
指纹信号生成器

基于真实设备档案 + verificationId HMAC 种子生成浏览器指纹信号。
同一设备 + 不同 verificationId → 不同信号值 (Canvas/Audio/WebGL 哈希)

SheerID 指纹算法 (逆向自 fd.sheerid.com/learn.js):
- 哈希: MurmurHash3 x64_128, seed=31
- 分隔符: ~~~
- 输出: 32 位十六进制字符串
"""

import hashlib
import hmac
import logging
import struct

try:
    import mmh3
except ImportError:
    raise ImportError(
        "mmh3 是必需依赖，用于生成与 SheerID 一致的 MurmurHash3 指纹哈希。\n"
        "安装: pip install mmh3"
    )

logger = logging.getLogger(__name__)

# 用于 HMAC 的固定密钥 (可配置)
_HMAC_KEY = b"device-fingerprint-salt-v1"

# ============================================================
# Chrome 版本配置
# 版本号必须与 curl_cffi impersonate 对应
# curl_cffi v0.14.0 支持: chrome124, chrome130, chrome131, chrome133, chrome136, chrome145
# ============================================================

# 每个版本条目: (精确版本号, curl_cffi impersonate 名称, sec-ch-ua 字符串)
# sec-ch-ua 来源: 真实 Chrome 浏览器抓包，品牌顺序和 Not-A.Brand 格式各版本不同
CHROME_VERSION_MAP = {
    "chrome136": {
        "version": "136.0.7103.93",
        "sec_ch_ua": '"Chromium";v="136", "Google Chrome";v="136", "Not?A_Brand";v="99"',
    },
    "chrome133": {
        "version": "133.0.6943.142",
        "sec_ch_ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    },
    "chrome131": {
        "version": "131.0.6778.140",
        "sec_ch_ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    },
    "chrome130": {
        "version": "130.0.6723.117",
        "sec_ch_ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    },
    "chrome124": {
        "version": "124.0.6367.201",
        "sec_ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    },
}

# 按权重排列 (最新版本最高概率，符合真实用户分布)
# 2026-02 真实世界分布: chrome136 ~55%, chrome133 ~20%, chrome131 ~10%, chrome130 ~8%
CHROME_IMPERSONATE_KEYS = [
    "chrome136",   # 最新稳定版 — 最高概率
    "chrome136",
    "chrome136",
    "chrome136",
    "chrome133",   # 次新 — 中等概率
    "chrome131",   # 较旧 — 低概率
    "chrome130",   # 较旧 — 低概率
]

# 向后兼容: 精确版本号列表 (供外部引用)
CHROME_VERSIONS = [v["version"] for v in CHROME_VERSION_MAP.values()]


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
    """
    确定性选择 Chrome 版本。

    Returns:
        curl_cffi impersonate 键名 (如 "chrome131")
    """
    seed = _deterministic_seed(verification_id, "chrome_version")
    idx = _seed_to_int(seed, len(CHROME_IMPERSONATE_KEYS))
    selected = CHROME_IMPERSONATE_KEYS[idx]
    logger.debug("Chrome 版本选择: idx=%d/%d -> %s", idx, len(CHROME_IMPERSONATE_KEYS), selected)
    return selected


def get_chrome_full_version(impersonate_key: str) -> str:
    """获取完整 Chrome 版本号 (如 '131.0.6778.140')"""
    return CHROME_VERSION_MAP[impersonate_key]["version"]


def generate_sec_ch_ua(impersonate_key: str) -> str:
    """生成与 Chrome 版本精确匹配的 sec-ch-ua 请求头"""
    return CHROME_VERSION_MAP[impersonate_key]["sec_ch_ua"]


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


def compute_fingerprint_hash(components: list) -> str:
    """
    将所有信号组件拼接并计算指纹哈希。

    使用 MurmurHash3 x64_128 (seed=31)，与 SheerID learn.js 一致。
    分隔符: ~~~
    输出: 32 位十六进制字符串
    """
    raw = "~~~".join(str(c) for c in components)
    logger.debug("指纹哈希计算: 组件数=%d, 拼接长度=%d", len(components), len(raw))
    # MurmurHash3 x64_128, seed=31, 与 SheerID learn.js 一致
    hash_val = mmh3.hash128(raw, seed=31, x64arch=True, signed=False)
    result = f"{hash_val:032x}"
    logger.debug("指纹哈希结果: %s", result)
    return result
