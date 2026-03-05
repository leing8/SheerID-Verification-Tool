"""StudentInfoFactory 核心测试

覆盖:
- 创建学生信息
- 确定性（同 vid → 同结果）
- 文档数量与类型
- fetch_avatar 开关
- 日志输出验证
- 每步文档保存到 output 目录
"""

import logging

import pytest
from student_document_factory import StudentInfoFactory, StudentInfo
from student_document_factory.universities import DocumentType

from conftest import save_document


class TestCreate:
    """工厂创建"""

    def test_create_returns_student_info(self, factory, sample_vid) -> None:
        """create() 返回 StudentInfo"""
        result = factory.create(sample_vid, fetch_avatar=False)
        assert isinstance(result, StudentInfo)

    def test_create_fields_populated(self, factory, sample_vid) -> None:
        """所有字段非空"""
        info = factory.create(sample_vid, fetch_avatar=False)

        assert info.first_name
        assert info.last_name
        assert info.email
        assert info.birth_date
        assert info.university
        assert info.program
        assert len(info.documents) >= 2

    def test_university_dict_fields(self, factory, sample_vid) -> None:
        """university 字典包含完整字段"""
        info = factory.create(sample_vid, fetch_avatar=False)
        uni = info.university

        assert "id" in uni
        assert "idExtended" in uni
        assert "name" in uni
        assert "domain" in uni

    def test_email_format(self, factory, sample_vid) -> None:
        """邮箱格式: xxx@g.harvard.edu"""
        info = factory.create(sample_vid, fetch_avatar=False)
        assert "@g.harvard.edu" in info.email

    def test_birth_date_format(self, factory, sample_vid) -> None:
        """出生日期 YYYY-MM-DD"""
        info = factory.create(sample_vid, fetch_avatar=False)
        parts = info.birth_date.split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 4  # year
        assert len(parts[1]) == 2  # month
        assert len(parts[2]) == 2  # day


class TestDeterminism:
    """确定性验证"""

    def test_same_vid_same_result(self, factory, sample_vid) -> None:
        """同一 vid → 相同学生信息"""
        info1 = factory.create(sample_vid, fetch_avatar=False)
        info2 = factory.create(sample_vid, fetch_avatar=False)

        assert info1.first_name == info2.first_name
        assert info1.last_name == info2.last_name
        assert info1.email == info2.email
        assert info1.university == info2.university
        assert info1.program == info2.program
        assert len(info1.documents) == len(info2.documents)

    def test_different_vid_different_result(self, factory) -> None:
        """不同 vid → 不同学生信息"""
        info1 = factory.create("vid-aaaa-1111", fetch_avatar=False)
        info2 = factory.create("vid-bbbb-2222", fetch_avatar=False)

        # 姓名大概率不同（80*65 种）
        assert info1.first_name != info2.first_name or info1.last_name != info2.last_name


class TestDocuments:
    """文档生成"""

    def test_document_count(self, factory, sample_vid) -> None:
        """至少 2 份文档"""
        info = factory.create(sample_vid, fetch_avatar=False)
        assert len(info.documents) >= 2

    def test_document_format(self, factory, sample_vid) -> None:
        """每份文档: (文件名, bytes)"""
        info = factory.create(sample_vid, fetch_avatar=False)
        for filename, data in info.documents:
            assert isinstance(filename, str)
            assert filename.endswith(".png")
            assert isinstance(data, bytes)
            assert len(data) > 0

    def test_save_all_documents(self, factory, sample_vid) -> None:
        """保存所有文档到 output 目录，日志记录路径"""
        info = factory.create(sample_vid, fetch_avatar=False)
        for i, (filename, data) in enumerate(info.documents):
            path = save_document(data, filename, label=f"factory_step{i+1}")
            assert path.exists()


class TestFetchAvatar:
    """头像开关"""

    def test_avatar_off_no_network(self, factory, sample_vid) -> None:
        """fetch_avatar=False 不发网络请求"""
        info = factory.create(sample_vid, fetch_avatar=False)
        # 能正常返回即说明不依赖网络
        assert len(info.documents) >= 2

    def test_avatar_default_is_on(self) -> None:
        """默认参数 fetch_avatar=True"""
        import inspect
        sig = inspect.signature(StudentInfoFactory.create)
        assert sig.parameters["fetch_avatar"].default is True


class TestLogging:
    """日志验证"""

    def test_create_produces_info_logs(self, factory, sample_vid, caplog) -> None:
        """create() 产生 INFO 日志"""
        with caplog.at_level(logging.INFO, logger="student_document_factory.factory"):
            factory.create(sample_vid, fetch_avatar=False)

        messages = caplog.text
        assert "开始生成学生信息" in messages
        assert "[步骤1/7]" in messages
        assert "[步骤4/7]" in messages
        assert "[步骤5/7]" in messages
        assert "[步骤6/7]" in messages
        assert "[步骤7/7]" in messages
