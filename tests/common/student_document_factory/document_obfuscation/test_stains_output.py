"""
test_stains_output.py — 污渍效果视觉检查测试

纯色底板上应用污渍，附彩色轮廓圈标注范围，可选叠加黄色矩形标注安全保护区，
所有图片保存至 tests/output/stains/ 目录，可直接打开查看效果。

运行方式:
    # 全部测试（含安全区可视化）
    pytest tests/common/student_document_factory/document_obfuscation/test_stains_output.py -v -s

    # 只看三种污渍类型
    pytest tests/common/student_document_factory/document_obfuscation/test_stains_output.py::TestMudStain -v -s
    pytest tests/common/student_document_factory/document_obfuscation/test_stains_output.py::TestWearStain -v -s
    pytest tests/common/student_document_factory/document_obfuscation/test_stains_output.py::TestFadingStain -v -s

    # 安全区可视化（黄色保护框 + 彩色污渍圈）
    pytest tests/common/student_document_factory/document_obfuscation/test_stains_output.py::TestSafeZones -v -s

    # 自定义 seed
    pytest tests/common/student_document_factory/document_obfuscation/test_stains_output.py -v -s --vid=my-seed
"""

from pathlib import Path

import pytest

# 输出目录：tests/output/stains/（与 test_verbose_output.py 的 tests/output/ 根保持一致）
_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "output" / "stains"


# 画布尺寸
_W, _H = 640, 400


# ─────────────────────────────────────────────────────────────────────────────
# 绘制辅助
# ─────────────────────────────────────────────────────────────────────────────

def _draw_ellipse_mark(img, cx, cy, rx, ry, color, label=""):
    """在图像上用彩色实线椭圆 + 中心十字标注污渍范围"""
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    bbox = [cx - rx, cy - ry, cx + rx, cy + ry]
    draw.ellipse(bbox, outline=color, width=3)
    cross = 8
    draw.line([(cx - cross, cy), (cx + cross, cy)], fill=color, width=2)
    draw.line([(cx, cy - cross), (cx, cy + cross)], fill=color, width=2)
    if label:
        draw.text((cx - len(label) * 3, cy - ry - 16), label, fill=color)


def _draw_safe_zone_mark(img, zone):
    """在图像上用黄色虚线矩形标注安全保护区（含 padding）"""
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    ex1, ey1, ex2, ey2 = zone.expanded_bounds()
    # 夹紧到画布范围内
    ex1 = max(0, ex1); ey1 = max(0, ey1)
    ex2 = min(img.width - 1, ex2); ey2 = min(img.height - 1, ey2)
    # 黄色实线矩形（虚线需 PIL 9.2+，此处用宽 2px 实线代替）
    draw.rectangle([ex1, ey1, ex2, ey2], outline=(255, 200, 0), width=2)
    if zone.label:
        draw.text((ex1 + 4, ey1 + 3), zone.label, fill=(200, 150, 0))


def _save(img, filename: str) -> Path:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = _OUTPUT_DIR / filename
    img.save(str(path), format="PNG")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 测试：单一污渍类型（无安全区）
# ─────────────────────────────────────────────────────────────────────────────

class TestMudStain:
    """泥块（mud）— 白底，多个 seed，附红圈标注污渍范围"""

    def test_mud_multiple_seeds(self, sample_vid, white_canvas, make_rng):
        from student_document_factory.document_obfuscation.effects.stains import (
            _apply_mud, _mud_params, _to_float32, _to_uint8,
        )
        import numpy as np
        from PIL import Image

        print("\n" + "=" * 66)
        print("  mud（泥块）— 多 seed，红圈标注（无保护区）")
        print("=" * 66)

        saved = []
        for i in range(6):
            rng = make_rng(f"{sample_vid}-mud-{i}")
            p = _mud_params(rng, _W, _H, safe_zones=[])
            if p is None:
                print(f"  [{i}] 采样失败（无合法中心），跳过")
                continue

            arr = _to_float32(np.array(white_canvas.copy()))
            arr = _apply_mud(arr, p, rng)
            result = Image.fromarray(_to_uint8(arr))
            _draw_ellipse_mark(result, p["cx"], p["cy"], p["rx"], p["ry"],
                               color=(210, 30, 30), label="mud")
            path = _save(result, f"mud_{i:02d}.png")
            saved.append(path)
            print(f"  [{i}]  cx={p['cx']:>3} cy={p['cy']:>3}  "
                  f"rx={p['rx']:>3} ry={p['ry']:>3}  "
                  f"opacity={p['opacity']:.2f}  color=RGB{p['color']}")

        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")


