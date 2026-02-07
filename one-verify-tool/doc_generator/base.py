"""
文档生成模块基础定义
包含文档类型枚举和核心工具函数
"""

import hashlib
import random
from enum import Enum
from typing import List


class DocumentType(Enum):
    """文档类型枚举"""
    TRANSCRIPT = "transcript"       # 学术成绩单
    STUDENT_ID = "student_id"       # 学生证
    RECEIPT = "receipt"             # 收据（学费/书本费）


class Region(Enum):
    """支持的地区枚举"""
    US = "us"           # 美国
    CA = "ca"           # 加拿大
    UK = "uk"           # 英国
    AU = "au"           # 澳大利亚
    IN = "in"           # 印度


def get_seeded_random(seed: str) -> random.Random:
    """
    获取基于种子的随机数生成器（强制要求种子）
    
    注意: 此函数与 anti_detect.fingerprint.base.get_seeded_random 功能相同，
    为避免导入链问题（anti_detect 依赖 numpy）而在此独立实现。
    
    参数:
        seed: 必须提供的随机种子（verificationId）
    
    异常:
        ValueError: 如果 seed 为空
    """
    if not seed:
        raise ValueError("[指纹错误] verificationId 是必须的，无法生成一致性指纹")

    rng = random.Random()
    rng.seed(int(hashlib.sha256(seed.encode()).hexdigest(), 16) % (2 ** 32))
    return rng


def get_available_document_types() -> List[DocumentType]:
    """获取所有可用的文档类型"""
    return list(DocumentType)


def get_available_regions() -> List[Region]:
    """获取所有可用的地区"""
    return list(Region)
