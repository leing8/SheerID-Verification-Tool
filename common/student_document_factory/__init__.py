"""
common.student_document_factory — 学生文档工厂（学生信息生成与文档生成公共模块）

对外暴露：
  - StudentInfoFactory: 工厂类，调用 create(verification_id) 获取完整学生信息
  - StudentInfo:        工厂返回值 dataclass
  - DocumentType:       文档类型枚举
"""

from .factory import StudentInfo, StudentInfoFactory
from .universities import DocumentType

__all__ = [
    "StudentInfoFactory",
    "StudentInfo",
    "DocumentType",
]
