"""模拟 verifier.py 调用链的集成测试

验证 student_document_factory 生成的学生信息和文档
可以正确用于 verifier.py 的验证流程。

verifier.py 中的调用:
    factory = StudentInfoFactory()
    student_info = factory.create(self.vid)
    first = student_info.first_name
    last  = student_info.last_name
    ...
    for doc_name, doc_bytes in student_info.documents:
        print(f"📄 {doc_name}: {len(doc_bytes) / 1024:.1f} KB")

覆盖:
- 完整调用链模拟
- StudentInfo 结构完整性
- 文档可直接上传使用
- 所有文档保存到 output 目录
"""

import logging

import pytest
from student_document_factory import StudentInfoFactory, StudentInfo
from student_document_factory.universities import DocumentType

from conftest import save_document

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class TestVerifierStudentFlow:
    """模拟 verifier.py 的完整学生信息流"""

    def test_full_flow(self, factory, sample_vid) -> None:
        """
        模拟 verifier.py 中的调用:
            factory = StudentInfoFactory()
            student_info = factory.create(self.vid)

        生成的文档保存到 tests/output/student_docs/ 目录。
        修改 conftest.py 中的 OBFUSCATION_CONFIG 可查看各混淆效果。
        """
        student_info = factory.create(sample_vid, fetch_avatar=False)

        # 1. 基本字段（verifier.py 直接使用）
        assert isinstance(student_info, StudentInfo)
        first = student_info.first_name
        last = student_info.last_name
        email = student_info.email
        dob = student_info.birth_date
        uni = student_info.university

        assert first
        assert last
        assert "@" in email
        assert len(dob.split("-")) == 3

        # 2. 学校字段（用于 API 请求 body）
        assert uni["id"]
        assert uni["idExtended"]
        assert uni["name"]

        # 3. 文档（至少 2 份，用于上传）
        assert len(student_info.documents) >= 2
        for i, (doc_name, doc_bytes) in enumerate(student_info.documents):
            assert isinstance(doc_name, str)
            assert isinstance(doc_bytes, bytes)
            assert len(doc_bytes) > 0
            # 保存到 output 目录，便于查看效果
            save_document(doc_bytes, doc_name, label=f"full_flow_{i+1}")

    def test_save_all_verifier_documents(self, factory, sample_vid) -> None:
        """保存所有文档到 output 目录（模拟 verifier 日志输出）"""
        student_info = factory.create(sample_vid, fetch_avatar=False)

        for i, (doc_name, doc_bytes) in enumerate(student_info.documents):
            path = save_document(doc_bytes, doc_name, label=f"verifier_doc{i+1}")
            assert path.exists()
            assert path.stat().st_size > 0


class TestVerifierFields:
    """verifier.py 所需字段完整性"""

    def test_student_info_for_api_body(self, factory, sample_vid) -> None:
        """
        模拟 verifier.py 构建 API 请求体:
            body = {
                "firstName": first,
                "lastName": last,
                "birthDate": dob,
                "email": email,
                "organization": {
                    "id": self.org["id"],
                    "idExtended": self.org["idExtended"],
                    "name": self.org["name"],
                },
            }
        """
        info = factory.create(sample_vid, fetch_avatar=False)

        body = {
            "firstName": info.first_name,
            "lastName": info.last_name,
            "birthDate": info.birth_date,
            "email": info.email,
            "organization": {
                "id": info.university["id"],
                "idExtended": info.university["idExtended"],
                "name": info.university["name"],
            },
        }

        assert body["firstName"]
        assert body["lastName"]
        assert body["birthDate"]
        assert body["email"]
        assert body["organization"]["id"]

    def test_documents_are_valid_png(self, factory, sample_vid) -> None:
        """每份文档是有效 PNG"""
        info = factory.create(sample_vid, fetch_avatar=False)
        for filename, data in info.documents:
            assert data[:8] == _PNG_MAGIC, f"{filename} 不是有效 PNG"


class TestVerifierLogging:
    """verifier 调用链日志"""

    def test_full_logging_chain(self, factory, sample_vid, caplog) -> None:
        """完整调用链产生日志（模拟 verifier.py 调用时的日志输出）"""
        with caplog.at_level(logging.DEBUG):
            factory.create(sample_vid, fetch_avatar=False)

        messages = caplog.text
        # factory 日志
        assert "开始生成学生信息" in messages
        assert "[步骤1/7]" in messages
        # module 日志
        assert "哈佛学生数据生成" in messages or "哈佛文档生成" in messages
        # student_data 日志
        assert "哈佛学生数据构建完成" in messages
        # 文档生成日志
        assert "[步骤6/7]" in messages
        assert "[步骤7/7]" in messages
