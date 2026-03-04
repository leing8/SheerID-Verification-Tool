"""
document_obfuscation.effects.background_scene — 背景场景叠加效果

模拟用户将文档放置在桌面/地毯/其他物品上用手机拍照的视觉效果。

核心流程：
  1. 生成背景纹理（木纹 / 深色桌面 / 白色桌面 / 布面 / 纯色）
  2. 计算并渲染柔和投影阴影
  3. 将文档（已由 transform_3d 完成透视变换）粘贴到背景中央（允许轻微偏移）
  4. 对背景可见区域叠加轻微光照渐变，使整体更自然

注意：
  3D 透视变换（yaw/pitch/roll 相机角度模拟）已独立移至 transform_3d.py，
  本模块仅负责背景生成与文档合成。流水线顺序：
    stains → creases → crop → transform_3d → background_scene → photo_sim

设计约束（基于 SheerID 官方文档）：
  - 文档四边均可见，不截断关键信息
  - 背景与文档形成明显色彩对比
  - 文档内部像素质量不受背景效果干扰
"""

from __future__ import annotations

import random

from PIL import Image, ImageFilter

# ── 背景类型定义 ────────────────────────────────────────────────────────────────
# (type_name, weight)  权重决定各类型出现概率
_BG_TYPES: list[tuple[str, float]] = [
    ("desk_wood",  0.30),   # 浅木纹桌面（最常见）
    ("desk_dark",  0.25),   # 深色桌面（对比最强，有利文档识别）
    ("desk_white", 0.20),   # 白色/浅灰桌面
    ("carpet",     0.15),   # 地毯/布面纹理
    ("notebook",   0.10),   # 笔记本/杂志背面（纯色）
]


# ══════════════════════════════════════════════════════════════════════════════
# 公共入口
# ══════════════════════════════════════════════════════════════════════════════

def apply_background_scene(
    img: Image.Image,
    rng: random.Random,
    doc_type: str = "",
) -> Image.Image:
    """
    在文档外叠加背景场景，模拟桌面拍照效果。

    注意：本函数期望接收已经过 transform_3d 透视变换的图像（RGB）。
    若 pipeline 中 transform_3d=False，则接收原始 RGB 文档图像。

    Args:
        img:      输入 PIL 图像（RGB），已完成透视变换的文档。
        rng:      确定性随机数生成器（由调用方传入）。
        doc_type: 文档类型（当前未使用，预留扩展）。

    Returns:
        包含背景的新 PIL 图像（RGB），尺寸约为原图的 1.12×～1.28×。
    """
    try:
        import numpy as np
    except ImportError:
        return img  # numpy 不可用时直接返回原图

    doc_w, doc_h = img.size

    # ── 1. 选择背景类型并生成背景 ─────────────────────────────────────────────
    bg_type = _choose_bg_type(rng)
    bg_scale = rng.uniform(1.12, 1.28)          # 背景比文档大 12%～28%
    bg_w = int(doc_w * bg_scale)
    bg_h = int(doc_h * bg_scale)
    background = _generate_background(bg_type, bg_w, bg_h, rng)

    # ── 2. 计算文档粘贴位置（居中 + 轻微随机偏移） ──────────────────────────
    offset_x = int((bg_w - doc_w) / 2 + rng.uniform(-0.03, 0.03) * bg_w)
    offset_y = int((bg_h - doc_h) / 2 + rng.uniform(-0.03, 0.03) * bg_h)
    # 防止越界
    offset_x = max(0, min(offset_x, bg_w - doc_w))
    offset_y = max(0, min(offset_y, bg_h - doc_h))

    # ── 3. 渲染投影阴影 ───────────────────────────────────────────────────────
    _paste_shadow(background, img, offset_x, offset_y, rng, np)

    # ── 4. 粘贴文档（RGB 直接粘贴）─────────────────────────────────────────
    _paste_doc(background, img, offset_x, offset_y)

    # ── 5. 背景区域光照后处理（轻微渐变，不增加噪声）────────────────────────
    background = _post_process_background(background, rng, np)

    return background


# ══════════════════════════════════════════════════════════════════════════════
# 背景生成
# ══════════════════════════════════════════════════════════════════════════════

