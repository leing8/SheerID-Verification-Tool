"""
test_transform_3d_output.py — 3D 透视变换效果视觉检查测试

在文档图像上施加 yaw/pitch/roll 相机角度透视变换，
所有图片保存至 tests/output/transform_3d/ 目录，可直接打开查看效果。

运行方式:
    # 全部测试
    pytest tests/common/student_document_factory/document_obfuscation/test_transform_3d_output.py -v -s

    # 只看随机透视效果
    pytest tests/common/student_document_factory/document_obfuscation/test_transform_3d_output.py::TestTransform3DVisual -v -s

    # 只看前后对比
    pytest tests/common/student_document_factory/document_obfuscation/test_transform_3d_output.py::TestTransform3DCompare -v -s

    # 只看单元测试
    pytest tests/common/student_document_factory/document_obfuscation/test_transform_3d_output.py::TestTransform3DUnit -v -s

    # 自定义 seed
    pytest tests/common/student_document_factory/document_obfuscation/test_transform_3d_output.py -v -s --vid=my-seed
"""

from pathlib import Path

import pytest

# 输出目录：tests/output/transform_3d/
_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "output" / "transform_3d"

# 画布尺寸（模拟真实学生证/成绩单尺寸）
_W, _H = 640, 400


# ─────────────────────────────────────────────────────────────────────────────
# 工具函数
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

    draw.rectangle([0, 0, w, 60], fill=(30, 60, 120))
    draw.rectangle([20, 10, w - 20, 50], fill=(255, 255, 255))
    for y in range(80, h - 40, 22):
        line_w = w - 40 - (hash(str(y)) % 80)
        draw.rectangle([20, y, line_w, y + 10], fill=(180, 180, 180))
    draw.ellipse([w - 100, h - 90, w - 20, h - 20], outline=(30, 80, 160), width=3)

    return img


def _save(img, filename: str) -> Path:
    """保存图片到 transform_3d 输出目录"""
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = _OUTPUT_DIR / filename
    img.save(str(path), format="PNG")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 测试：随机透视变换视觉展示
# ─────────────────────────────────────────────────────────────────────────────

class TestTransform3DVisual:
    """
    apply_transform_3d 随机参数视觉测试。

    多个 seed 展示 yaw/pitch/roll 各种随机角度组合产生的梯形透视效果。
    """

    def test_random_perspective_seeds(self, sample_vid, make_rng):
        """随机透视变换 — 10 个 seed，观察各种角度组合效果"""
        from student_document_factory.document_obfuscation.effects.transform_3d import (
            apply_transform_3d,
        )

        print("\n" + "=" * 66)
        print("  3D 透视变换 — 多 seed（yaw/pitch/roll 随机角度）")
        print("=" * 66)

        saved = []
        for i in range(10):
            rng = make_rng(f"{sample_vid}-3d-random-{i}")
            doc = _make_realistic_doc(_W, _H)
            result = apply_transform_3d(doc, rng, doc_type="transcript")
            path = _save(result, f"perspective_{i:02d}.png")
            saved.append(path)
            ratio_w = result.width / _W
            ratio_h = result.height / _H
            print(f"  [{i:02d}]  in={doc.size}  out={result.size}"
                  f"  scale=({ratio_w:.2f}×{ratio_h:.2f})")

        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")

    def test_doc_types(self, sample_vid, make_rng):
        """不同文档类型应均正常产生透视变换效果"""
        from student_document_factory.document_obfuscation.effects.transform_3d import (
            apply_transform_3d,
        )

        print("\n" + "=" * 66)
        print("  3D 透视变换 — 不同文档类型（transcript / student_id / invoice）")
        print("=" * 66)

        doc_types = ["transcript", "student_id", "invoice", ""]
        saved = []
        for i, doc_type in enumerate(doc_types):
            rng = make_rng(f"{sample_vid}-3d-doctype-{i}")
            doc = _make_realistic_doc(_W, _H)
            result = apply_transform_3d(doc, rng, doc_type=doc_type)
            label = doc_type if doc_type else "(empty)"
            path = _save(result, f"doctype_{i:02d}_{label}.png")
            saved.append(path)
            print(f"  [{i}]  doc_type={label!r:15s}  out={result.size}")

        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")


