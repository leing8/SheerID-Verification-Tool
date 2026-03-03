"""
test_background_scene_output.py — 背景场景叠加效果视觉检查测试

仅测试 apply_background_scene，不依赖任何其他效果模块。
所有图片保存至 tests/output/background_scene/ 目录，可直接打开查看效果。

相关测试文件：
  test_transform_3d_output.py  — 3D 透视变换独立测试

运行方式:
    # 全部测试
    pytest tests/common/student_document_factory/document_obfuscation/test_background_scene_output.py -v -s

    # 只看特定背景类型
    pytest tests/common/student_document_factory/document_obfuscation/test_background_scene_output.py::TestBackgroundTypes -v -s

    # 只看随机背景（多 seed）
    pytest tests/common/student_document_factory/document_obfuscation/test_background_scene_output.py::TestRandomBackground -v -s

    # 自定义 seed
    pytest tests/common/student_document_factory/document_obfuscation/test_background_scene_output.py -v -s --vid=my-seed
"""

from pathlib import Path

import pytest

# 输出目录：tests/output/background_scene/
_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "output" / "background_scene"

# 画布尺寸（模拟真实学生证/成绩单尺寸）
_W, _H = 640, 400


# ─────────────────────────────────────────────────────────────────────────────
# 共享工具函数
# ─────────────────────────────────────────────────────────────────────────────

