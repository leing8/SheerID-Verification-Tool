"""
test_creases_output.py — 折痕效果视觉检查测试

在纯色底板上应用折痕效果，输出 PNG 文件至 tests/output/creases/ 目录，
可直接打开查看效果。附彩色标注线指示折痕位置。

运行方式:
    # 全部测试
    pytest tests/common/student_document_factory/document_obfuscation/test_creases_output.py -v -s

    # 只看水平折痕
    pytest tests/common/student_document_factory/document_obfuscation/test_creases_output.py::TestHorizontalCrease -v -s

    # 只看垂直折痕
    pytest tests/common/student_document_factory/document_obfuscation/test_creases_output.py::TestVerticalCrease -v -s

    # 随机折痕（完整效果）
    pytest tests/common/student_document_factory/document_obfuscation/test_creases_output.py::TestRandomCreases -v -s

    # 学生证跳过验证
    pytest tests/common/student_document_factory/document_obfuscation/test_creases_output.py::TestStudentIdSkip -v -s

    # 自定义 seed
    pytest tests/common/student_document_factory/document_obfuscation/test_creases_output.py -v -s --vid=my-seed
"""

from pathlib import Path

import pytest

# 输出目录：tests/output/creases/
_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "output" / "creases"

# 画布尺寸（与 test_stains_output.py 一致）
_W, _H = 640, 400


# ─────────────────────────────────────────────────────────────────────────────
# 绘制辅助
# ─────────────────────────────────────────────────────────────────────────────

def _draw_crease_mark(img, axis: str, pos_frac: float, color, label: str = ""):
    """在图像上用彩色虚线标注折痕位置"""
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    w, h = img.size

    if axis == "horizontal":
        y = int(pos_frac * h)
        # 虚线：每 12px 画 8px
        for x in range(0, w, 12):
            draw.line([(x, y), (min(x + 8, w - 1), y)], fill=color, width=2)
        if label:
            draw.text((4, y - 14), label, fill=color)
    else:
        x = int(pos_frac * w)
        for y in range(0, h, 12):
            draw.line([(x, y), (x, min(y + 8, h - 1))], fill=color, width=2)
        if label:
            draw.text((x + 4, 4), label, fill=color)


def _save(img, filename: str) -> Path:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = _OUTPUT_DIR / filename
    img.save(str(path), format="PNG")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 测试：水平折痕
# ─────────────────────────────────────────────────────────────────────────────

class TestHorizontalCrease:
    """水平折痕 — 白底，6 个 seed，红色虚线标注折痕位置"""

    def test_horizontal_multiple_seeds(self, sample_vid, make_rng):
        from student_document_factory.document_obfuscation.effects.creases import (
            _sample_crease_params, _apply_single_crease,
        )
        from student_document_factory.document_obfuscation.effects.stains import _to_uint8
        import numpy as np
        from PIL import Image

        print("\n" + "=" * 66)
        print("  水平折痕 — 多 seed，红色虚线标注折痕位置（白底）")
        print("=" * 66)

        saved = []
        for i in range(6):
            rng = make_rng(f"{sample_vid}-h-crease-{i}")
            canvas = Image.new("RGB", (_W, _H), color=(255, 255, 255))
            arr = np.array(canvas, dtype=np.float32)

            # 强制水平折痕（直接构造参数，使用新签名）
            pos_frac = rng.uniform(0.25, 0.75)
            cp = {
                "axis": "horizontal",
                "pos_frac": pos_frac,
                "grad_width": rng.randint(25, 60),
                "bright_side": rng.uniform(1.04, 1.11),
                "dark_side": rng.uniform(0.86, 0.95),
                "grad_decay": rng.uniform(3.0, 6.0),
                "specular_side": rng.choice(["positive", "negative"]),
                "spec_width": rng.uniform(1.5, 4.0),
                "spec_offset": rng.uniform(2.0, 5.0),
                "spec_bright": rng.uniform(1.08, 1.22),
                "spec_blur": rng.uniform(1.0, 2.5),
                "line_width": rng.randint(2, 5),
                "line_dark": rng.uniform(0.62, 0.80),
                "line_blur": rng.uniform(0.8, 1.8),
                "wiggle_amp": rng.uniform(0.5, 2.0),
                "wiggle_freq": rng.uniform(0.008, 0.025),
                "wiggle_phase": rng.uniform(0, 6.28),
            }

            arr = _apply_single_crease(arr, cp)

            result = Image.fromarray(_to_uint8(arr))
            _draw_crease_mark(result, "horizontal", pos_frac,
                              color=(200, 30, 30), label=f"crease@{pos_frac:.2f}")
            path = _save(result, f"horizontal_{i:02d}.png")
            saved.append(path)
            print(f"  [{i}]  y={int(pos_frac * _H):>3}px  "
                  f"lw={cp['line_width']}  dark={cp['line_dark']:.2f}  "
                  f"grad={cp['grad_width']}px  spec_bright={cp['spec_bright']:.2f}")

        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")