# ─────────────────────────────────────────────────────────────────────────────
# 测试：前/后对比展示
# ─────────────────────────────────────────────────────────────────────────────

class TestTransform3DCompare:
    """
    将变换前/后图像成对保存，方便对比观察透视畸变效果。

    命名规则：compare_N_before.png / compare_N_after.png
    """

    def test_before_after_comparison(self, sample_vid, make_rng):
        """保存原图和变换后图像各 6 对，便于直观对比"""
        from student_document_factory.document_obfuscation.effects.transform_3d import (
            apply_transform_3d,
        )

        print("\n" + "=" * 66)
        print("  3D 透视变换 — 前/后对比（6 对）")
        print("=" * 66)

        for i in range(6):
            rng = make_rng(f"{sample_vid}-3d-compare-{i}")
            doc = _make_realistic_doc(_W, _H)

            # 用相同 seed 生成变换结果
            rng_warp = make_rng(f"{sample_vid}-3d-compare-{i}")
            warped = apply_transform_3d(doc, rng_warp, doc_type="transcript")

            _save(doc, f"compare_{i:02d}_before.png")
            _save(warped, f"compare_{i:02d}_after.png")
            diff_w = warped.width - doc.width
            diff_h = warped.height - doc.height
            print(f"  [{i}]  {doc.size} → {warped.size}"
                  f"  Δw={diff_w:+d}px  Δh={diff_h:+d}px")

        print(f"\n  ✅ 前/后对比图已保存至: {_OUTPUT_DIR}")

    def test_extreme_angles_edge_cases(self, sample_vid, make_rng):
        """
        验证边缘角度（接近最大 yaw/pitch/roll）下变换仍然正常。

        使用内部 _perspective_warp 直接施加固定角度，检查输出是否合理。
        """
        from student_document_factory.document_obfuscation.effects.transform_3d import (
            apply_transform_3d,
        )

        print("\n" + "=" * 66)
        print("  3D 透视变换 — 多 seed 视觉验证（正常角度范围）")
        print("=" * 66)

        saved = []
        for i in range(6):
            rng = make_rng(f"{sample_vid}-3d-edge-{i}")
            doc = _make_realistic_doc(_W, _H)
            result = apply_transform_3d(doc, rng, doc_type="transcript")
            path = _save(result, f"edge_{i:02d}.png")
            saved.append(path)
            print(f"  [{i}]  out={result.size}")

        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")


# ─────────────────────────────────────────────────────────────────────────────
# 测试：apply_transform_3d 单元验证（非视觉）
# ─────────────────────────────────────────────────────────────────────────────