class TestWearStain:
    """磨损（wear）— 白底，多个 seed，附蓝圈标注"""

    def test_wear_multiple_seeds(self, sample_vid, white_canvas, make_rng):
        from student_document_factory.document_obfuscation.effects.stains import (
            _apply_wear, _wear_params, _to_float32, _to_uint8,
        )
        import numpy as np
        from PIL import Image

        print("\n" + "=" * 66)
        print("  wear（磨损）— 多 seed，蓝圈标注（无保护区）")
        print("=" * 66)

        saved = []
        for i in range(6):
            rng = make_rng(f"{sample_vid}-wear-{i}")
            p = _wear_params(rng, _W, _H, safe_zones=[])
            if p is None:
                continue

            arr = _to_float32(np.array(white_canvas.copy()))
            arr = _apply_wear(arr, p, rng)
            result = Image.fromarray(_to_uint8(arr))
            _draw_ellipse_mark(result, p["cx"], p["cy"], p["rx"], p["ry"],
                               color=(30, 80, 210), label="wear")
            path = _save(result, f"wear_{i:02d}.png")
            saved.append(path)
            print(f"  [{i}]  cx={p['cx']:>3} cy={p['cy']:>3}  "
                  f"rx={p['rx']:>3} ry={p['ry']:>3}  opacity={p['opacity']:.2f}")

        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")


class TestFadingStain:
    """掉色（fading）— 彩色底板，多个 seed，附绿圈标注"""

    def test_fading_multiple_seeds(self, sample_vid, colored_canvas, make_rng):
        from student_document_factory.document_obfuscation.effects.stains import (
            _apply_fading, _fading_params, _to_float32, _to_uint8,
        )
        import numpy as np
        from PIL import Image

        print("\n" + "=" * 66)
        print("  fading（掉色）— 多 seed，绿圈标注（蓝色底板，无保护区）")
        print("=" * 66)

        saved = []
        for i in range(6):
            rng = make_rng(f"{sample_vid}-fading-{i}")
            p = _fading_params(rng, _W, _H, safe_zones=[])
            if p is None:
                continue

            arr = _to_float32(np.array(colored_canvas.copy()))
            arr = _apply_fading(arr, p, rng)
            result = Image.fromarray(_to_uint8(arr))
            _draw_ellipse_mark(result, p["cx"], p["cy"], p["rx"], p["ry"],
                               color=(30, 160, 60), label="fading")
            path = _save(result, f"fading_{i:02d}.png")
            saved.append(path)
            print(f"  [{i}]  cx={p['cx']:>3} cy={p['cy']:>3}  "
                  f"rx={p['rx']:>3} ry={p['ry']:>3}  "
                  f"sat={p['sat_factor']:.2f}  val={p['val_factor']:.2f}")

        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")


class TestAllStains:
    """三种污渍叠加，各自颜色标注：红=mud，蓝=wear，绿=fading"""

    def test_all_stains_combined(self, sample_vid, make_rng):
        from student_document_factory.document_obfuscation.effects.stains import (
            _apply_mud, _mud_params,
            _apply_wear, _wear_params,
            _apply_fading, _fading_params,
            _to_float32, _to_uint8,
        )
        import numpy as np
        from PIL import Image

        print("\n" + "=" * 66)
        print("  三种污渍叠加（极淡蓝底，无保护区）")
        print("  红=mud  蓝=wear  绿=fading")
        print("=" * 66)

        saved = []
        for i in range(6):
            rng = make_rng(f"{sample_vid}-all-{i}")
            canvas = Image.new("RGB", (_W, _H), color=(230, 238, 250))
            arr = _to_float32(np.array(canvas))

            marks = []
            for ptype, param_fn, apply_fn, color, label in [
                ("mud",    _mud_params,    _apply_mud,    (210, 30, 30),  "mud"),
                ("wear",   _wear_params,   _apply_wear,   (30, 80, 210),  "wear"),
                ("fading", _fading_params, _apply_fading, (30, 160, 60),  "fading"),
            ]:
                p = param_fn(rng, _W, _H, safe_zones=[])
                if p is not None:
                    arr = apply_fn(arr, p, rng)
                    marks.append((p["cx"], p["cy"], p["rx"], p["ry"], color, label))

            result = Image.fromarray(_to_uint8(arr))
            for cx, cy, rx, ry, color, label in marks:
                _draw_ellipse_mark(result, cx, cy, rx, ry, color, label)

            path = _save(result, f"all_stains_{i:03d}.png")
            saved.append(path)
            info = " | ".join(f"{l}@({cx},{cy})" for cx, cy, _, _, _, l in marks)
            print(f"  [{i:03d}]  {info}")

        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")


# ─────────────────────────────────────────────────────────────────────────────
# 测试：安全区可视化（核心功能验证）
# ─────────────────────────────────────────────────────────────────────────────