# ─────────────────────────────────────────────────────────────────────────────
# 测试：垂直折痕
# ─────────────────────────────────────────────────────────────────────────────

class TestVerticalCrease:
    """垂直折痕 — 白底，6 个 seed，蓝色虚线标注折痕位置"""

    def test_vertical_multiple_seeds(self, sample_vid, make_rng):
        from student_document_factory.document_obfuscation.effects.creases import (
            _sample_crease_params, _apply_single_crease,
        )
        from student_document_factory.document_obfuscation.effects.stains import _to_uint8
        import numpy as np
        from PIL import Image

        print("\n" + "=" * 66)
        print("  垂直折痕 — 多 seed，蓝色虚线标注折痕位置（白底）")
        print("=" * 66)

        saved = []
        for i in range(6):
            rng = make_rng(f"{sample_vid}-v-crease-{i}")
            canvas = Image.new("RGB", (_W, _H), color=(255, 255, 255))
            arr = np.array(canvas, dtype=np.float32)

            pos_frac = rng.uniform(0.25, 0.75)
            cp = {
                "axis": "vertical",
                "pos_frac": pos_frac,
                "line_width": rng.randint(2, 5),
                "line_dark": rng.uniform(0.62, 0.80),
                "line_blur": rng.uniform(0.8, 1.8),
                "grad_width": rng.randint(25, 60),
                "bright_side": rng.uniform(1.04, 1.11),
                "dark_side": rng.uniform(0.86, 0.95),
                "grad_decay": rng.uniform(3.0, 6.0),
                "specular_side": rng.choice(["positive", "negative"]),
                "spec_width": rng.uniform(1.5, 4.0),
                "spec_offset": rng.uniform(2.0, 5.0),
                "spec_bright": rng.uniform(1.08, 1.22),
                "spec_blur": rng.uniform(1.0, 2.5),
                "wiggle_amp": rng.uniform(0.5, 2.0),
                "wiggle_freq": rng.uniform(0.008, 0.025),
                "wiggle_phase": rng.uniform(0, 6.28),
            }

            arr = _apply_single_crease(arr, cp)

            result = Image.fromarray(_to_uint8(arr))
            _draw_crease_mark(result, "vertical", pos_frac,
                              color=(30, 60, 200), label=f"crease@{pos_frac:.2f}")
            path = _save(result, f"vertical_{i:02d}.png")
            saved.append(path)
            print(f"  [{i}]  x={int(pos_frac * _W):>3}px  "
                  f"lw={cp['line_width']}  dark={cp['line_dark']:.2f}  "
                  f"grad={cp['grad_width']}px  spec_bright={cp['spec_bright']:.2f}")

        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")


# ─────────────────────────────────────────────────────────────────────────────
# 测试：完整随机折痕（完整 apply_creases 接口）
# ─────────────────────────────────────────────────────────────────────────────

