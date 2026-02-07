"""
美国大学通用文档模板
作为未指定特定模板大学的默认实现
"""

from typing import List

from .base_template import UniversityTemplate
from ..base import get_seeded_random
from ..documents import (
    create_transcript_image,
    generate_transcript_bytes,
    create_student_id_image,
    generate_student_id_bytes,
    create_receipt_image,
    generate_receipt_bytes,
)


class USGenericTemplate(UniversityTemplate):
    """
    美国大学通用文档模板
    
    用于所有未指定特定模板的美国大学
    """
    
    @property
    def university_ids(self) -> List[int]:
        """通用模板支持所有大学（返回空列表）"""
        return []
    
    def generate_transcript(
        self,
        first: str,
        last: str,
        school: str,
        dob: str,
        seed: str
    ) -> bytes:
        """生成美国通用格式成绩单"""
        rng = get_seeded_random(seed)
        img = create_transcript_image(
            first=first,
            last=last,
            school=school,
            dob=dob,
            rng=rng,
            header_color=(0, 0, 0),
            accent_color=(0, 100, 0),
        )
        return generate_transcript_bytes(img, rng)
    
    def generate_student_id(
        self,
        first: str,
        last: str,
        school: str,
        seed: str
    ) -> bytes:
        """生成美国通用格式学生证"""
        rng = get_seeded_random(seed)
        img = create_student_id_image(
            first=first,
            last=last,
            school=school,
            rng=rng,
        )
        return generate_student_id_bytes(img, rng)
    
    def generate_receipt(
        self,
        first: str,
        last: str,
        school: str,
        seed: str,
        receipt_type: str = "tuition"
    ) -> bytes:
        """生成收据"""
        rng = get_seeded_random(seed)
        img = create_receipt_image(
            first=first,
            last=last,
            school=school,
            rng=rng,
            receipt_type=receipt_type,
        )
        return generate_receipt_bytes(img, rng)
    
    def supports_receipt(self) -> bool:
        """美国通用模板支持收据生成"""
        return True


# 默认模板实例
default_us_template = USGenericTemplate()
