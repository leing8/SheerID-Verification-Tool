"""
哈佛大学学校模块

实现 SchoolModule 接口，作为哈佛专属逻辑的入口：
- 学生数据生成 → student_data.build()
- 文档生成 → documents 子包（transcript / invoice / student_id）

依赖方向：module → student_data（数据层）
          module → documents（渲染层）
"""

from .documents import generate_invoice, generate_student_id_card, generate_transcript
from .student_data import HarvardStudentData, build as _build_student
from ...interfaces import DocumentResult, SchoolModule
from ...universities import DocumentType

# 文档类型 → (生成函数, 输出文件名)
_DOC_GENERATORS = {
    DocumentType.TRANSCRIPT: (generate_transcript, "transcript.png"),
    DocumentType.INVOICE:    (generate_invoice,    "invoice.png"),
    DocumentType.STUDENT_ID: (generate_student_id_card, "student_id.png"),
}


class HarvardModule(SchoolModule):
    """哈佛大学模块，支持：transcript / invoice / student_id"""

    def school_id(self) -> int:
        return 1426

    def generate_student_data(
        self, verification_id: str, program: str = ""
    ) -> HarvardStudentData:
        """基于 verificationId + program 确定性生成哈佛学生数据。"""
        return _build_student(verification_id, program)

    def generate_document(
        self, doc_type: str, student_data: HarvardStudentData
    ) -> DocumentResult:
        """根据文档类型生成哈佛专属样式文档。"""
        entry = _DOC_GENERATORS.get(doc_type)
        if entry is None:
            raise ValueError(f"哈佛模块不支持文档类型: {doc_type!r}")

        generator, filename = entry
        data = generator(student_data)
        return DocumentResult(filename=filename, data=data)
