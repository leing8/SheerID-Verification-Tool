"""
test_background_scene_output.py — 背景场景效果视觉检查测试

在文档图像上叠加桌面/地毯等背景，模拟拍照场景，
所有图片保存至 tests/output/background_scene/ 目录，可直接打开查看效果。

运行方式:
    # 全部测试
    pytest tests/common/student_document_factory/document_obfuscation/test_background_scene_output.py -v -s

    # 只看特定背景类型
    pytest tests/common/student_document_factory/document_obfuscation/test_background_scene_output.py::TestBackgroundTypes -v -s

    # 看完整管道效果（背景 + 拍照模拟）
    pytest tests/common/student_document_factory/document_obfuscation/test_background_scene_output.py::TestFullPipeline -v -s

    # 自定义 seed
    pytest tests/common/student_document_factory/document_obfuscation/test_background_scene_output.py -v -s --vid=my-seed
"""

from pathlib import Path

import pytest

# 输出目录
_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "output" / "background_scene"

# 画布尺寸（模拟真实学生证/成绩单尺寸）
_W, _H = 640, 400


# ─────────────────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────────────────

def _make_realistic_doc(w: int, h: int):
    """生成一个模拟真实文档的画布（象牙白底 + 简单文字区域色块）"""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (w, h), color=(250, 248, 240))
    draw = ImageDraw.Draw(img)

    # 模拟文档头部（深蓝色）
    draw.rectangle([0, 0, w, 60], fill=(30, 60, 120))

    # 模拟标题文字区（白色条）
    draw.rectangle([20, 10, w - 20, 50], fill=(255, 255, 255))

    # 模拟若干文字行（灰色细条）
    for y in range(80, h - 40, 22):
        line_w = w - 40 - (hash(str(y)) % 80)  # 不同长度
        draw.rectangle([20, y, line_w, y + 10], fill=(180, 180, 180))

    # 模拟印章/徽标椭圆（右下角）
    draw.ellipse([w - 100, h - 90, w - 20, h - 20], outline=(30, 80, 160), width=3)

    return img


def _save(img, filename: str) -> Path:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = _OUTPUT_DIR / filename
    img.save(str(path), format="PNG")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 测试：各背景类型单独展示
# ─────────────────────────────────────────────────────────────────────────────

class TestBackgroundTypes:
    """
    分别测试 5 种背景类型（通过 monkey-patch _choose_bg_type 强制固定类型），
    每种类型保存 4 个不同 seed 的结果。
    """

    def _run_fixed_bg(self, bg_type: str, sample_vid, make_rng):
        """固定背景类型，运行 4 个 seed，返回保存路径列表"""
        import student_document_factory.document_obfuscation.effects.background_scene as bs_mod
        from student_document_factory.document_obfuscation.effects.background_scene import (
            apply_background_scene,
        )

        saved = []
        orig_choose = bs_mod._choose_bg_type

        # 强制固定背景类型
        bs_mod._choose_bg_type = lambda rng: bg_type

        try:
            for i in range(4):
                rng = make_rng(f"{sample_vid}-bg-{bg_type}-{i}")
                doc = _make_realistic_doc(_W, _H)
                result = apply_background_scene(doc, rng, doc_type="transcript")
                path = _save(result, f"bg_{bg_type}_{i:02d}.png")
                saved.append(path)
                print(f"  [{i}]  size={result.size}  bg_type={bg_type}")
        finally:
            bs_mod._choose_bg_type = orig_choose

        return saved

    def test_desk_wood(self, sample_vid, make_rng):
        """浅木纹桌面背景"""
        print("\n" + "=" * 66)
        print("  背景类型: desk_wood（浅木纹桌面）")
        print("=" * 66)
        saved = self._run_fixed_bg("desk_wood", sample_vid, make_rng)
        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")

    def test_desk_dark(self, sample_vid, make_rng):
        """深色桌面背景（与白色文档对比最强）"""
        print("\n" + "=" * 66)
        print("  背景类型: desk_dark（深色桌面，文档对比最强）")
        print("=" * 66)
        saved = self._run_fixed_bg("desk_dark", sample_vid, make_rng)
        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")

    def test_desk_white(self, sample_vid, make_rng):
        """白色/浅灰桌面背景"""
        print("\n" + "=" * 66)
        print("  背景类型: desk_white（白色/浅灰桌面）")
        print("=" * 66)
        saved = self._run_fixed_bg("desk_white", sample_vid, make_rng)
        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")

    def test_carpet(self, sample_vid, make_rng):
        """地毯/布面背景"""
        print("\n" + "=" * 66)
        print("  背景类型: carpet（地毯/布面纹理）")
        print("=" * 66)
        saved = self._run_fixed_bg("carpet", sample_vid, make_rng)
        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")

    def test_notebook(self, sample_vid, make_rng):
        """笔记本封面背景"""
        print("\n" + "=" * 66)
        print("  背景类型: notebook（笔记本/书封面）")
        print("=" * 66)
        saved = self._run_fixed_bg("notebook", sample_vid, make_rng)
        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")


# ─────────────────────────────────────────────────────────────────────────────
# 测试：随机背景（完全随机类型 + seed）
# ─────────────────────────────────────────────────────────────────────────────

