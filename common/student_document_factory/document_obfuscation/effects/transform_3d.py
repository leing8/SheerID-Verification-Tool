"""
document_obfuscation.effects.transform_3d — 3D 透视变换效果

模拟手机从偏转角度俯拍文档时产生的透视畸变（yaw / pitch / roll），
生成梯形或轻微桶形变形效果。

返回格式：RGBA（保留透明通道）
  Alpha=0 的区域即文档轮廓外的透明部分，由下游的 background_scene 通过
  alpha 蒙版合成，透明区域自然显示背景纹理，不产生白色边框割裂感。

  若下游不使用 background_scene，调用方需自行转为 RGB：
      img_rgb = result.convert("RGB")

透视变换说明：
  真实拍照时相机并非正对文档，而是从某个偏转角度俯拍，
  导致文档呈现梯形（近大远小）甚至一定程度的透视畸变。
  本模块使用 PIL 的 PERSPECTIVE 变换 (8 参数单应矩阵) 精确模拟
  四角独立偏移产生的透视效果，同时控制最大角度 ≤ 6° 满足 SheerID 要求。

设计约束（基于 SheerID 官方文档）：
  - 倾斜角 < 10°（本模块限制在 ±6°）
  - 文档四边均可见，不截断关键信息
"""

from __future__ import annotations

import math
import random
from typing import Tuple

from PIL import Image


# ══════════════════════════════════════════════════════════════════════════════
# 公共入口
# ══════════════════════════════════════════════════════════════════════════════

def apply_transform_3d(
    img: Image.Image,
    rng: random.Random,
    doc_type: str = "",
) -> Image.Image:
    """
    对文档施加 3D 透视变换，模拟相机从偏转角度俯拍。

    Args:
        img:      输入 PIL 图像（RGB），代表原始文档。
        rng:      确定性随机数生成器（由调用方传入）。
        doc_type: 文档类型（当前未使用，预留扩展）。

    Returns:
        透视变换后的 PIL 图像（**RGBA**）。
        Alpha=0 的区域是文档轮廓外的透明部分，由下游的
        background_scene 通过 alpha 蒙版将其自然显示为背景纹理，
        避免白色边框与背景产生割裂感。

        若下游不使用 background_scene，调用方需自行转为 RGB：
            img_rgb = result.convert("RGB")
    """
    try:
        import numpy as np
    except ImportError:
        return img.convert("RGBA")  # numpy 不可用时返回 RGBA 原图

    warped_rgba, _ = _perspective_warp(img, rng)
    return warped_rgba  # 直接返回 RGBA，保留透明通道，不填白


# ══════════════════════════════════════════════════════════════════════════════
# 透视变换（核心实现）
# ══════════════════════════════════════════════════════════════════════════════

def _perspective_warp(
    img: Image.Image,
    rng: random.Random,
) -> Tuple[Image.Image, list]:
    """
    对文档施加真实透视变换，模拟相机从偏转角度俯拍。

    变换策略（模拟真实拍照透视）：
      1. 选择一个随机"相机俯仰/偏转"角度（pitch / yaw 分量）
      2. 根据角度推导四角独立偏移量（近端变大，远端变小）
      3. 用 PIL PERSPECTIVE 8 参数单应矩阵实现变换
      4. 在变换后空白区域保留透明（Alpha=0）

    透视强度：
      - yaw (水平倾斜)  : 0°～6°  → 文档呈左右梯形
      - pitch (垂直倾斜): 0°～5°  → 文档呈上下梯形
      - roll (旋转)     : ±4°     → 整体轻微旋转

    Returns:
        (warped_img, dst_corners)
        warped_img   : 透视变换后的 PIL RGBA 图像（Alpha=0 为透明背景）
        dst_corners  : 文档四角在 warped_img 中的目标坐标列表
    """
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

    # 水平方向的边缘压缩（yaw → 左右两列的 y 收缩量）
    yaw_shift = int(math.tan(yaw_rad) * h * 0.5)
    # 垂直方向的边缘压缩（pitch → 上下两行的 x 收缩量）
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
        [0,   0  ],   # TL（初始化，后面修改）
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
    # 给变换后图像加 padding 避免越界（容器足够大，确保强透视下不裁剪内容）
    pad = yaw_shift + pitch_shift + 50
    out_w = w + pad * 2
    out_h = h + pad * 2
    dst_padded = dst + np.float32([pad, pad])
    src_padded = src + np.float32([pad, pad])  # 与画布粘贴位置 (pad, pad) 对齐

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

    # 构建线性方程组 A @ coeffs = b（4 个点对 → 8 个方程）
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
