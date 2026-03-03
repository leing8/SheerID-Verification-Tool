"""
document_obfuscation.effects.creases — 纸张折痕效果

渲染具有物理真实感的纸张折叠/折痕，分三层叠加（均为纯光照操作，不移动像素）：

  1. 指数光照渐变  — 折痕弯曲面的光照变化：迎光侧渐亮、背光侧渐暗，
                     采用指数衰减（比线性更陡，更接近纸张弯曲的实际光照曲线）
  2. 折叠高光细线  — 折痕棱角正对光源时产生的镜面高光（薄亮线），
                     叠加在压痕暗线的亮侧，产生立体弯折感
  3. 压痕暗线      — 纸纤维受压变暗的细线（带正弦微扰动，避免太"画线"感），
                     边缘高斯软化，混入少量暗棕偏色

设计原则：
  纯光照/颜色操作，不做任何像素位移（warp/remap）
     → 文字位置完全不受影响，不会产生文字错乱
  折叠的三维弯折感完全由光照梯度和高光细线传达
  安全区保护：折痕通过 Rejection Sampling 绕开所有 SafeZone
     折痕是贯穿全图的直线，其位置坐标不得落在任何保护区的对应轴范围内
  数量保证：必须找到所需数量的合法位置，否则扩大搜索范围
  学生证（doc_type == "student_id"）跳过
  确定性：相同 seed 保证相同结果
"""

import math
import random
from typing import List, Optional, Tuple

from PIL import Image

from .utils import to_uint8 as _to_uint8
from ..safe_zone import SafeZone

# Rejection Sampling 最大重试次数（每条折痕独立计算）
_MAX_SAMPLE_TRIES = 100


# ═══════════════════════════════════════════════════════════════════════════════
# 公开入口
# ═══════════════════════════════════════════════════════════════════════════════

def apply_creases(
    img: Image.Image,
    rng: random.Random,
    doc_type: str = "",
    safe_zones: Optional[List[SafeZone]] = None,
) -> Image.Image:
    """
    折痕效果主入口。

    Args:
        img:        输入 PIL 图像（RGB）。
        rng:        确定性随机数生成器（由调用方以 student_id 作为 seed 创建）。
        doc_type:   文档类型字符串。"student_id" 跳过折痕效果（塑料卡片不会折叠）。
        safe_zones: 核心数据保护区列表。折痕位置通过 Rejection Sampling 绕开所有保护区。
                    折痕为贯穿全图的直线，其轴坐标不得落在任何保护区的对应轴范围内。
                    None 或空列表表示无保护区约束。

    Returns:
        应用折痕后的 PIL 图像（RGB）。学生证原图原样返回。
    """
    try:
        import numpy as np
    except ImportError:
        return img

    # 学生证为硬塑料卡片，不适用折痕
    if doc_type == "student_id":
        return img

    w, h = img.size
    zones: List[SafeZone] = safe_zones or []
    arr = np.array(img.convert("RGB"), dtype=np.float32)

    # 随机决定折痕数量：70% 为 1 条，30% 为 2 条
    n_creases = 1 if rng.random() < 0.70 else 2

    # 生成各折痕参数（Rejection Sampling 保证绕开保护区且满足数量要求）
    crease_params = _sample_crease_params(rng, n_creases, w, h, zones)

    for cp in crease_params:
        arr = _apply_single_crease(arr, cp)

    return Image.fromarray(_to_uint8(arr))


# ═══════════════════════════════════════════════════════════════════════════════
# 参数采样
# ═══════════════════════════════════════════════════════════════════════════════

def _line_conflicts_safe_zones(
    axis: str,
    pos_px: float,
    img_w: int,
    img_h: int,
    safe_zones: List[SafeZone],
) -> bool:
    """
    判断贯穿全图的折痕线是否与任意保护区冲突。

    折痕是一条贯穿全图的直线：
      - horizontal 折痕：y = pos_px，横跨整个宽度
      - vertical   折痕：x = pos_px，纵跨整个高度

    冲突条件（含 padding 扩展）：
      - horizontal：pos_px 落在保护区 [ey1, ey2] 范围内
      - vertical  ：pos_px 落在保护区 [ex1, ex2] 范围内
    """
    for zone in safe_zones:
        ex1, ey1, ex2, ey2 = zone.expanded_bounds()
        if axis == "horizontal":
            if ey1 <= pos_px <= ey2:
                return True
        else:  # vertical
            if ex1 <= pos_px <= ex2:
                return True
    return False