def _make_realistic_doc(w: int, h: int):
    """
    生成模拟真实文档的画布（象牙白底 + 文字区域色块）。

    包含：
      - 深蓝色头部（模拟院校/机构 logo 区）
      - 标题文字区（白色矩形）
      - 多行正文（灰色细条，不同长度）
      - 右下角印章椭圆
    """
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
    """保存图片到背景场景输出目录"""
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

    背景生成：apply_background_scene 接收 RGB 文档图像，
    输出尺寸约为原图的 1.12×～1.28×（含四周背景边距）。
    """

    def _run_fixed_bg(self, bg_type: str, sample_vid, make_rng):
        """固定背景类型，运行 4 个 seed，返回保存路径列表"""
        import student_document_factory.document_obfuscation.effects.background_scene as bs_mod
        from student_document_factory.document_obfuscation.effects.background_scene import (
            apply_background_scene,
        )

        saved = []
        orig_choose = bs_mod._choose_bg_type
        bs_mod._choose_bg_type = lambda rng: bg_type  # monkey-patch 固定背景类型

        try:
            for i in range(4):
                rng = make_rng(f"{sample_vid}-bg-{bg_type}-{i}")
                doc = _make_realistic_doc(_W, _H)
                result = apply_background_scene(doc, rng, doc_type="transcript")
                path = _save(result, f"bg_{bg_type}_{i:02d}.png")
                saved.append(path)
                print(f"  [{i}]  size={result.size}  bg_type={bg_type}")
        finally:
            bs_mod._choose_bg_type = orig_choose  # 恢复原始函数

        return saved

    def test_desk_wood(self, sample_vid, make_rng):
        """浅木纹桌面背景（横向木纹条纹 + 低噪声）"""
        print("\n" + "=" * 66)
        print("  背景类型: desk_wood（浅木纹桌面）")
        print("=" * 66)
        saved = self._run_fixed_bg("desk_wood", sample_vid, make_rng)
        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")

    def test_desk_dark(self, sample_vid, make_rng):
        """深色桌面背景（深棕/深灰，与白色文档对比最强）"""
        print("\n" + "=" * 66)
        print("  背景类型: desk_dark（深色桌面，文档对比最强）")
        print("=" * 66)
        saved = self._run_fixed_bg("desk_dark", sample_vid, make_rng)
        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")

    def test_desk_white(self, sample_vid, make_rng):
        """白色/浅灰桌面背景（极低噪声，接近纯色）"""
        print("\n" + "=" * 66)
        print("  背景类型: desk_white（白色/浅灰桌面）")
        print("=" * 66)
        saved = self._run_fixed_bg("desk_white", sample_vid, make_rng)
        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")

    def test_carpet(self, sample_vid, make_rng):
        """地毯/布面背景（织物纹路 + 适度颗粒感）"""
        print("\n" + "=" * 66)
        print("  背景类型: carpet（地毯/布面纹理）")
        print("=" * 66)
        saved = self._run_fixed_bg("carpet", sample_vid, make_rng)
        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")

    def test_notebook(self, sample_vid, make_rng):
        """笔记本封面/书桌杂志背面（纯色 + 极低噪声）"""
        print("\n" + "=" * 66)
        print("  背景类型: notebook（笔记本/书封面，纯色）")
        print("=" * 66)
        saved = self._run_fixed_bg("notebook", sample_vid, make_rng)
        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")


# ─────────────────────────────────────────────────────────────────────────────
# 测试：随机背景（完全随机类型 + 多 seed）
# ─────────────────────────────────────────────────────────────────────────────

class TestRandomBackground:
    """随机背景类型（按权重分布），多个 seed 展示实际分布效果"""

    def test_random_multiple_seeds(self, sample_vid, make_rng):
        """完全随机背景 — 10 个 seed，背景类型按权重分布"""
        from student_document_factory.document_obfuscation.effects.background_scene import (
            apply_background_scene,
        )

        print("\n" + "=" * 66)
        print("  随机背景场景 — 多 seed（背景类型按权重随机分布）")
        print("=" * 66)

        saved = []
        for i in range(10):
            rng = make_rng(f"{sample_vid}-random-bg-{i}")
            doc = _make_realistic_doc(_W, _H)
            result = apply_background_scene(doc, rng, doc_type="transcript")
            path = _save(result, f"random_bg_{i:02d}.png")
            saved.append(path)
            scale_x = result.width / _W
            scale_y = result.height / _H
            print(f"  [{i:02d}]  out={result.size}  scale=({scale_x:.2f}×{scale_y:.2f})")

        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")


# ─────────────────────────────────────────────────────────────────────────────
# 测试：apply_background_scene 单元验证（非视觉）
# ─────────────────────────────────────────────────────────────────────────────

class TestBackgroundSceneUnit:
    """apply_background_scene 基本正确性单元测试"""

    def test_output_larger_than_input(self, sample_vid, make_rng):
        """输出图像应大于输入文档（背景边距 12%～28%）"""
        from student_document_factory.document_obfuscation.effects.background_scene import (
            apply_background_scene,
        )
        rng = make_rng(f"{sample_vid}-bs-unit-size")
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
        rng = make_rng(f"{sample_vid}-bs-unit-mode")
        doc = _make_realistic_doc(_W, _H)
        result = apply_background_scene(doc, rng)
        assert result.mode == "RGB", f"输出模式应为 RGB，实际为 {result.mode}"
        print(f"\n  ✅ 模式验证通过: {result.mode}")

    def test_scale_within_expected_range(self, sample_vid, make_rng):
        """输出尺寸应在 bg_scale 范围内（1.12×～1.28×，含轻微浮动）"""
        from student_document_factory.document_obfuscation.effects.background_scene import (
            apply_background_scene,
        )
        for i in range(5):
            rng = make_rng(f"{sample_vid}-bs-unit-scale-{i}")
            doc = _make_realistic_doc(_W, _H)
            result = apply_background_scene(doc, rng)
            scale_w = result.width / _W
            scale_h = result.height / _H
            assert 1.05 <= scale_w <= 1.40, f"宽度缩放 {scale_w:.2f} 超出预期范围"
            assert 1.05 <= scale_h <= 1.40, f"高度缩放 {scale_h:.2f} 超出预期范围"
        print(f"\n  ✅ 尺寸缩放验证通过（全部在 1.05×～1.40× 范围内）")

    def test_deterministic(self, sample_vid, make_rng):
        """相同 seed 应产生完全相同的结果（像素级确定性验证）"""
        import numpy as np
        from student_document_factory.document_obfuscation.effects.background_scene import (
            apply_background_scene,
        )
        doc = _make_realistic_doc(_W, _H)
        rng1 = make_rng(f"{sample_vid}-bs-det")
        rng2 = make_rng(f"{sample_vid}-bs-det")
        r1 = apply_background_scene(doc.copy(), rng1)
        r2 = apply_background_scene(doc.copy(), rng2)
        arr1 = np.array(r1)
        arr2 = np.array(r2)
        assert arr1.shape == arr2.shape, "相同 seed 输出尺寸应一致"
        assert np.array_equal(arr1, arr2), "相同 seed 输出像素应完全一致"
        print(f"\n  ✅ 确定性验证通过: {doc.size} → {r1.size}")
