"""
生成器模块包 - 学生信息和文档生成

导出所有生成函数
"""

from .student import (
    generate_name,
    generate_email,
    generate_birth_date,
    generate_phone_number,
    generate_address,
)

from .document import (
    generate_transcript,
    generate_student_id,
    generate_enrollment_letter,
    generate_harvard_transcript,
    add_scan_effects,
    add_document_noise,
    add_compression_artifacts,
)