def _sample_crease_params(
    rng: random.Random,
    n: int,
    img_w: int,
    img_h: int,
    safe_zones: List[SafeZone],
) -> List[dict]:
    """
    采样 n 条折痕的方向和位置参数（Rejection Sampling）。

    策略：
      - 折痕位置限制在图像 15%–85% 之间（比边缘留更多空间）
      - 多条折痕之间同轴间距 > 20%
      - Rejection Sampling：折痕位置不得落在任何 SafeZone 的对应轴范围内
      - 最多重试 _MAX_SAMPLE_TRIES 次（每条折痕独立计算）
      - 必须满足 n 条数量：若某次找不到合法位置，降级到全图随机（忽略间距约束）
        宁可两条折痕靠近，也要保证数量；仍找不到才放弃（宁可少一条也不违反保护区）
    """
    params = []
    used_positions: List[Tuple[str, float]] = []

    for crease_idx in range(n):
        found = False

        # 阶段1：标准采样（带间距约束 + 保护区约束）
        for _ in range(_MAX_SAMPLE_TRIES):
            axis = rng.choice(["horizontal", "vertical"])
            pos_frac = rng.uniform(0.15, 0.85)
            pos_px = pos_frac * (img_h if axis == "horizontal" else img_w)

            too_close = any(
                a == axis and abs(p - pos_frac) < 0.20
                for a, p in used_positions
            )
            if too_close:
                continue

            if _line_conflicts_safe_zones(axis, pos_px, img_w, img_h, safe_zones):
                continue

            # 合法位置，接受
            found = True
            used_positions.append((axis, pos_frac))
            break

        if not found:
            # 阶段2：放宽间距约束，仍保持保护区约束
            for _ in range(_MAX_SAMPLE_TRIES):
                axis = rng.choice(["horizontal", "vertical"])
                pos_frac = rng.uniform(0.10, 0.90)
                pos_px = pos_frac * (img_h if axis == "horizontal" else img_w)

                if _line_conflicts_safe_zones(axis, pos_px, img_w, img_h, safe_zones):
                    continue

                found = True
                used_positions.append((axis, pos_frac))
                break

        if not found:
            # 无论如何找不到合法位置，跳过此条折痕
            # 宁可少一条折痕，也不让折痕穿过核心数据区
            continue

        # 随机高光方向（迎光面）
        specular_side = rng.choice(["positive", "negative"])

        params.append({
            "axis":         axis,
            "pos_frac":     pos_frac,

            # 指数光照渐变
            "grad_width":   rng.randint(65, 90),
            "bright_side":  rng.uniform(1.04, 1.11),
            "dark_side":    rng.uniform(0.74, 0.90),
            "grad_decay":   rng.uniform(3.0, 6.0),
            "specular_side": specular_side,

            # 折叠棱角高光细线
            "spec_width":   rng.uniform(1.5, 4.0),
            "spec_offset":  rng.uniform(2.0, 5.0),
            "spec_bright":  rng.uniform(1.08, 1.22),
            "spec_blur":    rng.uniform(1.0, 2.5),

            # 压痕细线
            "line_width":   rng.randint(1, 3),
            "line_dark":    rng.uniform(0.62, 0.80),
            "line_blur":    rng.uniform(0.8, 1.8),

            # 正弦扰动
            "wiggle_amp":   rng.uniform(0.5, 2.0),
            "wiggle_freq":  rng.uniform(0.008, 0.025),
            "wiggle_phase": rng.uniform(0, 2 * math.pi),
        })

    return params


# ═══════════════════════════════════════════════════════════════════════════════
# 单条折痕渲染
# ═══════════════════════════════════════════════════════════════════════════════

def _apply_single_crease(
    arr: "numpy.ndarray",
    p: dict,
) -> "numpy.ndarray":
    """
    依次应用三层纯光照效果（不移动任何像素，文字位置完全不受影响）：
      1. 指数光照渐变（弯曲纸面的光照变化）
      2. 折叠棱角高光细线（镜面反射感）
      3. 压痕暗线（纸纤维压损）
    """
    arr = _render_lighting_gradient(arr, p)
    arr = _render_specular_highlight(arr, p)
    arr = _render_crease_line(arr, p)
    return arr


