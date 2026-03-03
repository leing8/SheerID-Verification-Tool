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


class TestObfuscationPipeline:
    """ObfuscationPipeline 与 PhotoSimulation 测试（替代旧 DocumentRandomizer）"""

    def test_pipeline_disabled_returns_original(self):
        """config.enabled=False 时，apply() 应返回原图（字节一致）"""
        import random
        from PIL import Image
        from student_document_factory.document_obfuscation import ObfuscationConfig, ObfuscationPipeline

        img = Image.open(TRANSCRIPT_TEMPLATE_1).convert("RGB")
        config = ObfuscationConfig(enabled=False)
        pipeline = ObfuscationPipeline(random.Random(42), config=config)
        result = pipeline.apply(img)

        # 禁用时返回同一对象（无副作用）
        assert result is img

    def test_pipeline_enabled_changes_image(self):
        """启用混淆后图像应有像素变化"""
        import random
        from PIL import Image
        from student_document_factory.document_obfuscation import DEFAULT_CONFIG, ObfuscationPipeline

        img = Image.open(TRANSCRIPT_TEMPLATE_1).convert("RGB")
        original_bytes = img.tobytes()

        pipeline = ObfuscationPipeline(random.Random(42), config=DEFAULT_CONFIG)
        processed = pipeline.apply(img)
        processed_bytes = processed.tobytes()

        assert original_bytes != processed_bytes, "混淆管道未改变任何像素"

    def test_photo_simulation_deterministic(self):
        """同一 RNG seed 的 PhotoSimulation 产生相同结果"""
        import random
        from PIL import Image
        from student_document_factory.document_obfuscation.photo_simulation import PhotoSimulation

        img = Image.open(TRANSCRIPT_TEMPLATE_1).convert("RGB")
        sim1 = PhotoSimulation(random.Random(42))
        sim2 = PhotoSimulation(random.Random(42))
        r1 = sim1.apply(img.copy())
        r2 = sim2.apply(img.copy())
        assert r1.tobytes() == r2.tobytes()

    def test_photo_simulation_different_seeds(self):
        """不同 seed 的 PhotoSimulation 结果应不同"""
        import random
        from PIL import Image
        from student_document_factory.document_obfuscation.photo_simulation import PhotoSimulation

        img = Image.open(TRANSCRIPT_TEMPLATE_1).convert("RGB")
        r1 = PhotoSimulation(random.Random(1)).apply(img.copy())
        r2 = PhotoSimulation(random.Random(2)).apply(img.copy())
        assert r1.tobytes() != r2.tobytes()

    def test_stains_at_least_one_type(self):
        """污渍效果必须至少出现一种（100 个 RNG seed 实验）"""
        import random
        from student_document_factory.document_obfuscation.effects.stains import _sample_stain_params

        # 使用足够大的画布 + 无保护区，确保 Rejection Sampling 总能找到合法位置
        img_size = (2000, 2000)
        for seed in range(100):
            rng = random.Random(seed)
            params = _sample_stain_params(rng, doc_type="", img_size=img_size, safe_zones=[])
            assert len(params) >= 1, f"seed={seed} 产生了 0 个污渍"

    def test_stains_fading_only_on_student_id(self):
        """fading 效果仅在 student_id 文档类型中出现"""
        import random
        from student_document_factory.document_obfuscation.effects.stains import _sample_stain_params

        img_size = (2000, 2000)
        # 大量 seed 测试非 student_id 文档不出现 fading
        for seed in range(200):
            rng = random.Random(seed)
            params = _sample_stain_params(rng, doc_type="transcript", img_size=img_size, safe_zones=[])
            types = {p["type"] for p in params}
            assert "fading" not in types, f"seed={seed} transcript 出现了 fading"

    def test_stains_wear_mud_on_all_docs(self):
        """mud/wear 效果在所有文档类型中都有机会出现"""
        import random
        from student_document_factory.document_obfuscation.effects.stains import _sample_stain_params

        img_size = (2000, 2000)
        seen_mud = seen_wear = False
        for seed in range(500):
            rng = random.Random(seed)
            params = _sample_stain_params(rng, doc_type="transcript", img_size=img_size, safe_zones=[])
            for p in params:
                if p["type"] == "mud":
                    seen_mud = True
                if p["type"] == "wear":
                    seen_wear = True
            if seen_mud and seen_wear:
                break
        assert seen_mud, "500 次采样中未见 mud 效果（transcript）"
        assert seen_wear, "500 次采样中未见 wear 效果（transcript）"

    def test_stains_apply_does_not_crash(self, sample_harvard_data):
        """apply_stains 对所有文档类型正常运行不崩溃"""
        import random
        from PIL import Image
        from student_document_factory.document_obfuscation.effects.stains import apply_stains

        img = Image.open(TRANSCRIPT_TEMPLATE_1).convert("RGB")
        for doc_type in ["", "transcript", "invoice", "student_id"]:
            rng = random.Random(42)
            result = apply_stains(img.copy(), rng, doc_type=doc_type)
            assert isinstance(result, Image.Image)


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
