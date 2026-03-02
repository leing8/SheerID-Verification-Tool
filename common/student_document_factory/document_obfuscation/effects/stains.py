"""
document_obfuscation.effects.stains — 文档污渍效果

实现三种物理污渍子类型，所有文档均支持，通过唯一 ID 确定性决定组合：

  mud     — 泥块：深棕不规则斑块，多层重叠椭圆 + 模糊边缘，支持全部文档
  wear    — 磨损：纸面局部变浅/褪白，纹理感，支持全部文档
  fading  — 掉色：局部向灰偏移，饱和度降低，仅限 student_id

设计原则：
  - 确定性：使用传入的 rng（由 student_id 派生），相同 seed 必定相同结果
  - 从唯一ID确定是否出现每种污渍（独立 bit 判断），至少保证 1 种出现
  - 污渍中心约束在图像边缘 20% 区域，不遮挡核心信息字段
  - 效果叠加自然：各污渍独立蒙版，顺序为 mud → wear → fading
"""

import random
from typing import List, Tuple

from PIL import Image

# ── 类型别名 ────────────────────────────────────────────────────────────────────
Color = Tuple[int, int, int]


# ═══════════════════════════════════════════════════════════════════════════════
# 公开入口
# ═══════════════════════════════════════════════════════════════════════════════

def apply_stains(
    img: Image.Image,
    rng: random.Random,
    doc_type: str = "",
) -> Image.Image:
    """
    对图像应用污渍效果（主入口）。

    Args:
        img:       输入 PIL 图像（RGB）。
        rng:       确定性随机数生成器（由调用方以 student_id 作为 seed 创建）。
        doc_type:  文档类型字符串（"student_id" / "transcript" / "invoice" / ""）。
                   fading 仅限 student_id，其余子类型全部文档均支持。

    Returns:
        应用污渍后的 PIL 图像（RGB）。
    """
    try:
        import numpy as np
    except ImportError:
        return img

    params = _sample_stain_params(rng, doc_type)
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
# 参数采样
# ═══════════════════════════════════════════════════════════════════════════════

def _sample_stain_params(
    rng: random.Random,
    doc_type: str,
) -> List[dict]:
    """
    根据 RNG 确定性地决定本次出现哪些污渍类型及各自参数。

    策略：
      - 用 3 个独立随机数分别判断 mud / wear / fading 是否出现
      - fading 仅在 doc_type == "student_id" 时才参与判断
      - 至少保证 1 种出现（若全部抽中不出现，则强制 mud 出现）
      - 每种出现的类型固定生成 1 个实例
    """
    is_student_id = doc_type == "student_id"

    # 独立概率判断各类型是否出现
    has_mud    = rng.random() < 0.75   # 75% 概率
    has_wear   = rng.random() < 0.55   # 55% 概率
    has_fading = (rng.random() < 0.50) if is_student_id else False  # 50%，仅学生证

    # 保证至少一种出现
    if not (has_mud or has_wear or has_fading):
        has_mud = True

    params = []
    if has_mud:
        params.append(_mud_params(rng))
    if has_wear:
        params.append(_wear_params(rng))
    if has_fading:
        params.append(_fading_params(rng))

    return params


def _mud_params(rng: random.Random, corner: str | None = None) -> dict:
    """采样泥块污渍参数"""
    if corner is None:
        corner = rng.choice(["tl", "tr", "bl", "br"])
    return {
        "type":    "mud",
        "corner":  corner,
        "rx":      rng.randint(50, 140),      # 椭圆 x 半径（明显更大）
        "ry":      rng.randint(40, 110),      # 椭圆 y 半径
        "layers":  rng.randint(4, 8),         # 更多层数，更不规则
        "opacity": rng.uniform(0.50, 0.82),   # 大幅提高不透明度（原 0.20~0.45）
        "blur_r":  rng.randint(3, 7),         # 较小模糊 → 边缘更粗糙
        # 泥块颜色：深棕 / 黑棕，深色调
        "color": (
            rng.randint(25, 75),   # R — 深棕
            rng.randint(15, 55),   # G
            rng.randint(3,  28),   # B
        ),
    }


