"""
document_obfuscation.effects.background_scene — 背景场景叠加效果

模拟用户将文档放置在桌面/地毯/其他物品上用手机拍照的视觉效果。

核心流程：
  1. 生成背景纹理（木纹 / 深色桌面 / 白色桌面 / 布面 / 纯色）
  2. 对文档施加真实透视变换（四角独立移动→单应矩阵→梯形/泡形畸变）
  3. 计算并渲染柔和投影阴影
  4. 将变换后的文档粘贴到背景中央（允许轻微偏移）
  5. 对背景可见区域叠加噪声 / 光照渐变，使整体更自然

透视变换说明：
  真实拍照时相机并非正对文档，而是从某个偏转角度俯拍，
  导致文档呈现梯形（近大远小）甚至一定程度的桶形畸变。
  本模块使用 PIL 的 PERSPECTIVE 变换 (8 参数单应矩阵) 来精确模拟
  四角独立偏移产生的透视效果，同时控制最大角度 ≤ 6° 满足 SheerID 要求。

设计约束（基于 SheerID 官方文档）：
  - 倾斜角 < 10°（本模块限制在 ±6°）
  - 文档四边均可见，不截断关键信息
  - 背景与文档形成明显色彩对比
  - 文档内部像素质量不受背景效果干扰
"""

from __future__ import annotations

