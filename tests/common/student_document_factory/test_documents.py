"""哈佛文档生成测试

覆盖:
- 3 种文档单独生成 (transcript / invoice / student_id)
- PNG 格式验证
- 每种文档保存到 output 目录
- fetch_avatar=False 学生证测试
- 文档生成日志验证
"""

import logging

import pytest
from student_document_factory.schools.harvard.documents import (
    generate_transcript,
    generate_invoice,
    generate_student_id_card,
)
from student_document_factory.schools.harvard.student_data import build

from conftest import SAMPLE_VID, save_document

# PNG 文件头魔数
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def student_data():
    """哈佛学生数据"""
    return build(SAMPLE_VID, "Computer Science (A.B.)")


class TestTranscript:
    """成绩单生成"""

    def test_returns_bytes(self, student_data) -> None:
        """返回 bytes"""
        result = generate_transcript(student_data)
        assert isinstance(result, bytes)
        assert len(result) > 1000

    def test_png_format(self, student_data) -> None:
        """PNG 格式"""
        result = generate_transcript(student_data)
        assert result[:8] == _PNG_MAGIC

    def test_save_to_output(self, student_data) -> None:
        """保存到 output 目录"""
        result = generate_transcript(student_data)
        path = save_document(result, "transcript.png", label="test")
        assert path.exists()

    def test_transcript_logging(self, student_data, caplog) -> None:
        """成绩单生成产生 DEBUG 日志"""
        with caplog.at_level(logging.DEBUG):
            generate_transcript(student_data)

        messages = caplog.text
        assert "成绩单生成开始" in messages
        assert "[成绩单 1/7]" in messages
        assert "[成绩单 7/7]" in messages


class TestInvoice:
    """发票生成"""

    def test_returns_bytes(self, student_data) -> None:
        result = generate_invoice(student_data)
        assert isinstance(result, bytes)
        assert len(result) > 1000

    def test_png_format(self, student_data) -> None:
        result = generate_invoice(student_data)
        assert result[:8] == _PNG_MAGIC

    def test_save_to_output(self, student_data) -> None:
        result = generate_invoice(student_data)
        path = save_document(result, "invoice.png", label="test")
        assert path.exists()

    def test_invoice_logging(self, student_data, caplog) -> None:
        """发票生成产生 DEBUG 日志"""
        with caplog.at_level(logging.DEBUG):
            generate_invoice(student_data)

        messages = caplog.text
        assert "发票生成开始" in messages
        assert "[发票 1/8]" in messages
        assert "[发票 8/8]" in messages


class TestStudentId:
    """学生证生成"""

    def test_returns_bytes(self, student_data) -> None:
        result = generate_student_id_card(student_data, fetch_avatar=False)
        assert isinstance(result, bytes)
        assert len(result) > 1000

    def test_png_format(self, student_data) -> None:
        result = generate_student_id_card(student_data, fetch_avatar=False)
        assert result[:8] == _PNG_MAGIC

    def test_save_to_output(self, student_data) -> None:
        result = generate_student_id_card(student_data, fetch_avatar=False)
        path = save_document(result, "student_id.png", label="no_avatar")
        assert path.exists()

    def test_fetch_avatar_false(self, student_data) -> None:
        """fetch_avatar=False 不发网络请求"""
        result = generate_student_id_card(student_data, fetch_avatar=False)
        assert isinstance(result, bytes)

    def test_student_id_logging(self, student_data, caplog) -> None:
        """学生证生成产生 DEBUG 日志"""
        with caplog.at_level(logging.DEBUG):
            generate_student_id_card(student_data, fetch_avatar=False)

        messages = caplog.text
        assert "学生证生成开始" in messages
        assert "[学生证 1/6]" in messages
        assert "fetch_avatar=False" in messages
        assert "[学生证 6/6]" in messages
