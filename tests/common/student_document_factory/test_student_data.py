"""
test_student_data.py — HarvardStudentData 数据生成测试

测试确定性数据生成、字段格式校验、数据合理性等关键属性。
"""

import re

import pytest
from student_document_factory.schools.harvard.student_data import (
    FIRST_NAMES,
    LAST_NAMES,
    PROGRAM_COURSES,
    PROGRAM_SCHOOL_CODE,
    TUITION_PER_TERM,
    US_ADDRESSES,
    US_STREETS,
    HarvardStudentData,
    build,
)


class TestDeterministicGeneration:
    """确定性生成: 同一 VID + program → 同一学生数据"""

    def test_same_vid_produces_identical_data(self):
        """同一 VID 多次调用产生完全相同的学生数据"""
        vid = "test-deterministic-001"
        prog = "Computer Science (A.B.)"
        data1 = build(vid, prog)
        data2 = build(vid, prog)
        assert data1.first_name == data2.first_name
        assert data1.last_name == data2.last_name
        assert data1.email == data2.email
        assert data1.student_id == data2.student_id
        assert data1.gpa == data2.gpa
        assert data1.address == data2.address

    def test_different_vid_produces_different_data(self):
        """不同 VID 产生不同的学生数据"""
        prog = "Computer Science (A.B.)"
        data1 = build("vid-aaa-111", prog)
        data2 = build("vid-bbb-222", prog)
        # 姓名+学号至少有一项不同（概率极高）
        assert (
            data1.first_name != data2.first_name
            or data1.last_name != data2.last_name
            or data1.student_id != data2.student_id
        )

    def test_different_program_preserves_name(self):
        """同一 VID 不同专业，姓名应相同（因为 rng 从同一 seed 开始）"""
        vid = "test-program-switch"
        data_ab = build(vid, "Computer Science (A.B.)")
        data_sm = build(vid, "Computer Science (S.M.)")
        assert data_ab.first_name == data_sm.first_name
        assert data_ab.last_name == data_sm.last_name


class TestFieldFormats:
    """字段格式校验"""

    def test_email_format(self, sample_harvard_data):
        """邮箱格式应为 xxx@g.harvard.edu"""
        assert sample_harvard_data.email.endswith("@g.harvard.edu")
        local = sample_harvard_data.email.split("@")[0]
        assert len(local) > 0

    def test_birth_date_format(self, sample_harvard_data):
        """出生日期格式应为 YYYY-MM-DD"""
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", sample_harvard_data.birth_date)

    def test_student_id_is_8_digits(self, sample_harvard_data):
        """学号应为 8 位数字"""
        assert re.match(r"^\d{8}$", sample_harvard_data.student_id)

    def test_gpa_format(self, sample_harvard_data):
        """GPA 格式应为 X.XX，范围 3.50-3.99"""
        gpa = float(sample_harvard_data.gpa)
        assert 3.50 <= gpa <= 3.99

    def test_invoice_number_format(self, sample_harvard_data):
        """发票号格式应为 INV-YYYYMMDD-学号"""
        assert sample_harvard_data.invoice_number.startswith("INV-")
        parts = sample_harvard_data.invoice_number.split("-")
        assert len(parts) == 3
        assert re.match(r"^\d{8}$", parts[1])  # 日期部分
        assert parts[2] == sample_harvard_data.student_id

    def test_term_format(self, sample_harvard_data):
        """学期格式应为 'Spring YYYY' 或 'Fall YYYY'"""
        assert re.match(r"^(Spring|Fall) \d{4}$", sample_harvard_data.term)


class TestDataIntegrity:
    """数据完整性和合理性"""

    def test_name_from_pool(self, sample_harvard_data):
        """姓名应来自预定义的姓名池"""
        assert sample_harvard_data.first_name in FIRST_NAMES
        assert sample_harvard_data.last_name in LAST_NAMES

    def test_school_code_matches_program(self):
        """学院代码应与专业匹配"""
        for program, expected_code in PROGRAM_SCHOOL_CODE.items():
            data = build("test-school-code", program)
            assert data.school_code == expected_code, (
                f"{program}: got {data.school_code}, expected {expected_code}"
            )

    def test_courses_match_program(self):
        """课程列表应与专业匹配"""
        for program, expected_courses in PROGRAM_COURSES.items():
            data = build("test-courses", program)
            assert data.courses == expected_courses

    def test_tuition_matches_program(self):
        """学费应与专业匹配"""
        for program, expected_tuition in TUITION_PER_TERM.items():
            data = build("test-tuition", program)
            assert data.tuition_amount == expected_tuition

    def test_fees_are_official_values(self, sample_harvard_data):
        """附加费用应为 2025-2026 官方数据"""
        assert sample_harvard_data.fee_health == 3054
        assert sample_harvard_data.fee_activity == 225
        assert sample_harvard_data.fee_gsc == 35

    def test_all_programs_generate_valid_data(self):
        """所有专业都能生成有效数据"""
        for i, program in enumerate(PROGRAM_SCHOOL_CODE.keys()):
            data = build(f"test-program-{i}", program)
            assert isinstance(data, HarvardStudentData)
            assert data.program == program
            assert len(data.courses) > 0


class TestAddress:
    """地址生成测试"""

    def test_address_is_4_tuple(self, sample_harvard_data):
        """地址应为 4 行元组"""
        assert isinstance(sample_harvard_data.address, tuple)
        assert len(sample_harvard_data.address) == 4

    def test_address_line1_contains_name(self, sample_harvard_data):
        """地址第一行应包含学生姓名"""
        name_line = sample_harvard_data.address[0]
        assert sample_harvard_data.first_name in name_line
        assert sample_harvard_data.last_name in name_line

    def test_address_line4_is_united_states(self, sample_harvard_data):
        """地址第四行应为 'United States'"""
        assert sample_harvard_data.address[3] == "United States"

    def test_address_deterministic(self):
        """同一 VID 地址应确定性"""
        data1 = build("test-addr-det", "Computer Science (A.B.)")
        data2 = build("test-addr-det", "Computer Science (A.B.)")
        assert data1.address == data2.address
