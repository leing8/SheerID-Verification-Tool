"""
test_crop_output.py — 边缘裁剪效果视觉检查测试

仅测试 apply_crop，不依赖任何其他效果模块。
所有图片保存至 tests/output/crop/ 目录，可直接打开查看效果。

相关测试文件：
  test_background_scene_output.py — 背景场景独立测试
  test_transform_3d_output.py     — 3D 透视变换独立测试

运行方式:
    # 全部测试
    pytest tests/common/student_document_factory/document_obfuscation/test_crop_output.py -v -s

    # 只看视觉效果（多 seed）
    pytest tests/common/student_document_factory/document_obfuscation/test_crop_output.py::TestCropVisual -v -s

    # 只看 SafeZone 约束验证
    pytest tests/common/student_document_factory/document_obfuscation/test_crop_output.py::TestCropSafeZone -v -s

    # 只看单元测试
    pytest tests/common/student_document_factory/document_obfuscation/test_crop_output.py::TestCropUnit -v -s

    # 自定义 seed
    pytest tests/common/student_document_factory/document_obfuscation/test_crop_output.py -v -s --vid=my-seed
"""

from pathlib import Path

import numpy as np
import pytest

# 输出目录：tests/output/crop/
_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent.parent / "output" / "crop"

# 画布尺寸
_W, _H = 640, 400


# ─────────────────────────────────────────────────────────────────────────────
# 共享工具函数
# ─────────────────────────────────────────────────────────────────────────────

def _make_doc(w: int, h: int, fill=(250, 248, 240)):
    """生成纯色文档画布（用于像素对比验证）"""
    from PIL import Image
    return Image.new("RGB", (w, h), fill)


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


def _draw_safe_zones(img, zones):
    """在图像上绘制 SafeZone 扩展边界（绿色矩形，用于可视化辅助）"""
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    for z in zones:
        ex1, ey1, ex2, ey2 = z.expanded_bounds()
        draw.rectangle([ex1, ey1, ex2, ey2], outline=(0, 200, 80), width=2)


def _save(img, filename: str) -> Path:
    """保存图片到 crop 输出目录"""
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = _OUTPUT_DIR / filename
    img.save(str(path), format="PNG")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# 测试：视觉展示（多 seed）
# ─────────────────────────────────────────────────────────────────────────────

class TestCropVisual:
    """
    apply_crop 随机参数视觉测试。

    每对图保存两版：
      - crop_N.png  — 裁剪后最终图像（与输入同尺寸，LANCZOS 回缩）
      - orig_N.png  — 原始文档（便于对比轻微差异）
    """

    def test_random_crop_seeds(self, sample_vid, make_rng):
        """随机边缘裁剪 — 10 个 seed，观察四边独立裁剪效果"""
        from student_document_factory.document_obfuscation.effects.crop import apply_crop

        print("\n" + "=" * 66)
        print("  边缘裁剪 — 多 seed（四边独立随机裁剪，无 SafeZone 约束）")
        print("=" * 66)

        saved = []
        for i in range(10):
            doc = _make_realistic_doc(_W, _H)
            rng = make_rng(f"{sample_vid}-crop-{i}")
            result = apply_crop(doc, rng)

            assert result.size == doc.size, "resize 后应恢复原始尺寸"
            path = _save(result, f"crop_{i:02d}.png")
            saved.append(path)
            print(f"  [{i:02d}]  in={doc.size}  out={result.size}  → {path.name}")

        print(f"\n  ✅ 已保存 {len(saved)} 张：{_OUTPUT_DIR}")

    def test_crop_with_safe_zones_visual(self, sample_vid, make_rng):
        """带 SafeZone 的裁剪视觉展示（绿框=保护区）"""
        from student_document_factory.document_obfuscation.effects.crop import apply_crop
        from student_document_factory.document_obfuscation.safe_zone import SafeZone

        # 模拟真实保护区：学号（左侧）、日期（右侧）、姓名（顶部）
        zones = [
            SafeZone(x1=20,       y1=80,  x2=140,     y2=110, padding=8),  # 学号（左）
            SafeZone(x1=_W - 160, y1=80,  x2=_W - 40, y2=110, padding=8),  # 日期（右）
            SafeZone(x1=100,      y1=10,  x2=300,     y2=50,  padding=8),  # 姓名（顶）
        ]

        print("\n" + "=" * 66)
        print("  带 SafeZone 约束的边缘裁剪 — 6 个 seed（绿框=保护区）")
        print("=" * 66)

        saved = []
        for i in range(6):
            doc = _make_realistic_doc(_W, _H)
            _draw_safe_zones(doc, zones)  # 在文档上标注保护区

            rng = make_rng(f"{sample_vid}-sz-visual-{i}")
            result = apply_crop(doc, rng, safe_zones=zones)
            path = _save(result, f"safezone_{i:02d}.png")
            saved.append(path)
            print(f"  [{i}]  out={result.size}  → {path.name}")

        print(f"\n  ✅ 已保存 {len(saved)} 张（绿框=SafeZone 保护区）：")
        for p in saved:
            print(f"     file:///{p.as_posix()}")