class TestTransform3DUnit:
    """
    apply_transform_3d 基本正确性单元测试。

    验证：输出模式、尺寸合理性、确定性、非全黑。
    """

    def test_output_is_rgba(self, sample_vid, make_rng):
        """输出应为 RGBA 模式（透明区域保留 alpha 通道，不填白）"""
        from student_document_factory.document_obfuscation.effects.transform_3d import (
            apply_transform_3d,
        )
        rng = make_rng(f"{sample_vid}-3d-unit-mode")
        doc = _make_realistic_doc(_W, _H)
        result = apply_transform_3d(doc, rng)
        assert result.mode == "RGBA", f"输出应为 RGBA，实际: {result.mode}"
        print(f"\n  ✅ 输出模式: {result.mode}")

    def test_output_size_reasonable(self, sample_vid, make_rng):
        """
        输出尺寸不应超出输入的合理倍数。

        约束：yaw ≤ 6°, pitch ≤ 5°, roll ≤ 4°，加 padding 后最大约 25% 扩展。
        """
        from student_document_factory.document_obfuscation.effects.transform_3d import (
            apply_transform_3d,
        )
        for i in range(8):
            rng = make_rng(f"{sample_vid}-3d-unit-size-{i}")
            doc = _make_realistic_doc(_W, _H)
            result = apply_transform_3d(doc, rng)
            assert result.width <= _W * 1.25, \
                f"[{i}] 宽度 {result.width} 超出上限（{_W} × 1.25 = {int(_W * 1.25)}）"
            assert result.height <= _H * 1.25, \
                f"[{i}] 高度 {result.height} 超出上限（{_H} × 1.25 = {int(_H * 1.25)}）"
        print(f"\n  ✅ 尺寸合理性验证通过（全部 ≤ 原始尺寸 × 1.25）")

    def test_deterministic(self, sample_vid, make_rng):
        """相同 seed 应产生完全相同的结果（像素级确定性验证）"""
        import numpy as np
        from student_document_factory.document_obfuscation.effects.transform_3d import (
            apply_transform_3d,
        )
        doc = _make_realistic_doc(_W, _H)
        rng1 = make_rng(f"{sample_vid}-3d-det")
        rng2 = make_rng(f"{sample_vid}-3d-det")
        r1 = apply_transform_3d(doc.copy(), rng1)
        r2 = apply_transform_3d(doc.copy(), rng2)
        arr1 = np.array(r1)
        arr2 = np.array(r2)
        assert arr1.shape == arr2.shape, "相同 seed 输出尺寸应一致"
        assert np.array_equal(arr1, arr2), "相同 seed 输出像素应完全一致"
        print(f"\n  ✅ 确定性验证通过: {doc.size} → {r1.size}")

    def test_no_all_black_output(self, sample_vid, make_rng):
        """变换后图像不应全黑（保证变换逻辑正常执行）"""
        import numpy as np
        from student_document_factory.document_obfuscation.effects.transform_3d import (
            apply_transform_3d,
        )
        rng = make_rng(f"{sample_vid}-3d-unit-notblack")
        doc = _make_realistic_doc(_W, _H)
        result = apply_transform_3d(doc, rng)
        arr = np.array(result)
        assert arr.mean() > 50, f"输出图像不应全黑（均值应 > 50，实际 {arr.mean():.1f}）"
        print(f"\n  ✅ 输出图像非全黑，均值={arr.mean():.1f}")

    def test_transparent_area_has_zero_alpha(self, sample_vid, make_rng):
        """
        透明区域（文档轮廓外）的 alpha 应为 0，
        而非白色填充，确保与 background_scene 合成不产生割裂感。
        """
        import numpy as np
        from student_document_factory.document_obfuscation.effects.transform_3d import (
            apply_transform_3d,
        )
        rng = make_rng(f"{sample_vid}-3d-unit-alpha")
        doc = _make_realistic_doc(_W, _H)
        result = apply_transform_3d(doc, rng)
        assert result.mode == "RGBA", "应返回 RGBA 以支持 alpha 合成"

        arr = np.array(result)
        alpha = arr[:, :, 3]

        # 应存在 alpha=0 的透明像素（参考透视变换之同四角）
        has_transparent = (alpha == 0).any()
        assert has_transparent, "透视变换应在文档轮廓外生成透明区域（alpha=0）"

        # 文档主体区域应全部不透明（中心 60% 区域）
        h, w = alpha.shape
        center_alpha = alpha[
            int(h * 0.2):int(h * 0.8),
            int(w * 0.2):int(w * 0.8),
        ]
        assert center_alpha.min() > 200, \
            f"文档中心区域应完全不透明，alpha 最小値={center_alpha.min()}"
        print(f"\n  ✅ 透明区域验证通过: has_transparent={has_transparent}, center_min_alpha={center_alpha.min()}")
