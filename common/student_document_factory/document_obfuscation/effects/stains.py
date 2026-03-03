"""
document_obfuscation.effects.stains — 文档污渍效果

实现三种物理污渍子类型：

  mud     — 泥块：深棕不规则斑块，多层重叠椭圆 + 模糊边缘
  wear    — 磨损：纸面局部变浅/褪白，纹理感
  fading  — 掉色：局部向灰偏移，饱和度降低，仅限 student_id

设计原则：
  - 确定性：使用传入的 rng（由 student_id 派生），相同 seed 必定相同结果
  - Rejection Sampling：污渍中心在整图范围内随机采样，自动绕开所有 SafeZone
    （核心数据区）；全部候选被排除则跳过该污渍，宁可少污渍也不遮挡关键信息
  - 通用性：safe_zones 由调用方传入，stains.py 无需知道文档细节
  - 效果叠加自然：各污渍独立蒙版，顺序为 mud → wear → fading
"""

import random
from typing import List, Optional, Tuple

from PIL import Image

from ..safe_zone import SafeZone

# ── 类型别名 ────────────────────────────────────────────────────────────────────
Color = Tuple[int, int, int]

# Rejection Sampling 最大重试次数
_MAX_SAMPLE_TRIES = 50


# ═══════════════════════════════════════════════════════════════════════════════
# 公开入口
# ═══════════════════════════════════════════════════════════════════════════════

def apply_stains(
    img: Image.Image,
    rng: random.Random,
    doc_type: str = "",
    safe_zones: Optional[List[SafeZone]] = None,
) -> Image.Image:
    """
    对图像应用污渍效果（主入口）。

    Args:
        img:        输入 PIL 图像（RGB）。
        rng:        确定性随机数生成器（由调用方以 student_id 作为 seed 创建）。
        doc_type:   文档类型字符串（"student_id" / "transcript" / "invoice" / ""）。
                    fading 仅限 student_id，其余子类型全部文档均支持。
        safe_zones: 核心数据保护区列表。污渍中心通过 Rejection Sampling 自动绕开
                    所有保护区。None 或空列表表示无保护区约束（污渍可出现在任意位置）。

    Returns:
        应用污渍后的 PIL 图像（RGB）。
    """
    try:
        import numpy as np
    except ImportError:
        return img

    zones: List[SafeZone] = safe_zones or []
    params = _sample_stain_params(rng, doc_type, img.size, zones)
    if not params:
        return img

    arr = _to_float32(np.array(img.convert("RGB")))
    for p in params:
        if p["type"] == "mud":
            arr = _apply_mud(arr, p, rng)
        elif p["type"] == "wear":
            arr = _apply_wear(arr, p, rng)
        elif p["type"] == "fading":
            arr = _apply_fading(arr, p, rng)

    return Image.fromarray(_to_uint8(arr))


# ═══════════════════════════════════════════════════════════════════════════════
# 中心采样（Rejection Sampling）
# ═══════════════════════════════════════════════════════════════════════════════

def _sample_center(
    rng: random.Random,
    img_w: int,
    img_h: int,
    rx: int,
    ry: int,
    safe_zones: List[SafeZone],
) -> Optional[Tuple[int, int]]:
    """
    在整图范围内随机采样污渍中心，自动绕开所有 SafeZone。

    采样范围：[rx, w-rx] × [ry, h-ry]，确保椭圆不超出图像边界。
    最多重试 _MAX_SAMPLE_TRIES 次；全部失败返回 None（跳过此污渍）。
    """
    lo_x = rx
    hi_x = max(lo_x + 1, img_w - rx)
    lo_y = ry
    hi_y = max(lo_y + 1, img_h - ry)

    for _ in range(_MAX_SAMPLE_TRIES):
        cx = rng.randint(lo_x, hi_x)
        cy = rng.randint(lo_y, hi_y)
        if not any(z.conflicts(cx, cy, rx, ry) for z in safe_zones):
            return cx, cy
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# 参数采样
# ═══════════════════════════════════════════════════════════════════════════════