def _choose_bg_type(rng: random.Random) -> str:
    types, weights = zip(*_BG_TYPES)
    return rng.choices(list(types), weights=list(weights), k=1)[0]


def _generate_background(
    bg_type: str, w: int, h: int, rng: random.Random
) -> Image.Image:
    """根据背景类型生成 RGB PIL Image"""
    import numpy as np

    rs = np.random.RandomState(rng.randint(0, 2**31 - 1))

    if bg_type == "desk_wood":
        return _bg_wood(w, h, rng, rs)
    elif bg_type == "desk_dark":
        return _bg_dark(w, h, rng, rs)
    elif bg_type == "desk_white":
        return _bg_white(w, h, rng, rs)
    elif bg_type == "carpet":
        return _bg_carpet(w, h, rng, rs)
    else:  # notebook
        return _bg_notebook(w, h, rng, rs)


def _bg_wood(w: int, h: int, rng: random.Random, rs) -> Image.Image:
    """浅木纹桌面：横向条纹 + 扰动（降低噪声）"""
    import numpy as np

    # 基础木色（浅棕）
    base_r = rng.randint(170, 200)
    base_g = rng.randint(130, 160)
    base_b = rng.randint(80, 110)

    arr = np.zeros((h, w, 3), dtype=np.float32)
    arr[:, :, 0] = base_r
    arr[:, :, 1] = base_g
    arr[:, :, 2] = base_b

    # 横向木纹条纹（y 方向低频正弦）
    grain_freq = rng.uniform(8, 20)          # 木纹条数
    grain_amp  = rng.uniform(15, 30)         # 明暗变化幅度
    y_idx = np.arange(h, dtype=np.float32)
    grain = np.sin(y_idx / h * np.pi * grain_freq) * grain_amp
    arr[:, :, 0] += grain[:, None]
    arr[:, :, 1] += grain[:, None] * 0.8
    arr[:, :, 2] += grain[:, None] * 0.4

    # 细粒噪声（已降低：6 → 3）
    noise = rs.normal(0, 3, (h, w, 3)).astype(np.float32)
    arr += noise

    # 随机斜向光影渐变（模拟窗光）
    light_dir = rng.choice(["lr", "rl", "tb"])
    if light_dir == "lr":
        g = np.linspace(0.92, 1.04, w)[None, :, None].astype(np.float32)
    elif light_dir == "rl":
        g = np.linspace(1.04, 0.92, w)[None, :, None].astype(np.float32)
    else:
        g = np.linspace(0.94, 1.02, h)[:, None, None].astype(np.float32)
    arr *= g

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _bg_dark(w: int, h: int, rng: random.Random, rs) -> Image.Image:
    """深色桌面：深棕/深灰，与白色文档对比最强（降低噪声）"""
    import numpy as np

    style = rng.choice(["dark_wood", "dark_gray", "dark_blue"])
    if style == "dark_wood":
        base = (rng.randint(45, 70), rng.randint(28, 45), rng.randint(12, 22))
    elif style == "dark_gray":
        v = rng.randint(40, 65)
        base = (v, v, v)
    else:
        base = (rng.randint(28, 45), rng.randint(35, 55), rng.randint(50, 75))

    arr = np.full((h, w, 3), base, dtype=np.float32)

    # 细纹（已降低：uniform(3,8) → uniform(2,5)）
    grain_amp = rng.uniform(2, 5)
    arr += rs.normal(0, grain_amp, (h, w, 3)).astype(np.float32)

    # 横纹（深色木纹）
    y_idx = np.arange(h, dtype=np.float32)
    grain_freq = rng.uniform(10, 25)
    grain = np.sin(y_idx / h * np.pi * grain_freq) * rng.uniform(3, 8)
    arr[:, :, 0] += grain[:, None]
    arr[:, :, 1] += grain[:, None] * 0.7
    arr[:, :, 2] += grain[:, None] * 0.4

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _bg_white(w: int, h: int, rng: random.Random, rs) -> Image.Image:
    """白色/浅灰桌面（降低噪声：3 → 2）"""
    import numpy as np

    v = rng.randint(230, 250)
    tint_r = rng.randint(-5, 5)
    tint_b = rng.randint(-5, 5)
    base = (
        max(0, min(255, v + tint_r)),
        v,
        max(0, min(255, v + tint_b)),
    )
    arr = np.full((h, w, 3), base, dtype=np.float32)
    arr += rs.normal(0, 2, (h, w, 3)).astype(np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _bg_carpet(w: int, h: int, rng: random.Random, rs) -> Image.Image:
    """地毯/布面：中等饱和色 + 细粒噪声（降低噪声：12 → 5）"""
    import numpy as np

    # 随机中性色（米色、蓝灰、绿灰…）
    palette = [
        (180, 165, 140),  # 米色
        (130, 145, 160),  # 蓝灰
        (140, 155, 135),  # 绿灰
        (160, 130, 125),  # 玫瑰灰
        (120, 120, 130),  # 中性灰
    ]
    base = rng.choice(palette)
    arr = np.full((h, w, 3), base, dtype=np.float32)

    # 高频噪声（织物颗粒感，已降低：12 → 5）
    arr += rs.normal(0, 5, (h, w, 3)).astype(np.float32)

    # 织物方向纹路（细横条 + 细竖条交织）
    y_pattern = (np.arange(h) % rng.randint(3, 6)).astype(np.float32) * 3
    x_pattern = (np.arange(w) % rng.randint(3, 6)).astype(np.float32) * 3
    arr[:, :, 0] += y_pattern[:, None] - x_pattern[None, :]
    arr[:, :, 1] += y_pattern[:, None] * 0.8
    arr[:, :, 2] += x_pattern[None, :] * 0.8

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _bg_notebook(w: int, h: int, rng: random.Random, rs) -> Image.Image:
    """笔记本封面/书桌杂志背面：纯色带极轻微噪声（降低：5 → 2）"""
    import numpy as np

    palette = [
        (80,  100, 140),   # 蓝色
        (60,  100,  80),   # 绿色
        (140,  70,  70),   # 红褐
        (100,  80, 130),   # 紫色
        ( 50,  50,  50),   # 黑色
        (200, 190, 170),   # 米黄
    ]
    base = rng.choice(palette)
    arr = np.full((h, w, 3), base, dtype=np.float32)
    arr += rs.normal(0, 2, (h, w, 3)).astype(np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# ══════════════════════════════════════════════════════════════════════════════
# 阴影 & 合成
# ══════════════════════════════════════════════════════════════════════════════

def _paste_shadow(
    background: Image.Image,
    doc_img: Image.Image,
    offset_x: int,
    offset_y: int,
    rng: random.Random,
    np,
) -> None:
    """
    在背景上绘制文档的柔和投影阴影（就地修改 background）。

    Shadow 实现：
      1. 基于文档尺寸创建矩形阴影蒙版
      2. 降低不透明度（shadow_opacity）得到灰色阴影层
      3. 高斯模糊（模拟阴影扩散）
      4. 偏移粘贴（模拟光源方向）
    """
    shadow_opacity   = rng.uniform(0.25, 0.45)
    shadow_blur      = rng.uniform(8, 18)
    # 光源方向决定阴影偏移
    shadow_dx = int(rng.uniform(4, 12))
    shadow_dy = int(rng.uniform(4, 12))

    doc_w, doc_h = doc_img.size

    # 提取或构造 Alpha 蒙版（RGB 文档使用全不透明蒙版）
    if doc_img.mode == "RGBA":
        alpha_ch = doc_img.split()[3]
    else:
        alpha_ch = Image.new("L", (doc_w, doc_h), 255)

    # 阴影 padding：为高斯模糊留出扩散空间（3× blur 半径覆盖 ~99.7% 能量）
    sh_pad = int(shadow_blur * 3) + 2
    padded_w = doc_w + sh_pad * 2
    padded_h = doc_h + sh_pad * 2
    padded_alpha = Image.new("L", (padded_w, padded_h), 0)
    padded_alpha.paste(alpha_ch, (sh_pad, sh_pad))

    # 将 alpha 映射为暗灰色阴影
    shadow_arr = np.array(padded_alpha, dtype=np.float32) * shadow_opacity
    shadow_gray = Image.fromarray(shadow_arr.clip(0, 255).astype(np.uint8), mode="L")
    shadow_gray = shadow_gray.filter(ImageFilter.GaussianBlur(radius=shadow_blur))

    # 在背景上合成阴影（背景像素变暗）
    bg_arr = np.array(background, dtype=np.float32)
    bg_h, bg_w = bg_arr.shape[:2]
    sh_arr = np.array(shadow_gray, dtype=np.float32) / 255.0

    # 阴影粘贴位置（考虑 padding 偏移 + 光源方向偏移）
    sh_x1 = offset_x + shadow_dx - sh_pad
    sh_y1 = offset_y + shadow_dy - sh_pad
    sh_x2 = sh_x1 + padded_w
    sh_y2 = sh_y1 + padded_h

    # 裁剪到背景范围内
    sx_start = max(0, sh_x1)
    sy_start = max(0, sh_y1)
    sx_end   = min(bg_w, sh_x2)
    sy_end   = min(bg_h, sh_y2)

    if sx_end > sx_start and sy_end > sy_start:
        sh_crop_x1 = sx_start - sh_x1
        sh_crop_y1 = sy_start - sh_y1
        sh_crop_x2 = sh_crop_x1 + (sx_end - sx_start)
        sh_crop_y2 = sh_crop_y1 + (sy_end - sy_start)

        sh_region = sh_arr[sh_crop_y1:sh_crop_y2, sh_crop_x1:sh_crop_x2]
        bg_region = bg_arr[sy_start:sy_end, sx_start:sx_end]
        # 阴影：背景变暗
        bg_arr[sy_start:sy_end, sx_start:sx_end] = (
            bg_region * (1.0 - sh_region[:, :, None] * 0.7)
        )

    bg_result = np.clip(bg_arr, 0, 255).astype(np.uint8)
    background.paste(Image.fromarray(bg_result))


def _paste_doc(
    background: Image.Image,
    doc_img: Image.Image,
    offset_x: int,
    offset_y: int,
) -> None:
    """将文档（RGB 或 RGBA）粘贴到背景上（就地修改 background）"""
    if doc_img.mode == "RGBA":
        # 用 Alpha 通道做蒙版合成，透明区域保留背景
        background.paste(doc_img.convert("RGB"), (offset_x, offset_y),
                         mask=doc_img.split()[3])
    else:
        background.paste(doc_img, (offset_x, offset_y))


# ══════════════════════════════════════════════════════════════════════════════
# 背景后处理（仅光照渐变，不叠加噪声）
# ══════════════════════════════════════════════════════════════════════════════

def _post_process_background(
    img: Image.Image,
    rng: random.Random,
    np,
) -> Image.Image:
    """
    对整张照片（背景 + 文档）统一施加轻微光照偏移和渐变，
    使背景与文档看起来处于同一拍照环境中。

    注意：仅做光照/色温渐变，不再叠加随机噪声（避免干扰文档可读性）。
    主要的拍照模拟（噪声/模糊/JPEG）由 PhotoSimulation 统一负责。
    """
    arr = np.array(img, dtype=np.float32)

    # 轻微全局亮度偏移（模拟室内光照环境）
    brightness = rng.uniform(-0.04, 0.06)
    arr *= (1.0 + brightness)

    # 极轻微色温偏移（暖光/冷光环境）
    color_temp = rng.uniform(-4, 4)
    arr[:, :, 0] += color_temp    # R
    arr[:, :, 2] -= color_temp    # B

    # 极轻微渐变（模拟窗光来自某侧，强度已降低）
    grad_intensity = rng.uniform(0.01, 0.04)
    grad_dir = rng.choice(["tb", "lr"])
    h, w = arr.shape[:2]
    if grad_dir == "tb":
        g = np.linspace(1.0 + grad_intensity, 1.0 - grad_intensity, h,
                        dtype=np.float32)[:, None, None]
    else:
        g = np.linspace(1.0 + grad_intensity, 1.0 - grad_intensity, w,
                        dtype=np.float32)[None, :, None]
    arr *= g

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