class TestRandomBackground:
    """随机背景类型（按权重分布），多个 seed"""

    def test_random_multiple_seeds(self, sample_vid, make_rng):
        """完全随机：背景类型 + 透视角度 + 所有参数均随机"""
        from student_document_factory.document_obfuscation.effects.background_scene import (
            apply_background_scene,
        )

        print("\n" + "=" * 66)
        print("  随机背景场景 — 多 seed（背景类型随机分布）")
        print("=" * 66)

        saved = []
        for i in range(10):
            rng = make_rng(f"{sample_vid}-random-bg-{i}")
            doc = _make_realistic_doc(_W, _H)
            result = apply_background_scene(doc, rng, doc_type="transcript")
            path = _save(result, f"random_bg_{i:02d}.png")
            saved.append(path)
            print(f"  [{i:02d}]  output_size={result.size}")

        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")


# ─────────────────────────────────────────────────────────────────────────────
# 测试：完整 ObfuscationPipeline（所有效果叠加）
# ─────────────────────────────────────────────────────────────────────────────

class TestFullPipeline:
    """测试完整流水线：stains + creases + background_scene + photo_simulation"""

    def test_full_pipeline_with_background(self, sample_vid, make_rng):
        """完整管道效果：所有混淆 + 背景场景 + 拍照模拟"""
        from PIL import Image
        from student_document_factory.document_obfuscation.config import DEFAULT_CONFIG
        from student_document_factory.document_obfuscation.pipeline import ObfuscationPipeline

        print("\n" + "=" * 66)
        print("  完整 ObfuscationPipeline（含 background_scene）")
        print("=" * 66)

        saved = []
        for i in range(6):
            rng = make_rng(f"{sample_vid}-full-pipeline-{i}")
            doc = _make_realistic_doc(_W, _H)

            pipeline = ObfuscationPipeline(rng, config=DEFAULT_CONFIG, doc_type="transcript")
            result = pipeline.apply(doc)

            assert isinstance(result, Image.Image), "管道应返回 PIL Image"
            path = _save(result, f"full_pipeline_{i:02d}.png")
            saved.append(path)
            print(f"  [{i}]  input={doc.size}  output={result.size}")

        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")

    def test_background_scene_only(self, sample_vid, make_rng):
        """仅背景场景（禁用其他效果），方便隔离观察"""
        from PIL import Image
        from student_document_factory.document_obfuscation.config import ObfuscationConfig
        from student_document_factory.document_obfuscation.pipeline import ObfuscationPipeline

        config = ObfuscationConfig(
            stains=False,
            creases=False,
            crop=False,
            transform_3d=False,
            photo_simulation=False,
            background_scene=True,
        )

        print("\n" + "=" * 66)
        print("  仅背景场景效果（隔离测试）")
        print("=" * 66)

        saved = []
        for i in range(8):
            rng = make_rng(f"{sample_vid}-bg-only-{i}")
            doc = _make_realistic_doc(_W, _H)
            pipeline = ObfuscationPipeline(rng, config=config, doc_type="transcript")
            result = pipeline.apply(doc)

            assert isinstance(result, Image.Image)
            assert result.width > _W, "输出宽度应大于原文档（包含背景）"
            assert result.height > _H, "输出高度应大于原文档（包含背景）"

            path = _save(result, f"bg_only_{i:02d}.png")
            saved.append(path)
            print(f"  [{i}]  in={doc.size}  out={result.size}  "
                  f"scale_x={result.width/_W:.2f}  scale_y={result.height/_H:.2f}")

        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")


# ─────────────────────────────────────────────────────────────────────────────
# 测试：单元验证（非视觉）
# ─────────────────────────────────────────────────────────────────────────────

class TestBackgroundSceneUnit:
    """apply_background_scene 的基本正确性单元测试"""

    def test_output_larger_than_input(self, sample_vid, make_rng):
        """输出图像应大于输入文档（包含背景边距）"""
        from student_document_factory.document_obfuscation.effects.background_scene import (
            apply_background_scene,
        )
        rng = make_rng(f"{sample_vid}-unit-size")
        doc = _make_realistic_doc(_W, _H)
        result = apply_background_scene(doc, rng)
        assert result.width > _W, f"输出宽 {result.width} 应 > 输入宽 {_W}"
        assert result.height > _H, f"输出高 {result.height} 应 > 输入高 {_H}"
        print(f"\n  ✅ 尺寸验证通过: {doc.size} → {result.size}")

    def test_output_is_rgb(self, sample_vid, make_rng):
        """输出应为 RGB 模式"""
        from student_document_factory.document_obfuscation.effects.background_scene import (
            apply_background_scene,
        )
        rng = make_rng(f"{sample_vid}-unit-mode")
        doc = _make_realistic_doc(_W, _H)
        result = apply_background_scene(doc, rng)
        assert result.mode == "RGB", f"输出模式应为 RGB，实际为 {result.mode}"
        print(f"\n  ✅ 模式验证通过: {result.mode}")

    def test_deterministic(self, sample_vid, make_rng):
        """相同 seed 应产生相同结果（确定性）"""
        import numpy as np
        from student_document_factory.document_obfuscation.effects.background_scene import (
            apply_background_scene,
        )
        doc = _make_realistic_doc(_W, _H)
        rng1 = make_rng(f"{sample_vid}-det")
        rng2 = make_rng(f"{sample_vid}-det")
        r1 = apply_background_scene(doc.copy(), rng1)
        r2 = apply_background_scene(doc.copy(), rng2)
        arr1 = np.array(r1)
        arr2 = np.array(r2)
        assert arr1.shape == arr2.shape, "相同 seed 输出尺寸应一致"
        assert np.array_equal(arr1, arr2), "相同 seed 输出像素应完全一致"
        print(f"\n  ✅ 确定性验证通过: 两次结果完全一致")
