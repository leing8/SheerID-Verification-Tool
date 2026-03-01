"""
test_documents.py — 文档生成测试

测试 transcript / invoice / student_id 三种文档的生成、
确定性、图像有效性和 DocumentRandomizer 效果。
"""

import pytest

from student_document_factory.schools.harvard.documents import (
    generate_invoice,
    generate_student_id_card,
    generate_transcript,
)
from student_document_factory.schools.harvard.documents.common import (
    DocumentRandomizer,
    INVOICE_TEMPLATE_1,
    INVOICE_TEMPLATE_2,
    STUDENT_ID_TEMPLATE,
    TRANSCRIPT_TEMPLATE_1,
    TRANSCRIPT_TEMPLATE_2,
)


class TestTemplateFiles:
    """模板文件完整性"""

    def test_transcript_template_exists(self):
        """成绩单模板文件应存在"""
        assert TRANSCRIPT_TEMPLATE_1.exists(), f"模板不存在: {TRANSCRIPT_TEMPLATE_1}"
        assert TRANSCRIPT_TEMPLATE_2.exists(), f"模板不存在: {TRANSCRIPT_TEMPLATE_2}"

    def test_invoice_template_exists(self):
        """发票模板文件应存在"""
        assert INVOICE_TEMPLATE_1.exists(), f"模板不存在: {INVOICE_TEMPLATE_1}"
        assert INVOICE_TEMPLATE_2.exists(), f"模板不存在: {INVOICE_TEMPLATE_2}"

    def test_student_id_template_exists(self):
        """学生证模板文件应存在"""
        assert STUDENT_ID_TEMPLATE.exists(), f"模板不存在: {STUDENT_ID_TEMPLATE}"


class TestDocumentGeneration:
    """文档生成核心测试"""

    def test_transcript_returns_bytes(self, sample_harvard_data):
        """成绩单生成应返回非空字节"""
        result = generate_transcript(sample_harvard_data)
        assert isinstance(result, bytes)
        assert len(result) > 1000

    def test_invoice_returns_bytes(self, sample_harvard_data):
        """发票生成应返回非空字节"""
        result = generate_invoice(sample_harvard_data)
        assert isinstance(result, bytes)
        assert len(result) > 1000

    def test_student_id_returns_bytes(self, sample_harvard_data):
        """学生证生成应返回非空字节（跳过网络头像获取）"""
        result = generate_student_id_card(sample_harvard_data)
        assert isinstance(result, bytes)
        assert len(result) > 1000

    def test_transcript_is_valid_image(self, sample_harvard_data):
        """成绩单应生成有效的图片（PNG 或 JPEG 头）"""
        data = generate_transcript(sample_harvard_data)
        # JPEG 头 (因为 DocumentRandomizer 的 JPEG 重编码)
        # 最终输出为 PNG，但 JPEG cycle 后再存 PNG
        assert data[:4] == b'\x89PNG' or data[:2] == b'\xff\xd8'

    def test_invoice_is_valid_image(self, sample_harvard_data):
        """发票应生成有效的图片"""
        data = generate_invoice(sample_harvard_data)
        assert data[:4] == b'\x89PNG' or data[:2] == b'\xff\xd8'

    def test_student_id_is_valid_image(self, sample_harvard_data):
        """学生证应生成有效的图片"""
        data = generate_student_id_card(sample_harvard_data)
        assert data[:4] == b'\x89PNG' or data[:2] == b'\xff\xd8'


class TestDeterministicDocuments:
    """文档确定性生成"""

    def test_same_data_produces_identical_transcript(self, sample_harvard_data):
        """同一学生数据生成的成绩单应完全相同"""
        result1 = generate_transcript(sample_harvard_data)
        result2 = generate_transcript(sample_harvard_data)
        assert result1 == result2

    def test_same_data_produces_identical_invoice(self, sample_harvard_data):
        """同一学生数据生成的发票应完全相同"""
        result1 = generate_invoice(sample_harvard_data)
        result2 = generate_invoice(sample_harvard_data)
        assert result1 == result2

    def test_same_data_produces_identical_student_id(self, sample_harvard_data):
        """同一学生数据生成的学生证应完全相同"""
        result1 = generate_student_id_card(sample_harvard_data)
        result2 = generate_student_id_card(sample_harvard_data)
        assert result1 == result2

    def test_different_students_produce_different_documents(self):
        """不同学生的文档应不同"""
        from student_document_factory.schools.harvard.student_data import build
        data1 = build("vid-doc-diff-1", "Computer Science (A.B.)")
        data2 = build("vid-doc-diff-2", "Computer Science (A.B.)")
        result1 = generate_transcript(data1)
        result2 = generate_transcript(data2)
        assert result1 != result2


