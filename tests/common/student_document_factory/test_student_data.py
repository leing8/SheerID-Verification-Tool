"""哈佛学生数据生成测试

覆盖:
- 学生字段验证
- 确定性
- 课程与学费数据
"""

import pytest

from student_document_factory.schools.harvard.student_data import (
    HarvardStudentData,
    build,
    PROGRAM_COURSES,
    PROGRAM_SCHOOL_CODE,
    TUITION_PER_TERM,
)

SAMPLE_VID = "test-verification-id-12345678-abcdef"


class TestBuild:
    """build() 函数"""

    def test_returns_harvard_student_data(self) -> None:
        """返回 HarvardStudentData"""
        data = build(SAMPLE_VID, "Computer Science (A.B.)")
        assert isinstance(data, HarvardStudentData)

    def test_required_fields(self) -> None:
        """通用必要字段"""
        data = build(SAMPLE_VID, "Computer Science (A.B.)")

        assert data.first_name
        assert data.last_name
        assert data.email
        assert data.birth_date
        assert data.student_id
        assert data.program == "Computer Science (A.B.)"
        assert data.school_code == "FAS"

    def test_student_id_8_digits(self) -> None:
        """学号 8 位"""
        data = build(SAMPLE_VID, "Computer Science (A.B.)")
        assert len(data.student_id) == 8
        assert data.student_id.isdigit()

    def test_email_harvard_domain(self) -> None:
        """邮箱 @g.harvard.edu"""
        data = build(SAMPLE_VID, "Computer Science (A.B.)")
        assert data.email.endswith("@g.harvard.edu")

    def test_birth_date_valid_range(self) -> None:
        """出生日期 18-26 岁"""
        from datetime import datetime
        data = build(SAMPLE_VID, "Computer Science (A.B.)")
        year = int(data.birth_date[:4])
        now_year = datetime.now().year
        age = now_year - year
        assert 18 <= age <= 26

    def test_gpa_range(self) -> None:
        """GPA 3.50-3.99"""
        data = build(SAMPLE_VID, "Computer Science (A.B.)")
        gpa = float(data.gpa)
        assert 3.50 <= gpa <= 3.99

    def test_address_4_lines(self) -> None:
        """地址 4 行"""
        data = build(SAMPLE_VID, "Computer Science (A.B.)")
        assert len(data.address) == 4
        assert data.address[3] == "United States"


class TestDeterminism:
    """确定性"""

    def test_same_vid_same_data(self) -> None:
        """同 vid → 同数据"""
        d1 = build(SAMPLE_VID, "Computer Science (A.B.)")
        d2 = build(SAMPLE_VID, "Computer Science (A.B.)")

        assert d1.first_name == d2.first_name
        assert d1.last_name == d2.last_name
        assert d1.student_id == d2.student_id
        assert d1.gpa == d2.gpa
        assert d1.courses == d2.courses


class TestCourses:
    """课程数据"""

    @pytest.mark.parametrize("program", list(PROGRAM_COURSES.keys()))
    def test_course_count(self, program: str) -> None:
        """8-12 门课"""
        data = build(SAMPLE_VID, program)
        assert 8 <= len(data.courses) <= 12

    @pytest.mark.parametrize("program", list(PROGRAM_COURSES.keys()))
    def test_course_format(self, program: str) -> None:
        """课程格式: (code, title, credits, grade, level)"""
        data = build(SAMPLE_VID, program)
        for code, title, credits_val, grade, level in data.courses:
            assert isinstance(code, str)
            assert isinstance(title, str)
            assert isinstance(credits_val, int)
            assert level in ("U", "G")


class TestSchoolCode:
    """学院代码"""

    @pytest.mark.parametrize("program,expected", [
        ("Computer Science (A.B.)", "FAS"),
        ("Computer Science (S.M.)", "GSAS"),
        ("Computer Science (Ph.D.)", "GSAS"),
        ("Data Science (S.M.)", "GSAS"),
    ])
    def test_school_code_mapping(self, program: str, expected: str) -> None:
        data = build(SAMPLE_VID, program)
        assert data.school_code == expected


class TestTuition:
    """学费数据"""

    @pytest.mark.parametrize("program", list(TUITION_PER_TERM.keys()))
    def test_tuition_amount(self, program: str) -> None:
        """学费与官方数据一致"""
        data = build(SAMPLE_VID, program)
        assert data.tuition_amount == TUITION_PER_TERM[program]

    def test_fee_fields(self) -> None:
        """附加费字段存在"""
        data = build(SAMPLE_VID, "Computer Science (A.B.)")
        assert data.fee_health > 0
        assert data.fee_activity > 0
        assert data.fee_gsc > 0
