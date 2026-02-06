"""
指纹生成基础模块
提供种子随机数生成器和哈希工具函数
"""

import hashlib
import random
import uuid


def get_seeded_random(seed: str) -> random.Random:
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
    # 使用 SHA-256 提高哈希质量
    rng.seed(int(hashlib.sha256(seed.encode()).hexdigest(), 16) % (2 ** 32))
    return rng


def generate_session_id(seed: str, suffix: str = "") -> str:
    """基于种子生成确定性 UUID"""
    return str(uuid.UUID(hashlib.md5(f"{seed}{suffix}".encode()).hexdigest()))


def generate_deterministic_hash(seed: str, suffix: str = "") -> str:
    """基于种子生成确定性 SHA-256 哈希（取前32位）"""
    return hashlib.sha256(f"{seed}{suffix}".encode()).hexdigest()[:32]
