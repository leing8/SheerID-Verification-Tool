"""
学校模块标准接口定义

每所学校必须实现 SchoolModule 抽象基类，
封装该校专属的学生数据生成和文档生成逻辑。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class DocumentResult:
    """文档生成结果"""
    filename: str   # 上传文件名，如 "transcript.png"
    data: bytes     # PNG 字节流


class SchoolModule(ABC):
    """
    学校模块标准接口。

    每所大学实现此接口，封装：
    - 该校所需的学生数据字段（各校文档所需字段不同）
    - 该校各类文档的生成逻辑（样式、内容）
    """

    @abstractmethod
    def school_id(self) -> int:
        """返回 SheerID 机构 ID"""

    @abstractmethod
    def generate_student_data(self, verification_id: str) -> dict:
        """
        基于 verificationId 确定性生成该校所需的全部学生字段。

        必须包含的公共字段：
          first_name (str)
          last_name  (str)
          email      (str)
          birth_date (str, YYYY-MM-DD)

        各校可在此之外添加专属字段（如 school_code、gpa 等）。
        """

    @abstractmethod
    def generate_document(
        self, doc_type: str, student_data: dict, *, fetch_avatar: bool = True,
    ) -> DocumentResult:
        """
        根据文档类型生成对应文档。

        Args:
            doc_type:     DocumentType 枚举的字符串值
                          ("transcript" | "invoice" | "student_id" | "schedule")
            student_data: generate_student_data() 的返回字典
            fetch_avatar: 是否从网络获取头像（仅影响学生证）

        Returns:
            DocumentResult(filename, data)
        """