import random
from typing import Tuple

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

    Args:
        img:      输入 PIL 图像（RGB），代表原始文档。
        rng:      确定性随机数生成器（由调用方传入）。
        doc_type: 文档类型（当前未使用，预留扩展）。

    Returns:
        包含背景的新 PIL 图像（RGB），尺寸约为原图的 1.5×～1.7×。
    """
    try:
        import numpy as np
    except ImportError:
        return img  # numpy 不可用时直接返回原图

    doc_w, doc_h = img.size

    # ── 1. 选择背景类型并生成背景 ─────────────────────────────────────────────
    bg_type = _choose_bg_type(rng)
    bg_scale = rng.uniform(1.12, 1.28)          # 背景比文档大 12%～28%（四周露出约 6%～14%）
    bg_w = int(doc_w * bg_scale)
    bg_h = int(doc_h * bg_scale)
    background = _generate_background(bg_type, bg_w, bg_h, rng)

    # ── 2. 透视变换（四角独立偏移 → 真实单应变换） ──────────────────────────
    doc_warped, corners_dst = _perspective_warp(img, rng, bg_type)
    warp_w, warp_h = doc_warped.size

    # ── 3. 计算文档粘贴位置（居中 + 轻微随机偏移） ──────────────────────────
    offset_x = int((bg_w - warp_w) / 2 + rng.uniform(-0.03, 0.03) * bg_w)
    offset_y = int((bg_h - warp_h) / 2 + rng.uniform(-0.03, 0.03) * bg_h)
    # 防止越界
    offset_x = max(0, min(offset_x, bg_w - warp_w))
    offset_y = max(0, min(offset_y, bg_h - warp_h))

    # ── 4. 渲染投影阴影 ───────────────────────────────────────────────────────
    _paste_shadow(background, doc_warped, offset_x, offset_y, rng, np)

    # ── 5. 粘贴文档（用透视变换后的 alpha 蒙版）─────────────────────────────
    _paste_doc(background, doc_warped, offset_x, offset_y)

    # ── 6. 背景区域光照 / 噪声后处理 ─────────────────────────────────────────
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
    """浅木纹桌面：横向条纹 + Perlin 风格扰动"""
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

    # 细粒噪声（木纹表面）
    noise = rs.normal(0, 6, (h, w, 3)).astype(np.float32)
    arr += noise

    # 随机斜向光影渐变（模拟窗光）
    light_dir = rng.choice(["lr", "rl", "tb"])
    if light_dir == "lr":
        g = np.linspace(0.90, 1.05, w)[None, :, None].astype(np.float32)
    elif light_dir == "rl":
        g = np.linspace(1.05, 0.90, w)[None, :, None].astype(np.float32)
    else:
        g = np.linspace(0.93, 1.03, h)[:, None, None].astype(np.float32)
    arr *= g

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _bg_dark(w: int, h: int, rng: random.Random, rs) -> Image.Image:
    """深色桌面：深棕/深灰，与白色文档对比最强"""
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

    # 细纹
    grain_amp = rng.uniform(3, 8)
    arr += rs.normal(0, grain_amp, (h, w, 3)).astype(np.float32)

    # 横纹（深色木纹）
    y_idx = np.arange(h, dtype=np.float32)
    grain_freq = rng.uniform(10, 25)
    grain = np.sin(y_idx / h * np.pi * grain_freq) * rng.uniform(4, 10)
    arr[:, :, 0] += grain[:, None]
    arr[:, :, 1] += grain[:, None] * 0.7
    arr[:, :, 2] += grain[:, None] * 0.4

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _bg_white(w: int, h: int, rng: random.Random, rs) -> Image.Image:
    """白色/浅灰桌面"""
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
    arr += rs.normal(0, 3, (h, w, 3)).astype(np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _bg_carpet(w: int, h: int, rng: random.Random, rs) -> Image.Image:
    """地毯/布面：中等饱和色 + 高频细粒噪声模拟织物"""
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

    # 高频噪声（织物颗粒感）
    arr += rs.normal(0, 12, (h, w, 3)).astype(np.float32)

    # 织物方向纹路（细横条 + 细竖条交织）
    y_pattern = (np.arange(h) % rng.randint(3, 6)).astype(np.float32) * 3
    x_pattern = (np.arange(w) % rng.randint(3, 6)).astype(np.float32) * 3
    arr[:, :, 0] += y_pattern[:, None] - x_pattern[None, :]
    arr[:, :, 1] += y_pattern[:, None] * 0.8
    arr[:, :, 2] += x_pattern[None, :] * 0.8

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def _bg_notebook(w: int, h: int, rng: random.Random, rs) -> Image.Image:
    """笔记本封面/书桌杂志背面：纯色带轻微噪声"""
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
    arr += rs.normal(0, 5, (h, w, 3)).astype(np.float32)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# ══════════════════════════════════════════════════════════════════════════════
# 透视变换（核心）
# ══════════════════════════════════════════════════════════════════════════════

def _perspective_warp(
    img: Image.Image,
    rng: random.Random,
    bg_type: str,
) -> Tuple[Image.Image, list]:
    """
    对文档施加真实透视变换，模拟相机从偏转角度俯拍。

    变换策略（模拟真实拍照透视）：
      1. 选择一个随机"相机俯仰/偏转"角度（pitch / yaw 分量）
      2. 根据角度推导四角独立偏移量（近端变大，远端变小）
      3. 用 PIL PERSPECTIVE 8 参数单应矩阵实现变换
      4. 在变换后空白区域填充背景灰白色（后续会被背景覆盖）

    透视强度：
      - yaw (水平倾斜)  : 0°～6°  → 文档呈左右梯形
      - pitch (垂直倾斜): 0°～5°  → 文档呈上下梯形
      - roll (旋转)     : ±4°     → 整体轻微旋转

    Returns:
        (warped_img, dst_corners)
        warped_img   : 透视变换后的 PIL RGBA 图像（Alpha=0 为透明背景）
        dst_corners  : 文档四角在 warped_img 中的目标坐标
    """
    import math
    import numpy as np

    w, h = img.size

    # ── 相机角度采样 ─────────────────────────────────────────────────────────
    # yaw: 相机水平偏转（绕垂直轴）→ 左右梯形
    # pitch: 相机垂直俯仰（绕水平轴）→ 上下梯形
    # roll: 相机旋转（绕光轴）→ 整体旋转
    yaw_deg   = rng.uniform(-6.0, 6.0)
    pitch_deg = rng.uniform(-5.0, 5.0)
    roll_deg  = rng.uniform(-4.0, 4.0)

    # 透视强度系数（yaw/pitch 决定梯形变形程度）
    # 用 tan(angle) * 宽/高 近似三维投影效果
    yaw_rad   = math.radians(abs(yaw_deg))
    pitch_rad = math.radians(abs(pitch_deg))

    # 水平方向的边缘压缩（yaw → 左右两列的 x 收缩量）
    yaw_shift = int(math.tan(yaw_rad) * h * 0.5)
    # 垂直方向的边缘压缩（pitch → 上下两行的 y 收缩量）
    pitch_shift = int(math.tan(pitch_rad) * w * 0.5)

    # ── 构造源矩形四角（顺时针：左上、右上、右下、左下）──────────────────────
    src = np.float32([
        [0,   0  ],   # TL
        [w-1, 0  ],   # TR
        [w-1, h-1],   # BR
        [0,   h-1],   # BL
    ])

    # ── 构造目标四角（施加透视偏移）─────────────────────────────────────────
    # yaw_deg > 0: 相机偏右 → 文档右侧透视收缩（右边变窄）
    # pitch_deg > 0: 相机偏上 → 文档上侧透视收缩（顶边变窄）
    dst = np.float32([
        [0,   0  ],   # TL (初始化，后面修改)
        [w-1, 0  ],   # TR
        [w-1, h-1],   # BR
        [0,   h-1],   # BL
    ])

    # yaw 效果：右半侧两角 y 坐标内缩（向中心移动），左半侧外扩
    if yaw_deg >= 0:
        # 相机向右看：右列（TR/BR）向中心收缩
        dst[1][1] += yaw_shift      # TR.y 下移
        dst[2][1] -= yaw_shift      # BR.y 上移
        dst[0][1] -= yaw_shift // 2  # TL.y 轻微外扩
        dst[3][1] += yaw_shift // 2  # BL.y 轻微外扩
    else:
        # 相机向左看：左列（TL/BL）向中心收缩
        dst[0][1] += yaw_shift      # TL.y 下移
        dst[3][1] -= yaw_shift      # BL.y 上移
        dst[1][1] -= yaw_shift // 2  # TR.y 轻微外扩
        dst[2][1] += yaw_shift // 2  # BR.y 轻微外扩

    # pitch 效果：顶边/底边 x 坐标内缩
    if pitch_deg >= 0:
        # 相机从上方看：顶边（TL/TR）向中心内缩
        dst[0][0] += pitch_shift    # TL.x 右移
        dst[1][0] -= pitch_shift    # TR.x 左移
        dst[3][0] -= pitch_shift // 2  # BL.x 轻微内缩
        dst[2][0] += pitch_shift // 2  # BR.x 轻微内缩
    else:
        # 相机从下方看：底边（BL/BR）向中心内缩
        dst[3][0] += pitch_shift    # BL.x 右移
        dst[2][0] -= pitch_shift    # BR.x 左移
        dst[0][0] -= pitch_shift // 2  # TL.x 轻微内缩
        dst[1][0] += pitch_shift // 2  # TR.x 轻微内缩

    # ── 确保目标四角在合理范围内 ─────────────────────────────────────────────
    # 给变换后图像加 padding 避免越界
    pad = max(yaw_shift, pitch_shift) + 20
    out_w = w + pad * 2
    out_h = h + pad * 2
    dst_padded = dst + np.float32([pad, pad])
    src_padded = src  # src 不变

    # ── 计算 PIL PERSPECTIVE 变换系数（8 参数单应矩阵）────────────────────────
    coeffs = _compute_perspective_coeffs(src_padded, dst_padded, w, h, pad)

    # ── 执行透视变换（RGBA 保留透明区域）────────────────────────────────────
    rgba = img.convert("RGBA")

    # 先将图像放在 padding 画布中央
    canvas_rgba = Image.new("RGBA", (out_w, out_h), (255, 255, 255, 0))
    canvas_rgba.paste(rgba, (pad, pad))

    warped = canvas_rgba.transform(
        (out_w, out_h),
        Image.PERSPECTIVE,
        coeffs,
        resample=Image.BICUBIC,
    )

    # ── 施加旋转（roll）─────────────────────────────────────────────────────
    if abs(roll_deg) > 0.5:
        warped = warped.rotate(
            roll_deg,
            resample=Image.BICUBIC,
            expand=True,
            fillcolor=(255, 255, 255, 0),
        )

    # ── 裁剪掉多余的透明边距 ─────────────────────────────────────────────────
    warped = _autocrop_transparent(warped)

    return warped, dst_padded.tolist()


def _compute_perspective_coeffs(
    src: "numpy.ndarray",
    dst: "numpy.ndarray",
    w: int,
    h: int,
    pad: int,
) -> list:
    """
    用最小二乘法计算 PIL PERSPECTIVE 变换的 8 个系数。

    PIL 的 PERSPECTIVE data 参数 (a,b,c,d,e,f,g,h) 满足：
        x_src = (a*x_dst + b*y_dst + c) / (g*x_dst + h*y_dst + 1)
        y_src = (d*x_dst + e*y_dst + f) / (g*x_dst + h*y_dst + 1)

    注意 PIL 变换方向是 dst→src（逆变换），因此这里传入的 src 是原坐标，
    dst 是变换后坐标，我们要求 dst→src 的系数。
    """
    import numpy as np

    # 构建线性方程组 A @ coeffs = b
    # 4 个点对 → 8 个方程
    A = []
    b_vec = []
    for (xs, ys), (xd, yd) in zip(src, dst):
        A.append([xd, yd, 1, 0, 0, 0, -xs * xd, -xs * yd])
        b_vec.append(xs)
        A.append([0, 0, 0, xd, yd, 1, -ys * xd, -ys * yd])
        b_vec.append(ys)

    A = np.array(A, dtype=np.float64)
    b_vec = np.array(b_vec, dtype=np.float64)
    coeffs, _, _, _ = np.linalg.lstsq(A, b_vec, rcond=None)
    return list(coeffs)


def _autocrop_transparent(img: Image.Image) -> Image.Image:
    """裁剪掉 RGBA 图像四周多余的全透明行/列，保留内容区域"""
    import numpy as np

    arr = np.array(img)
    alpha = arr[:, :, 3]
    rows = np.any(alpha > 0, axis=1)
    cols = np.any(alpha > 0, axis=0)
    if not rows.any():
        return img
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    return img.crop((cmin, rmin, cmax + 1, rmax + 1))


# ══════════════════════════════════════════════════════════════════════════════
# 阴影 & 合成
# ══════════════════════════════════════════════════════════════════════════════

def _paste_shadow(
    background: Image.Image,
    doc_warped: Image.Image,
    offset_x: int,
    offset_y: int,
    rng: random.Random,
    np,
) -> None:
    """
    在背景上绘制文档的柔和投影阴影（就地修改 background）。

    Shadow 实现：
      1. 从 doc_warped 提取 Alpha 蒙版
      2. 降低不透明度（shadow_opacity）得到灰色阴影层
      3. 高斯模糊（模拟阴影扩散）
      4. 偏移粘贴（模拟光源方向）
    """
    shadow_opacity   = rng.uniform(0.25, 0.45)
    shadow_blur      = rng.uniform(8, 18)
    # 光源方向决定阴影偏移
    shadow_dx = int(rng.uniform(4, 12))
    shadow_dy = int(rng.uniform(4, 12))

    # 提取 Alpha 蒙版
    if doc_warped.mode == "RGBA":
        alpha_ch = doc_warped.split()[3]
    else:
        alpha_ch = Image.new("L", doc_warped.size, 255)

    # 将 alpha 映射为暗灰色阴影
    shadow_arr = np.array(alpha_ch, dtype=np.float32) * shadow_opacity
    shadow_gray = Image.fromarray(shadow_arr.clip(0, 255).astype(np.uint8), mode="L")
    shadow_gray = shadow_gray.filter(ImageFilter.GaussianBlur(radius=shadow_blur))

    # 在背景上合成阴影（背景像素 *= 1 - shadow_factor）
    bg_arr = np.array(background, dtype=np.float32)
    bg_h, bg_w = bg_arr.shape[:2]
    sh_arr = np.array(shadow_gray, dtype=np.float32) / 255.0

    sh_x1 = offset_x + shadow_dx
    sh_y1 = offset_y + shadow_dy
    sh_x2 = sh_x1 + doc_warped.width
    sh_y2 = sh_y1 + doc_warped.height

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
    doc_warped: Image.Image,
    offset_x: int,
    offset_y: int,
) -> None:
    """将变换后的文档（RGBA）粘贴到背景上（就地修改 background）"""
    if doc_warped.mode == "RGBA":
        # 用 Alpha 通道做蒙版合成，透明区域保留背景
        background.paste(doc_warped.convert("RGB"), (offset_x, offset_y),
                         mask=doc_warped.split()[3])
    else:
        background.paste(doc_warped, (offset_x, offset_y))


# ══════════════════════════════════════════════════════════════════════════════
# 背景后处理（光照 / 噪声）
# ══════════════════════════════════════════════════════════════════════════════

def _post_process_background(
    img: Image.Image,
    rng: random.Random,
    np,
) -> Image.Image:
    """
    对整张照片（背景 + 文档）统一施加轻微光照偏移和噪声，
    使背景与文档看起来处于同一拍照环境中。

    注意：此处仅做轻微处理，避免影响文档内部文字可读性。
    主要的拍照模拟（噪声/模糊/JPEG）由 PhotoSimulation 统一负责。
    """
    arr = np.array(img, dtype=np.float32)

    # 轻微全局亮度偏移（模拟室内光照环境）
    brightness = rng.uniform(-0.05, 0.08)
    arr *= (1.0 + brightness)

    # 极轻微色温偏移（暖光/冷光环境）
    color_temp = rng.uniform(-6, 6)
    arr[:, :, 0] += color_temp    # R
    arr[:, :, 2] -= color_temp    # B

    # 极轻微渐变（模拟窗光来自某侧）
    grad_intensity = rng.uniform(0.02, 0.06)
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