def _wear_params(rng: random.Random, corner: str | None = None) -> dict:
    """采样磨损污渍参数"""
    if corner is None:
        corner = rng.choice(["tl", "tr", "bl", "br"])
    return {
        "type":      "wear",
        "corner":    corner,
        "rx":        rng.randint(60, 140),      # 更大范围区域
        "ry":        rng.randint(50, 110),
        "opacity":   rng.uniform(0.40, 0.70),   # 更强（原 0.12~0.30）
        "noise_amt": rng.uniform(20.0, 50.0),   # 更强纸纤维噪声（原 8~20）
        "blur_r":    rng.randint(8, 16),
    }


def _fading_params(rng: random.Random, corner: str | None = None) -> dict:
    """采样掉色污渍参数（仅学生证）"""
    if corner is None:
        corner = rng.choice(["tl", "tr", "bl", "br"])
    return {
        "type":       "fading",
        "corner":     corner,
        "rx":         rng.randint(70, 150),
        "ry":         rng.randint(60, 120),
        "sat_factor": rng.uniform(0.02, 0.25),  # 几乎完全去色（原 0.20~0.55）
        "val_factor": rng.uniform(0.50, 0.78),  # 明显压暗（原 0.70~0.92）
        "opacity":    rng.uniform(0.55, 0.85),  # 更深混合（原 0.25~0.50）
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
      - 颜色为深棕黑，叠加到图像角落
    """
    import numpy as np
    from PIL import Image, ImageFilter

    h, w = arr.shape[:2]
    cx, cy = _corner_center(p["corner"], w, h, p["rx"], p["ry"])

    # 累积蒙版（多层叠加）
    combined_mask = np.zeros((h, w), dtype=np.float32)
    for _ in range(p["layers"]):
        ox = rng.randint(-p["rx"] // 3, p["rx"] // 3)
        oy = rng.randint(-p["ry"] // 3, p["ry"] // 3)
        lx = cx + ox
        ly = cy + oy
        combined_mask += _gaussian_ellipse(h, w, lx, ly, p["rx"], p["ry"])

    # 归一化 + 截断
    combined_mask = np.clip(combined_mask / p["layers"] * 1.5, 0.0, 1.0)

    # PIL 模糊软化边缘
    mask_img = Image.fromarray((combined_mask * 255).astype(np.uint8), mode="L")
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=p["blur_r"]))
    combined_mask = np.array(mask_img, dtype=np.float32) / 255.0

    # 应用不透明度
    alpha = combined_mask[:, :, np.newaxis] * p["opacity"]

    # 混合：arr * (1 - alpha) + mud_color * alpha
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
    cx, cy = _corner_center(p["corner"], w, h, p["rx"], p["ry"])

    mask = _gaussian_ellipse(h, w, cx, cy, p["rx"], p["ry"])

    # 模糊软化
    mask_img = Image.fromarray((mask * 255).astype(np.uint8), mode="L")
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=p["blur_r"]))
    mask = np.array(mask_img, dtype=np.float32) / 255.0

    # 细微白色噪声（纸纤维）
    rs = _make_rs(rng)
    noise = rs.normal(0, p["noise_amt"], (h, w, 1)).astype(np.float32)
    noise = np.clip(noise, 0, None)  # 只增亮

    # 向白色(255)方向强力提亮（原 alpha*0.3 → alpha*0.60）
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
    cx, cy = _corner_center(p["corner"], w, h, p["rx"], p["ry"])

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

def _corner_center(
    corner: str,
    w: int,
    h: int,
    rx: int,
    ry: int,
) -> Tuple[int, int]:
    """
    根据角落标识计算污渍中心坐标。
    中心约束在距对应边 20% 以内（最大短边的 20%），确保主体内容不被遮挡。
    """
    edge_x = max(rx, int(w * 0.20))
    edge_y = max(ry, int(h * 0.20))

    if corner == "tl":
        return edge_x, edge_y
    elif corner == "tr":
        return w - edge_x, edge_y
    elif corner == "bl":
        return edge_x, h - edge_y
    else:  # br
        return w - edge_x, h - edge_y


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
