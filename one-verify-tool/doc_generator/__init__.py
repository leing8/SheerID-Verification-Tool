"""
文档生成模块
生成虚拟学术成绩单、学生证和收据

反检测优化：
- EXIF 元数据清理/伪造
- 文档多样性（课程、布局变体）
- 真实感噪声和纹理
- 唯一性增强防止相似度检测
"""

from typing import List, Tuple

from .base import DocumentType, Region, get_available_document_types, get_available_regions
from .templates import default_us_template, harvard_template

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
    "generate_documents",
    "get_mime_type",
]

# ============ 文档类型到文件名的映射 ============
_DOC_FILENAMES = {
    "transcript": "transcript.png",
    "student_id": "student_card.png",
    "receipt": "tuition_receipt.png",
}


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


def generate_documents(
    doc_types: List[str],
    template: str,
    first: str,
    last: str,
    school: str,
    dob: str,
    seed: str = None,
) -> List[Tuple[str, bytes]]:
    """
    根据大学配置批量生成所有支持的文档

    根据 template 参数自动路由到对应模板（Harvard 或通用）。
    SheerID 审核要求文档包含 全名 + 学校名 + 当前日期，
    上传多种文档（成绩单+学生证）可互补信息提高通过率。

    参数:
        doc_types: 文档类型列表（如 ["transcript", "student_id", "receipt"]）
        template: 模板名称（"harvard" 使用 Harvard 专用模板，其他使用通用模板）
        first: 名
        last: 姓
        school: 学校名称
        dob: 出生日期
        seed: 随机种子（verificationId）

    返回:
        [(文件名, 文件字节数据), ...] 列表
    """
    is_harvard = template == "harvard"
    docs = []

    for doc_type in doc_types:
        filename = _DOC_FILENAMES.get(doc_type)
        if not filename:
            continue

        if doc_type == "transcript":
            if is_harvard:
                data = harvard_template.generate_transcript(first, last, school, dob, seed)
            else:
                data = default_us_template.generate_transcript(first, last, school, dob, seed)

        elif doc_type == "student_id":
            if is_harvard:
                data = harvard_template.generate_student_id(first, last, school, seed)
            else:
                data = default_us_template.generate_student_id(first, last, school, seed)

        elif doc_type == "receipt":
            # 收据只有通用模板支持
            data = default_us_template.generate_receipt(first, last, school, seed)

        else:
            continue

        docs.append((filename, data))

    return docs


def get_mime_type(filename: str) -> str:
    """
    根据文件扩展名获取 MIME 类型

    SheerID 支持的文件格式: jpg, jpeg, png, pdf, gif（最大 10MB）

    参数:
        filename: 文件名

    返回:
        MIME 类型字符串
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
    return {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "pdf": "application/pdf",
        "gif": "image/gif",
    }.get(ext, "image/png")