# ═══════════════════════════════════════════════════════════════════════════════
# 子步骤 1：指数光照渐变
# ═══════════════════════════════════════════════════════════════════════════════

def _render_lighting_gradient(
    arr: "numpy.ndarray",
    p: dict,
) -> "numpy.ndarray":
    """
    折痕弯曲面的光照变化：

    物理原理：
      - 折叠后纸面产生两个斜面，一个斜面朝向光源（变亮），另一个背对（变暗）
      - 弯曲越接近折痕处角度越大，光照变化越强（指数衰减而非线性）

    实现：
      - bright_side（迎光侧）：亮度系数从 bright_side（折痕处）衰减至 1.0（远端）
      - dark_side（背光侧）：亮度系数从 dark_side（折痕处）衰减至 1.0（远端）
      - 衰减函数：exp(-decay * dist / grad_width)，速率由 grad_decay 控制
    """
    import numpy as np

    h, w = arr.shape[:2]
    axis = p["axis"]
    grad_width = p["grad_width"]
    bright = p["bright_side"]
    dark = p["dark_side"]
    decay = p["grad_decay"]
    specular_side = p["specular_side"]  # "positive"=下/右 侧为迎光面

    if axis == "horizontal":
        pos = p["pos_frac"] * h
        indices = np.arange(h, dtype=np.float32)
        dist = indices - pos                    # 负=上方，正=下方
    else:
        pos = p["pos_frac"] * w
        indices = np.arange(w, dtype=np.float32)
        dist = indices - pos                    # 负=左方，正=右方

    abs_dist = np.abs(dist)
    # 指数衰减系数（0=折痕处，1=远端）
    t = np.exp(-decay * abs_dist / max(grad_width, 1))

    coeff = np.ones(len(indices), dtype=np.float32)

    if specular_side == "positive":
        # positive 侧（下/右）为迎光面 → 提亮
        # negative 侧（上/左）为背光面 → 压暗
        for i, d in enumerate(dist):
            if d > 0 and abs_dist[i] <= grad_width:
                coeff[i] = 1.0 + (bright - 1.0) * t[i]
            elif d < 0 and abs_dist[i] <= grad_width:
                coeff[i] = 1.0 + (dark - 1.0) * t[i]
    else:
        # negative 侧（上/左）为迎光面 → 提亮
        # positive 侧（下/右）为背光面 → 压暗
        for i, d in enumerate(dist):
            if d < 0 and abs_dist[i] <= grad_width:
                coeff[i] = 1.0 + (bright - 1.0) * t[i]
            elif d > 0 and abs_dist[i] <= grad_width:
                coeff[i] = 1.0 + (dark - 1.0) * t[i]

    if axis == "horizontal":
        mult = coeff[:, np.newaxis, np.newaxis]   # (H, 1, 1)
    else:
        mult = coeff[np.newaxis, :, np.newaxis]   # (1, W, 1)

    return np.clip(arr * mult, 0.0, 255.0)


# ═══════════════════════════════════════════════════════════════════════════════
# 子步骤 2：折叠棱角高光细线
# ═══════════════════════════════════════════════════════════════════════════════

