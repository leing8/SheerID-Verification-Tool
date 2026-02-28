"""
哈佛文档生成子包

提供 3 种文档的生成函数，外部通过此 __init__.py 统一导入：
    from .documents import generate_transcript, generate_invoice, generate_student_id_card
"""

from .invoice import generate_invoice
from .student_id import generate_student_id_card
from .transcript import generate_transcript

__all__ = [
    "generate_transcript",
    "generate_invoice",
    "generate_student_id_card",
]
