"""
文档生成模块
生成虚拟学术成绩单、学生证和收据

反检测优化：
- EXIF 元数据清理/伪造
- 文档多样性（课程、布局变体）
- 真实感噪声和纹理
- 唯一性增强防止相似度检测
"""

from .base import DocumentType, Region, get_available_document_types, get_available_regions
from .templates import default_us_template

__all__ = [
    # 枚举类型
    "DocumentType",
    "Region",
    # 函数
    "get_available_document_types",
    "get_available_regions",
    "generate_transcript",
    "generate_student_id",
    "generate_receipt",
]


def generate_transcript(first: str, last: str, school: str, dob: str, seed: str = None) -> bytes:
    """
    生成虚拟学术成绩单
    
    参数:
        first: 名
        last: 姓
        school: 学校名称
        dob: 出生日期
        seed: 随机种子（verificationId），用于确定性生成
    
    返回:
        PNG 格式的图像字节数据
    """
    return default_us_template.generate_transcript(first, last, school, dob, seed)


def generate_student_id(first: str, last: str, school: str, seed: str = None) -> bytes:
    """
    生成虚拟学生证
    
    参数:
        first: 名
        last: 姓
        school: 学校名称
        seed: 随机种子（verificationId），用于确定性生成
    
    返回:
        PNG 格式的图像字节数据
    """
    return default_us_template.generate_student_id(first, last, school, seed)


def generate_receipt(
    first: str, 
    last: str, 
    school: str, 
    seed: str = None,
    receipt_type: str = "tuition"
) -> bytes:
    """
    生成收据（学费或书店）
    
    参数:
        first: 名
        last: 姓
        school: 学校名称
        seed: 随机种子
        receipt_type: 收据类型 ("tuition" 学费, "bookstore" 书店)
    
    返回:
        PNG 格式的图像字节数据
    """
    return default_us_template.generate_receipt(first, last, school, seed, receipt_type)