def _sample_stain_params(
    rng: random.Random,
    doc_type: str,
    img_size: Tuple[int, int],
    safe_zones: List[SafeZone],
) -> List[dict]:
    """
    根据 RNG 确定性地决定本次出现哪些污渍类型及各自参数。

    策略：
      - 用 3 个独立随机数分别判断 mud / wear / fading 是否出现
      - fading 仅在 doc_type == "student_id" 时才参与判断
      - 至少保证 1 种出现（若全部抽中不出现，则强制 mud 出现）
      - 各参数通过 _sample_center() Rejection Sampling 确定中心位置
      - 若某类型找不到合法中心则跳过（宁可少污渍也不遮挡关键字段）
    """
    is_student_id = doc_type == "student_id"
    w, h = img_size

    has_mud    = rng.random() < 0.75   # 75% 概率
    has_wear   = rng.random() < 0.55   # 55% 概率
    has_fading = (rng.random() < 0.50) if is_student_id else False  # 50%，仅学生证

    # 保证至少一种出现
    if not (has_mud or has_wear or has_fading):
        has_mud = True

    params = []
    if has_mud:
        p = _mud_params(rng, w, h, safe_zones)
        if p is not None:
            params.append(p)
    if has_wear:
        p = _wear_params(rng, w, h, safe_zones)
        if p is not None:
            params.append(p)
    if has_fading:
        p = _fading_params(rng, w, h, safe_zones)
        if p is not None:
            params.append(p)

    return params


def _mud_params(
    rng: random.Random,
    img_w: int,
    img_h: int,
    safe_zones: List[SafeZone],
) -> Optional[dict]:
    """采样泥块污渍参数；若找不到合法中心返回 None"""
    rx = rng.randint(50, 140)
    ry = rng.randint(40, 110)
    center = _sample_center(rng, img_w, img_h, rx, ry, safe_zones)
    if center is None:
        return None
    cx, cy = center
    return {
        "type":    "mud",
        "cx":      cx,
        "cy":      cy,
        "rx":      rx,
        "ry":      ry,
        "layers":  rng.randint(4, 8),
        "opacity": rng.uniform(0.50, 0.82),
        "blur_r":  rng.randint(3, 7),
        "color": (
            rng.randint(25, 75),   # R — 深棕
            rng.randint(15, 55),   # G
            rng.randint(3,  28),   # B
        ),
    }


def _wear_params(
    rng: random.Random,
    img_w: int,
    img_h: int,
    safe_zones: List[SafeZone],
) -> Optional[dict]:
    """采样磨损污渍参数；若找不到合法中心返回 None"""
    rx = rng.randint(60, 140)
    ry = rng.randint(50, 110)
    center = _sample_center(rng, img_w, img_h, rx, ry, safe_zones)
    if center is None:
        return None
    cx, cy = center
    return {
        "type":      "wear",
        "cx":        cx,
        "cy":        cy,
        "rx":        rx,
        "ry":        ry,
        "opacity":   rng.uniform(0.40, 0.70),
        "noise_amt": rng.uniform(20.0, 50.0),
        "blur_r":    rng.randint(8, 16),
    }


def _fading_params(
    rng: random.Random,
    img_w: int,
    img_h: int,
    safe_zones: List[SafeZone],
) -> Optional[dict]:
    """采样掉色污渍参数（仅学生证）；若找不到合法中心返回 None"""
    rx = rng.randint(70, 150)
    ry = rng.randint(60, 120)
    center = _sample_center(rng, img_w, img_h, rx, ry, safe_zones)
    if center is None:
        return None
    cx, cy = center
    return {
        "type":       "fading",
        "cx":         cx,
        "cy":         cy,
        "rx":         rx,
        "ry":         ry,
        "sat_factor": rng.uniform(0.02, 0.25),
        "val_factor": rng.uniform(0.50, 0.78),
        "opacity":    rng.uniform(0.55, 0.85),
        "blur_r":     rng.randint(10, 20),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 效果实现：mud（泥块）
# ═══════════════════════════════════════════════════════════════════════════════

def _apply_mud(
    arr,
    p: dict,
    rng: random.Random,
) -> "numpy.ndarray":
    """
    泥块效果：
      - 多层略偏移的高斯椭圆蒙版叠加，形成不规则边界
      - 边缘经高斯模糊软化
      - 颜色为深棕黑，叠加到图像指定位置
    """
    import numpy as np
    from PIL import Image, ImageFilter

    h, w = arr.shape[:2]
    cx, cy = p["cx"], p["cy"]

    # 累积蒙版（多层叠加）
    combined_mask = np.zeros((h, w), dtype=np.float32)
    for _ in range(p["layers"]):
        ox = rng.randint(-p["rx"] // 3, p["rx"] // 3)
        oy = rng.randint(-p["ry"] // 3, p["ry"] // 3)
        combined_mask += _gaussian_ellipse(h, w, cx + ox, cy + oy, p["rx"], p["ry"])

    # 归一化 + 截断
    combined_mask = np.clip(combined_mask / p["layers"] * 1.5, 0.0, 1.0)

    # PIL 模糊软化边缘
    mask_img = Image.fromarray((combined_mask * 255).astype(np.uint8), mode="L")
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=p["blur_r"]))
    combined_mask = np.array(mask_img, dtype=np.float32) / 255.0

    # 应用不透明度并混合
    alpha = combined_mask[:, :, np.newaxis] * p["opacity"]
    mud_color = np.array(p["color"], dtype=np.float32)
    arr = arr * (1.0 - alpha) + mud_color * alpha

    return arr


# ═══════════════════════════════════════════════════════════════════════════════
# 效果实现：wear（磨损）
# ═══════════════════════════════════════════════════════════════════════════════

def _apply_wear(
    arr,
    p: dict,
    rng: random.Random,
) -> "numpy.ndarray":
    """
    磨损效果：
      - 椭圆区域内像素向白色方向偏移
      - 叠加细微随机噪声模拟纸纤维感
      - 高斯椭圆蒙版控制过渡
    """
    import numpy as np
    from PIL import Image, ImageFilter

    h, w = arr.shape[:2]
    cx, cy = p["cx"], p["cy"]

    mask = _gaussian_ellipse(h, w, cx, cy, p["rx"], p["ry"])

    # 模糊软化
    mask_img = Image.fromarray((mask * 255).astype(np.uint8), mode="L")
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=p["blur_r"]))
    mask = np.array(mask_img, dtype=np.float32) / 255.0

    # 细微白色噪声（纸纤维）
    rs = _make_rs(rng)
    noise = rs.normal(0, p["noise_amt"], (h, w, 1)).astype(np.float32)
    noise = np.clip(noise, 0, None)  # 只增亮

    # 向白色(255)方向强力提亮
    alpha = mask[:, :, np.newaxis] * p["opacity"]
    white = np.full_like(arr, 255.0)
    arr = arr * (1.0 - alpha) + (arr + noise) * alpha
    arr = arr * (1.0 - alpha * 0.60) + white * (alpha * 0.60)

    return arr


