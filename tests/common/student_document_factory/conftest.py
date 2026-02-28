"""
tests/common/student_document_factory/conftest.py

student_document_factory 专属 fixtures。
顶层 conftest.py 的 sample_vid fixture 在此继承可用。
"""

import pytest


@pytest.fixture
def student_factory():
    """返回 StudentInfoFactory 实例"""
    from student_document_factory import StudentInfoFactory
    return StudentInfoFactory()


@pytest.fixture
def sample_student(student_factory, sample_vid):
    """返回一个固定的 StudentInfo 实例"""
    return student_factory.create(sample_vid)


@pytest.fixture
def harvard_module():
    """返回 HarvardModule 实例"""
    from student_document_factory.schools.harvard import HarvardModule
    return HarvardModule()


@pytest.fixture
def sample_harvard_data():
    """返回一个固定的 HarvardStudentData 实例"""
    from student_document_factory.schools.harvard.student_data import build
    return build("test-harvard-fixture-001", "Computer Science (A.B.)")
