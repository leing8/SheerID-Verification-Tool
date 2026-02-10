"""
文档类型模块导出
"""

from .avatar import (
    fetch_random_avatar,
    create_placeholder_avatar,
)
from .receipt import (
    create_receipt_image,
    generate_receipt_bytes,
    generate_receipt_items,
)
from .student_id import (
    create_student_id_image,
    generate_student_id_bytes,
)
from .transcript import (
    create_transcript_image,
    generate_transcript_bytes,
    generate_unique_courses,
    calculate_gpa,
    get_current_semester,
)

__all__ = [
    # 头像
    "fetch_random_avatar",
    "create_placeholder_avatar",
    # 成绩单
    "create_transcript_image",
    "generate_transcript_bytes",
    "generate_unique_courses",
    "calculate_gpa",
    "get_current_semester",
    # 学生证
    "create_student_id_image",
    "generate_student_id_bytes",
    # 收据
    "create_receipt_image",
    "generate_receipt_bytes",
    "generate_receipt_items",
]