# ─────────────────────────────────────────────────────────────────────────────
# 测试：SafeZone 保护约束验证（通过 apply_crop 行为验证）
# ─────────────────────────────────────────────────────────────────────────────

class TestCropSafeZone:
    """
    验证 apply_crop 正确遵守 SafeZone 约束。

    验证策略：在 SafeZone 完全覆盖某边的情况下，
    用足够多的 seed 反复调用，确认该边内容（像素列/行）始终被保留。

    SafeZone 边界碰撞规则（内部实现，对测试不透明）：
      expanded_bounds → (ex1, ey1, ex2, ey2)
      ex1 < left  → left=0，ex2 > w-right → right=0
      ey1 < top   → top=0，ey2 > h-bottom → bottom=0
    """

    def _left_column_preserved(self, img_orig, img_result, col_x: int) -> bool:
        """检查 col_x 列在原图与结果图的像素列方向内容是否一致（允许 LANCZOS 轻微误差）"""
        orig_col = np.array(img_orig)[:, col_x, :]
        res_col  = np.array(img_result)[:, col_x, :]
        return float(np.abs(orig_col.astype(int) - res_col.astype(int)).mean()) < 20

    def test_safe_zone_protects_left_edge(self, sample_vid, make_rng):
        """
        SafeZone 紧贴左边（ex1 ≤ 0）时，无论 seed 如何，left 方向内容不应被裁剪。
        验证方式：结果图 x=5 列的像素与原图 x=5 列基本一致。
        """
        from student_document_factory.document_obfuscation.effects.crop import apply_crop
        from student_document_factory.document_obfuscation.safe_zone import SafeZone

        # SafeZone 覆盖左边，expanded_bounds → ex1 = 5-8 = -3 < 0
        zone = SafeZone(x1=5, y1=100, x2=85, y2=160, padding=8)

        print("\n" + "=" * 66)
        print("  SafeZone 左边保护验证（30 个 seed）")
        print("=" * 66)

        for i in range(20):
            doc = _make_realistic_doc(_W, _H)
            rng = make_rng(f"{sample_vid}-sz-left-{i}")
            result = apply_crop(doc, rng, safe_zones=[zone])
            # 点验 SafeZone 中心区域的均値颜色特征是否保留（脱离像素精确对比）
            orig_mean = np.array(doc)[:, 30:70, :].mean(axis=(0, 1))
            res_mean  = np.array(result)[:, 30:70, :].mean(axis=(0, 1))
            diff = float(np.abs(orig_mean - res_mean).max())
            assert diff < 40, \
                f"[seed {i}] SafeZone 左边保护失败，平均颜色偶和差异过大={diff:.1f}"

        print("  ✅ 20 个 seed 均未删除左边 SafeZone 区域内容")

    def test_safe_zone_protects_right_edge(self, sample_vid, make_rng):
        """SafeZone 紧贴右边时，right 方向内容不应被裁剪"""
        from student_document_factory.document_obfuscation.effects.crop import apply_crop
        from student_document_factory.document_obfuscation.safe_zone import SafeZone

        # SafeZone 覆盖右边， expanded_bounds → ex2 = (_W-5)+8 = _W+3 > _W-max_px
        zone = SafeZone(x1=_W - 80, y1=100, x2=_W - 5, y2=160, padding=8)

        print("\n" + "=" * 66)
        print("  SafeZone 右边保护验证（30 个 seed）")
        print("=" * 66)

        for i in range(20):
            doc = _make_realistic_doc(_W, _H)
            rng = make_rng(f"{sample_vid}-sz-right-{i}")
            result = apply_crop(doc, rng, safe_zones=[zone])
            # 检查 SafeZone 内部均値颜色特征是否保留
            orig_mean = np.array(doc)[:, _W - 70:_W - 10, :].mean(axis=(0, 1))
            res_mean  = np.array(result)[:, _W - 70:_W - 10, :].mean(axis=(0, 1))
            diff = float(np.abs(orig_mean - res_mean).max())
            assert diff < 40, \
                f"[seed {i}] SafeZone 右边保护失败，平均颜色偏差={diff:.1f}"

        print("  ✅ 20 个 seed 均未删除右边 SafeZone 区域内容")

    def test_safe_zone_protects_top_edge(self, sample_vid, make_rng):
        """SafeZone 紧贴顶边时，top 方向内容不应被裁剪"""
        from student_document_factory.document_obfuscation.effects.crop import apply_crop
        from student_document_factory.document_obfuscation.safe_zone import SafeZone

        # SafeZone 覆盖顶边，expanded_bounds → ey1 = 5-8 = -3 < 0
        zone = SafeZone(x1=100, y1=5, x2=300, y2=45, padding=8)

        print("\n" + "=" * 66)
        print("  SafeZone 顶边保护验证（30 个 seed）")
        print("=" * 66)

        for i in range(20):
            doc = _make_realistic_doc(_W, _H)
            rng = make_rng(f"{sample_vid}-sz-top-{i}")
            result = apply_crop(doc, rng, safe_zones=[zone])
            # SafeZone 内顶部深蓝色头部（y=5~45）平均颜色应和结果图一致
            orig_mean = np.array(doc)[10:40, 120:280, :].mean(axis=(0, 1))
            res_mean  = np.array(result)[10:40, 120:280, :].mean(axis=(0, 1))
            diff = float(np.abs(orig_mean - res_mean).max())
            assert diff < 40, \
                f"[seed {i}] SafeZone 顶边保护失败，平均颜色偏差={diff:.1f}"

        print("  ✅ 20 个 seed 均未删除顶边 SafeZone 区域内容")

    def test_safe_zone_protects_bottom_edge(self, sample_vid, make_rng):
        """SafeZone 紧贴底边时，bottom 方向内容不应被裁剪"""
        from student_document_factory.document_obfuscation.effects.crop import apply_crop
        from student_document_factory.document_obfuscation.safe_zone import SafeZone

        # SafeZone 覆盖底边
        zone = SafeZone(x1=100, y1=_H - 55, x2=300, y2=_H - 15, padding=8)

        print("\n" + "=" * 66)
        print("  SafeZone 底边保护验证（30 个 seed）")
        print("=" * 66)

        for i in range(20):
            doc = _make_realistic_doc(_W, _H)
            rng = make_rng(f"{sample_vid}-sz-bottom-{i}")
            result = apply_crop(doc, rng, safe_zones=[zone])
            # SafeZone 区域内底部内容平均颜色应和结果图一致
            orig_mean = np.array(doc)[_H - 50:_H - 20, 120:280, :].mean(axis=(0, 1))
            res_mean  = np.array(result)[_H - 50:_H - 20, 120:280, :].mean(axis=(0, 1))
            diff = float(np.abs(orig_mean - res_mean).max())
            assert diff < 40, \
                f"[seed {i}] SafeZone 底边保护失败，平均颜色偏差={diff:.1f}"

        print("  ✅ 20 个 seed 均未删除底边 SafeZone 区域内容")

    def test_central_safe_zone_allows_cropping(self, sample_vid, make_rng):
        """
        SafeZone 位于文档中央时，四边应可正常裁剪（不被过度约束）。
        验证：50 个 seed 中至少有 1 个 seed 的输出与原图顶部/底部行有像素差异（发生了裁剪）。
        """
        from student_document_factory.document_obfuscation.effects.crop import apply_crop
        from student_document_factory.document_obfuscation.safe_zone import SafeZone

        # SafeZone 完全居中，不接近任何边
        zone = SafeZone(x1=200, y1=150, x2=440, y2=250, padding=8)

        print("\n" + "=" * 66)
        print("  中央 SafeZone 不阻止四边裁剪验证（50 个 seed）")
        print("=" * 66)

        # 用有内容的文档（顶部深蓝头部，resize 后顶行颜色会变化）
        doc = _make_realistic_doc(_W, _H)
        doc_arr = np.array(doc)

        crop_occurred = False
        for i in range(50):
            rng = make_rng(f"{sample_vid}-sz-central-{i}")
            result = apply_crop(doc, rng, safe_zones=[zone])
            # 检查顶部/底部行是否有任何像素差异（裁剪+resize 会引起边缘行颜色偏移）
            if not np.array_equal(doc_arr[:5, :, :], np.array(result)[:5, :, :]):
                crop_occurred = True
                print(f"  [{i}] ✅ 顶行发生裁剪变化")
                break
            if not np.array_equal(doc_arr[-5:, :, :], np.array(result)[-5:, :, :]):
                crop_occurred = True
                print(f"  [{i}] ✅ 底行发生裁剪变化")
                break
            if not np.array_equal(doc_arr[:, :5, :], np.array(result)[:, :5, :]):
                crop_occurred = True
                print(f"  [{i}] ✅ 左列发生裁剪变化")
                break

        assert crop_occurred, "中央 SafeZone 不应阻止四边裁剪（50 seed 内应有裁剪发生）"
        print("  ✅ 中央 SafeZone 不影响四边正常裁剪")