# ═══════════════════════════════════════════════════════════════════════════════
# 效果实现：fading（掉色，仅学生证）
# ═══════════════════════════════════════════════════════════════════════════════

def _apply_fading(
    arr,
    p: dict,
    rng: random.Random,
) -> "numpy.ndarray":
    """
    掉色效果：
      - 椭圆区域内降低饱和度（向灰偏移）+ 轻微降低明度
      - 在 HSV 空间操作，保留色调
      - 高斯蒙版控制边缘过渡
    """
    import numpy as np
    from PIL import Image, ImageFilter

    h, w = arr.shape[:2]
    cx, cy = p["cx"], p["cy"]

    mask = _gaussian_ellipse(h, w, cx, cy, p["rx"], p["ry"])

    # 模糊软化
    mask_img = Image.fromarray((mask * 255).astype(np.uint8), mode="L")
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=p["blur_r"]))
    mask = np.array(mask_img, dtype=np.float32) / 255.0

    alpha = mask * p["opacity"]  # (H, W)

    # 在 HSV 空间降低饱和度
    from PIL import Image as PILImage
    img_pil = PILImage.fromarray(_to_uint8(arr)).convert("HSV")
    hsv = np.array(img_pil, dtype=np.float32)

    # S 通道衰减（降饱和）
    hsv[:, :, 1] = hsv[:, :, 1] * (1.0 - alpha * (1.0 - p["sat_factor"]))
    # V 通道衰减（轻微压暗）
    hsv[:, :, 2] = hsv[:, :, 2] * (1.0 - alpha * (1.0 - p["val_factor"]))

    hsv = np.clip(hsv, 0, 255).astype(np.uint8)
    faded = np.array(PILImage.fromarray(hsv, mode="HSV").convert("RGB"),
                     dtype=np.float32)

    # 将掉色结果与原图按 alpha 混合
    a3 = alpha[:, :, np.newaxis]
    arr = arr * (1.0 - a3) + faded * a3

    return arr


# ═══════════════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════════════

def _gaussian_ellipse(
    h: int,
    w: int,
    cx: float,
    cy: float,
    rx: int,
    ry: int,
) -> "numpy.ndarray":
    """生成一个归一化高斯椭圆蒙版 [0, 1]，中心为 (cx, cy)"""
    import numpy as np
    ys, xs = np.ogrid[:h, :w]
    dist = ((xs - cx) / max(rx, 1)) ** 2 + ((ys - cy) / max(ry, 1)) ** 2
    return np.exp(-dist * 2.0).astype(np.float32)


def _make_rs(rng: random.Random) -> "numpy.random.RandomState":
    """从 rng 创建 numpy RandomState（保证确定性）"""
    import numpy as np
    return np.random.RandomState(rng.randint(0, 2 ** 31 - 1))


def _to_float32(arr: "numpy.ndarray") -> "numpy.ndarray":
    return arr.astype("float32")


def _to_uint8(arr: "numpy.ndarray") -> "numpy.ndarray":
    import numpy as np
    return np.clip(arr, 0, 255).astype(np.uint8)