class TestRandomCreases:
    """随机折痕 — 浅灰底，6 个 seed，完整 apply_creases() 流程（1~2 条，方向随机）"""

    def test_random_creases_full_pipeline(self, sample_vid, make_rng):
        from student_document_factory.document_obfuscation.effects.creases import apply_creases
        from PIL import Image

        print("\n" + "=" * 66)
        print("  随机折痕（完整流水线）— 多 seed，浅灰底")
        print("=" * 66)

        saved = []
        for i in range(6):
            rng = make_rng(f"{sample_vid}-rand-crease-{i}")
            canvas = Image.new("RGB", (_W, _H), color=(235, 235, 230))

            result = apply_creases(canvas, rng, doc_type="transcript")
            assert isinstance(result, Image.Image), "apply_creases 应返回 PIL Image"
            assert result.size == (_W, _H), "输出尺寸应与输入一致"

            path = _save(result, f"random_{i:02d}.png")
            saved.append(path)
            print(f"  [{i}]  → {path.name}")

        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")

    def test_invoice_doc_type(self, sample_vid, make_rng):
        """invoice 文档类型也应正常产生折痕"""
        from student_document_factory.document_obfuscation.effects.creases import apply_creases
        from PIL import Image

        print("\n" + "=" * 66)
        print("  invoice 文档类型折痕 — 象牙色底板")
        print("=" * 66)

        saved = []
        for i in range(4):
            rng = make_rng(f"{sample_vid}-invoice-crease-{i}")
            canvas = Image.new("RGB", (_W, _H), color=(252, 250, 240))

            result = apply_creases(canvas, rng, doc_type="invoice")
            path = _save(result, f"invoice_{i:02d}.png")
            saved.append(path)
            print(f"  [{i}]  → {path.name}")

        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")


# ─────────────────────────────────────────────────────────────────────────────
# 测试：学生证跳过验证（核心正确性测试）
# ─────────────────────────────────────────────────────────────────────────────

class TestStudentIdSkip:
    """
    学生证文档应完全跳过折痕效果。

    验证：apply_creases(img, rng, doc_type="student_id") 返回像素值
    与原图完全一致（逐像素相等）。
    """

    def test_student_id_returns_unchanged(self, sample_vid, make_rng):
        from student_document_factory.document_obfuscation.effects.creases import apply_creases
        import numpy as np
        from PIL import Image

        print("\n" + "=" * 66)
        print("  学生证跳过验证 — apply_creases(doc_type='student_id') 应返回原图")
        print("=" * 66)

        saved = []
        all_passed = True
        for i in range(4):
            rng = make_rng(f"{sample_vid}-student-id-{i}")
            canvas = Image.new("RGB", (_W, _H), color=(200, 210, 230))

            original = np.array(canvas)
            result = apply_creases(canvas, rng, doc_type="student_id")
            result_arr = np.array(result)

            is_same = np.array_equal(original, result_arr)
            if not is_same:
                all_passed = False
                diff = np.abs(original.astype(int) - result_arr.astype(int))
                print(f"  [{i}]  ❌ 像素不一致！最大差异={diff.max()}")
            else:
                print(f"  [{i}]  ✅ 像素完全一致（student_id 已跳过）")

            path = _save(result, f"student_id_skip_{i:02d}.png")
            saved.append(path)

        assert all_passed, "student_id 文档不应被应用折痕效果！"

        print(f"\n  ✅ 全部 student_id 测试通过（原图未被修改）")
        print(f"  保存的图片（应与输入完全一致）：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")

    def test_empty_doc_type_applies_crease(self, sample_vid, make_rng):
        """空字符串 doc_type 应正常应用折痕（只有 'student_id' 才跳过）"""
        from student_document_factory.document_obfuscation.effects.creases import apply_creases
        import numpy as np
        from PIL import Image

        rng = make_rng(f"{sample_vid}-empty-doctype")
        canvas = Image.new("RGB", (_W, _H), color=(245, 245, 245))
        original = np.array(canvas)

        result = apply_creases(canvas, rng, doc_type="")
        result_arr = np.array(result)

        # 空 doc_type 应产生折痕，像素值不应与原图完全相同
        assert not np.array_equal(original, result_arr), \
            "空 doc_type 应产生折痕效果，但像素与原图完全相同"
        print("\n  ✅ 空 doc_type 正常应用折痕效果")