class TestDocumentRandomizer:
    """DocumentRandomizer 变换参数测试"""

    def test_randomizer_deterministic(self):
        """同一 seed 的 randomizer 产生相同参数"""
        import random
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        r1 = DocumentRandomizer(rng1)
        r2 = DocumentRandomizer(rng2)
        assert r1._rotation_angle == r2._rotation_angle
        assert r1._brightness_offset == r2._brightness_offset
        assert r1._noise_sigma == r2._noise_sigma
        assert r1._crop_margins == r2._crop_margins
        assert r1._fold_count == r2._fold_count
        assert r1._stain_count == r2._stain_count

    def test_different_seed_different_params(self):
        """不同 seed 的 randomizer 参数不同"""
        import random
        r1 = DocumentRandomizer(random.Random(1))
        r2 = DocumentRandomizer(random.Random(2))
        # 至少有一项不同
        assert (
            r1._rotation_angle != r2._rotation_angle
            or r1._brightness_offset != r2._brightness_offset
            or r1._noise_sigma != r2._noise_sigma
        )

    def test_rotation_angle_within_limit(self):
        """旋转角度应在 ±1.2° 范围内"""
        import random
        for seed in range(100):
            r = DocumentRandomizer(random.Random(seed))
            assert abs(r._rotation_angle) <= 1.2

    def test_brightness_offset_within_limit(self):
        """亮度偏移应在 ±10% 范围内"""
        import random
        for seed in range(100):
            r = DocumentRandomizer(random.Random(seed))
            assert abs(r._brightness_offset) <= 0.10

    def test_jpeg_quality_within_range(self):
        """JPEG 质量应在 87-95 范围内"""
        import random
        for seed in range(100):
            r = DocumentRandomizer(random.Random(seed))
            assert 87 <= r._jpeg_quality <= 95

    def test_crop_margins_within_limit(self):
        """裁剪边距应在 0~15px 范围内"""
        import random
        for seed in range(100):
            r = DocumentRandomizer(random.Random(seed))
            assert len(r._crop_margins) == 4
            for margin in r._crop_margins:
                assert 0 <= margin <= 15

    def test_fold_count_within_range(self):
        """折痕数量应在 0~2 范围内"""
        import random
        for seed in range(100):
            r = DocumentRandomizer(random.Random(seed))
            assert 0 <= r._fold_count <= 2
            assert len(r._fold_params) == r._fold_count

    def test_fold_position_in_edge_zone(self):
        """折痕位置比例应在 5%~15% 边缘范围内"""
        import random
        for seed in range(100):
            r = DocumentRandomizer(random.Random(seed))
            for direction, pos_ratio, _near_start, thickness, opacity in r._fold_params:
                assert direction in ("h", "v")
                assert 0.05 <= pos_ratio <= 0.15
                assert 3 <= thickness <= 8
                assert 0.05 <= opacity <= 0.15

    def test_stain_count_within_range(self):
        """污渍数量应在 0~2 范围内"""
        import random
        for seed in range(100):
            r = DocumentRandomizer(random.Random(seed))
            assert 0 <= r._stain_count <= 2
            assert len(r._stain_params) == r._stain_count

    def test_stain_opacity_within_range(self):
        """污渍不透明度应在 6%~18% 范围内"""
        import random
        for seed in range(100):
            r = DocumentRandomizer(random.Random(seed))
            for _corner, _rx, _ry, _ox, _oy, opacity, _color in r._stain_params:
                assert 0.06 <= opacity <= 0.18

    def test_photo_simulation_changes_image(self, sample_harvard_data):
        """拍照模拟应改变原始图像"""
        from PIL import Image
        import random
        img = Image.open(TRANSCRIPT_TEMPLATE_1).convert("RGB")
        original_data = list(img.getdata())

        rng = random.Random(42)
        r = DocumentRandomizer(rng)
        processed = r.apply_photo_simulation(img)
        processed_data = list(processed.getdata())

        # 至少有部分像素不同
        diff_count = sum(1 for a, b in zip(original_data, processed_data) if a != b)
        assert diff_count > 0, "拍照模拟未改变任何像素"


class TestStudentInfoFactory:
    """StudentInfoFactory 集成测试"""

    def test_factory_returns_student_info(self, student_factory, sample_vid):
        """工厂应返回 StudentInfo 实例"""
        from student_document_factory import StudentInfo
        info = student_factory.create(sample_vid)
        assert isinstance(info, StudentInfo)

    def test_factory_generates_documents(self, sample_student):
        """工厂应生成至少 2 个文档"""
        assert len(sample_student.documents) >= 2

    def test_factory_documents_are_valid_images(self, sample_student):
        """所有生成的文档应为有效图片"""
        for filename, data in sample_student.documents:
            assert isinstance(filename, str)
            assert filename.endswith(".png")
            assert isinstance(data, bytes)
            assert len(data) > 1000

    def test_factory_deterministic(self, student_factory):
        """同一 VID 应生成完全相同的结果"""
        vid = "test-factory-det-001"
        info1 = student_factory.create(vid)
        info2 = student_factory.create(vid)
        assert info1.first_name == info2.first_name
        assert info1.last_name == info2.last_name
        assert info1.university == info2.university
        assert len(info1.documents) == len(info2.documents)
        for (f1, d1), (f2, d2) in zip(info1.documents, info2.documents):
            assert f1 == f2
            assert d1 == d2