def _render_specular_highlight(
    arr: "numpy.ndarray",
    p: dict,
) -> "numpy.ndarray":
    """
    折叠棱角高光细线（镜面反射）。

    物理原理：
      当纸张折叠时，折痕棱角处的纸面朝向正好对准光源，产生比周围更亮的
      镜面反射高光。这条高光细线是折叠三维感最强的视觉线索。

    实现：
      - 在折痕迎光侧 spec_offset px 处放置宽度为 spec_width 的高光细线
      - 亮度系数为 spec_bright（略高于迎光侧渐变的最大值）
      - 带正弦扰动（复用折痕主线的扰动参数），避免生硬直线
      - 高斯软化边缘
    """
    import numpy as np
    from PIL import Image as PILImage, ImageFilter

    h, w = arr.shape[:2]
    axis = p["axis"]
    specular_side = p["specular_side"]
    spec_offset = p["spec_offset"]
    spec_half_w = p["spec_width"] / 2.0
    spec_bright = p["spec_bright"]
    spec_blur = p["spec_blur"]
    wiggle_amp = p["wiggle_amp"] * 0.6   # 高光线扰动幅度略小于暗线
    wiggle_freq = p["wiggle_freq"]
    wiggle_phase = p["wiggle_phase"] + math.pi  # 与暗线反相，更自然

    mask = np.zeros((h, w), dtype=np.float32)

    # 迎光侧偏移方向
    side_sign = 1.0 if specular_side == "positive" else -1.0

    if axis == "horizontal":
        base_pos = p["pos_frac"] * h + side_sign * spec_offset
        for j in range(w):
            sp_y = base_pos + wiggle_amp * math.sin(wiggle_freq * j + wiggle_phase)
            for i in range(h):
                dist = abs(i - sp_y)
                if dist <= spec_half_w + 2:
                    mask[i, j] = max(0.0, 1.0 - dist / (spec_half_w + 1e-6))
    else:
        base_pos = p["pos_frac"] * w + side_sign * spec_offset
        for i in range(h):
            sp_x = base_pos + wiggle_amp * math.sin(wiggle_freq * i + wiggle_phase)
            for j in range(w):
                dist = abs(j - sp_x)
                if dist <= spec_half_w + 2:
                    mask[i, j] = max(0.0, 1.0 - dist / (spec_half_w + 1e-6))

    if spec_blur > 0.3:
        mask_img = PILImage.fromarray((mask * 255).astype(np.uint8), mode="L")
        mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=spec_blur))
        mask = np.array(mask_img, dtype=np.float32) / 255.0

    # 高光：原色向 spec_bright 方向提亮
    a = mask[:, :, np.newaxis]
    brightened = np.clip(arr * spec_bright, 0.0, 255.0)
    return arr * (1.0 - a) + brightened * a


# ═══════════════════════════════════════════════════════════════════════════════
# 子步骤 3：压痕暗线
# ═══════════════════════════════════════════════════════════════════════════════

def _render_crease_line(
    arr: "numpy.ndarray",
    p: dict,
) -> "numpy.ndarray":
    """
    折痕处的压痕暗线。

    物理原理：折叠处纸纤维受压变暗，形成细线状暗区。

    实现：
      - 宽度 line_width px 的高斯形截面暗线
      - 正弦扰动（不像画出来的直线）
      - 少量暗棕偏色（纸纤维压损的色调变化）
      - 高斯软化边缘
    """
    import numpy as np
    from PIL import Image as PILImage, ImageFilter

    h, w = arr.shape[:2]
    axis = p["axis"]
    half_w = p["line_width"] / 2.0
    dark = p["line_dark"]
    blur_r = p["line_blur"]
    wiggle_amp = p["wiggle_amp"]
    wiggle_freq = p["wiggle_freq"]
    wiggle_phase = p["wiggle_phase"]

    mask = np.zeros((h, w), dtype=np.float32)

    if axis == "horizontal":
        base_pos = p["pos_frac"] * h
        for j in range(w):
            crease_y = base_pos + wiggle_amp * math.sin(wiggle_freq * j + wiggle_phase)
            for i in range(h):
                dist = abs(i - crease_y)
                if dist <= half_w + 2:
                    mask[i, j] = max(0.0, 1.0 - dist / (half_w + 1e-6))
    else:
        base_pos = p["pos_frac"] * w
        for i in range(h):
            crease_x = base_pos + wiggle_amp * math.sin(wiggle_freq * i + wiggle_phase)
            for j in range(w):
                dist = abs(j - crease_x)
                if dist <= half_w + 2:
                    mask[i, j] = max(0.0, 1.0 - dist / (half_w + 1e-6))

    if blur_r > 0.3:
        mask_img = PILImage.fromarray((mask * 255).astype(np.uint8), mode="L")
        mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=blur_r))
        mask = np.array(mask_img, dtype=np.float32) / 255.0

    # 折痕暗棕色调（纸纤维压损）
    crease_tint = np.array([155.0, 140.0, 120.0], dtype=np.float32)

    a = mask[:, :, np.newaxis]
    darkened = arr * dark + crease_tint * (1.0 - dark)
    return np.clip(arr * (1.0 - a) + darkened * a, 0.0, 255.0)