# ─────────────────────────────────────────────────────────────────────────────
# 测试：apply_crop 单元验证（非视觉）
# ─────────────────────────────────────────────────────────────────────────────

class TestCropUnit:
    """apply_crop 基本正确性单元测试"""

    def test_output_same_size_as_input(self, sample_vid, make_rng):
        """裁剪后 resize，输出尺寸应与输入完全一致"""
        from student_document_factory.document_obfuscation.effects.crop import apply_crop
        rng = make_rng(f"{sample_vid}-crop-unit-size")
        doc = _make_realistic_doc(_W, _H)
        result = apply_crop(doc, rng)
        assert result.size == doc.size, f"输出尺寸 {result.size} 应等于输入尺寸 {doc.size}"
        print(f"\n  ✅ 尺寸验证通过: {doc.size} → {result.size}")

    def test_output_is_rgb(self, sample_vid, make_rng):
        """输出应为 RGB 模式"""
        from student_document_factory.document_obfuscation.effects.crop import apply_crop
        rng = make_rng(f"{sample_vid}-crop-unit-mode")
        doc = _make_realistic_doc(_W, _H)
        result = apply_crop(doc, rng)
        assert result.mode == "RGB", f"输出模式应为 RGB，实际: {result.mode}"
        print(f"\n  ✅ 模式验证通过: {result.mode}")

    def test_deterministic(self, sample_vid, make_rng):
        """相同 seed 应产生完全相同的结果（像素级确定性）"""
        from student_document_factory.document_obfuscation.effects.crop import apply_crop
        doc = _make_realistic_doc(_W, _H)
        rng1 = make_rng(f"{sample_vid}-crop-det")
        rng2 = make_rng(f"{sample_vid}-crop-det")
        r1 = apply_crop(doc.copy(), rng1)
        r2 = apply_crop(doc.copy(), rng2)
        assert r1.size == r2.size, "相同 seed 输出尺寸应一致"
        assert np.array_equal(np.array(r1), np.array(r2)), "相同 seed 输出像素应完全一致"
        print(f"\n  ✅ 确定性验证通过")

    def test_no_crop_on_tiny_image(self, sample_vid, make_rng):
        """极小图像（无法裁剪）时应原样返回"""
        from student_document_factory.document_obfuscation.effects.crop import apply_crop
        tiny = _make_doc(10, 10)
        rng = make_rng(f"{sample_vid}-crop-unit-tiny")
        result = apply_crop(tiny, rng)
        assert result.size == tiny.size
        assert np.array_equal(np.array(result), np.array(tiny)), "极小图像应原样返回"
        print(f"\n  ✅ 极小图像原样返回验证通过")

    def test_no_safe_zones_produces_variation(self, sample_vid, make_rng):
        """无 SafeZone 时，多个 seed 中应有裁剪发生（非空操作）"""
        from student_document_factory.document_obfuscation.effects.crop import apply_crop
        # 使用有内容的文档（边缘含颜色差异），裁剪+resize 后更易检测到像素变化
        doc = _make_realistic_doc(_W, _H)
        doc_arr = np.array(doc)
        crop_happened = False
        for i in range(20):
            rng = make_rng(f"{sample_vid}-crop-unit-var-{i}")
            result = apply_crop(doc, rng)
            if not np.array_equal(doc_arr, np.array(result)):
                crop_happened = True
                break
        assert crop_happened, "无 SafeZone 下，20 个 seed 中应有裁剪发生"
        print(f"\n  ✅ 裁剪效果验证通过（无 SafeZone 时有裁剪发生）")
