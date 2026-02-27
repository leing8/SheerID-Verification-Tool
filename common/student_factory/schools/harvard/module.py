"""
哈佛大学学校模块

实现 SchoolModule 接口，封装哈佛专属的：
- 学生数据生成（HarvardStudentData）
- 文档生成（学生证/成绩单/发票）
"""

from . import documents as _docs
from .student_data import HarvardStudentData, build as _build_student
from ...interfaces import DocumentResult, SchoolModule
from ...universities import DocumentType


class HarvardModule(SchoolModule):
    """哈佛大学模块，支持：transcript / invoice / student_id"""

    def school_id(self) -> int:
        return 1426

    def generate_student_data(self, verification_id: str, program: str = "") -> HarvardStudentData:
        """
        基于 verificationId + program 确定性生成哈佛学生数据。
        program 由工厂从 universities.py 的专业列表中选定后传入。
        """
        return _build_student(verification_id, program)

    def generate_document(self, doc_type: str, student_data: HarvardStudentData) -> DocumentResult:
        """
        根据文档类型生成哈佛专属样式文档。

        Args:
            doc_type:     DocumentType 枚举字符串值
            student_data: HarvardStudentData 实例
        """
        if doc_type == DocumentType.TRANSCRIPT:
            data = _docs.generate_transcript(student_data)
            return DocumentResult(filename="transcript.png", data=data)

        elif doc_type == DocumentType.INVOICE:
            data = _docs.generate_invoice(student_data)
            return DocumentResult(filename="invoice.png", data=data)

        elif doc_type == DocumentType.STUDENT_ID:
            data = _docs.generate_student_id_card(student_data)
            return DocumentResult(filename="student_id.png", data=data)

        else:
            raise ValueError(f"Harvard module does not support doc_type: {doc_type!r}")