class TestSafeZones:
    """
    安全区保护效果可视化验证。

    在画布上定义若干 SafeZone（模拟文档核心数据区），
    生成污渍并叠加：
      - 黄色矩形框 = SafeZone（含 padding 扩展）
      - 彩色椭圆圈 = 污渍范围

    肉眼检查：彩色圈不应与黄色框重叠。
    """

    def _make_demo_safe_zones(self):
        """模拟文档核心区域（三个保护区，覆盖上中下三段）"""
        from student_document_factory.document_obfuscation.safe_zone import SafeZone
        return [
            SafeZone(x1=100, y1=30,  x2=540, y2=100, padding=20, label="header_name"),
            SafeZone(x1=80,  y1=160, x2=560, y2=250, padding=20, label="key_data"),
            SafeZone(x1=60,  y1=310, x2=580, y2=380, padding=15, label="courses"),
        ]

    def test_safe_zone_rejection_sampling(self, sample_vid, make_rng):
        """验证 Rejection Sampling：污渍圈不与黄色安全区重叠"""
        from student_document_factory.document_obfuscation.effects.stains import (
            _mud_params, _wear_params, _apply_mud, _apply_wear,
            _to_float32, _to_uint8,
        )
        import numpy as np
        from PIL import Image

        zones = self._make_demo_safe_zones()

        print("\n" + "=" * 66)
        print("  SafeZone 保护区可视化（黄框=保护区，彩圈=污渍）")
        print("  ✓ 彩圈不应与黄框重叠")
        print("=" * 66)

        saved = []
        for i in range(8):
            rng = make_rng(f"{sample_vid}-safezone-{i}")
            canvas = Image.new("RGB", (_W, _H), color=(245, 245, 245))
            arr = _to_float32(np.array(canvas))

            marks = []
            p_mud = _mud_params(rng, _W, _H, safe_zones=zones)
            if p_mud:
                arr = _apply_mud(arr, p_mud, rng)
                marks.append((p_mud["cx"], p_mud["cy"], p_mud["rx"], p_mud["ry"],
                               (210, 30, 30), "mud"))

            p_wear = _wear_params(rng, _W, _H, safe_zones=zones)
            if p_wear:
                arr = _apply_wear(arr, p_wear, rng)
                marks.append((p_wear["cx"], p_wear["cy"], p_wear["rx"], p_wear["ry"],
                               (30, 80, 210), "wear"))

            result = Image.fromarray(_to_uint8(arr))

            # 先画安全区黄框，再画污渍彩圈，使两者清晰可辨
            for zone in zones:
                _draw_safe_zone_mark(result, zone)
            for cx, cy, rx, ry, color, label in marks:
                _draw_ellipse_mark(result, cx, cy, rx, ry, color, label)

            path = _save(result, f"safe_zone_{i:02d}.png")
            saved.append(path)
            stain_info = " | ".join(
                f"{l}@({cx},{cy})" for cx, cy, _, _, _, l in marks
            ) or "（全部跳过）"
            print(f"  [{i:02d}]  {stain_info}")

        print(f"\n  ✅ 已保存 {len(saved)} 张：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")

    def test_safe_zone_conflict_detection(self, make_rng):
        """单元测试：SafeZone.conflicts() 正确性验证"""
        from student_document_factory.document_obfuscation.safe_zone import SafeZone

        zone = SafeZone(x1=100, y1=100, x2=300, y2=200, padding=20)

        # 中心在保护区内 → 冲突
        assert zone.conflicts(200, 150, 30, 20), "中心在保护区内应冲突"

        # 椭圆与保护区右边缘接触 → 冲突
        assert zone.conflicts(280, 150, 80, 20), "椭圆触碰右边缘应冲突"

        # 完全在保护区右侧 → 不冲突
        assert not zone.conflicts(450, 150, 50, 30), "完全在右侧应不冲突"

        # 完全在保护区上方 → 不冲突
        assert not zone.conflicts(200, 20, 30, 15), "完全在上方应不冲突"

        print("\n  ✅ SafeZone.conflicts() 正确性验证通过")

    def test_apply_stains_with_safe_zones(self, sample_vid, make_rng):
        """集成测试：apply_stains() 传入 safe_zones 后正常运行且返回图像"""
        from student_document_factory.document_obfuscation.effects.stains import apply_stains
        from student_document_factory.document_obfuscation.safe_zone import SafeZone
        from PIL import Image

        zones = [
            SafeZone(x1=200, y1=150, x2=440, y2=250, padding=25, label="center_block"),
        ]

        for i in range(4):
            rng = make_rng(f"{sample_vid}-apply-{i}")
            canvas = Image.new("RGB", (_W, _H), color=(255, 255, 255))
            result = apply_stains(canvas, rng, doc_type="student_id", safe_zones=zones)
            assert isinstance(result, Image.Image), "apply_stains 应返回 PIL Image"
            assert result.size == (_W, _H), "输出尺寸应与输入一致"

        print("\n  ✅ apply_stains() with safe_zones 集成测试通过")
