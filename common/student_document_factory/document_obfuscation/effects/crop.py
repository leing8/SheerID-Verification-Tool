"""
document_obfuscation.effects.crop — 边缘裁剪效果

模拟用户拍照时手机未完全对准纸张，导致文档四边被轻微截断的效果。
其中以一定概率选定一条"主裁剪边"，做更大幅度截断，模拟手机明显偏向一侧的场景。

核心流程：
  1. 四边各自独立采样基础裁剪量（0 ~ normal_max）
  2. 以 70% 概率随机选一条边做"主裁剪"，叠加更大幅度裁剪（heavy_min ~ heavy_max）
  3. SafeZone 碰撞检查：若某边裁剪会截入保护区则该边裁剪量置为 0
  4. 执行裁剪（img.crop）
  5. Resize 回原始尺寸（LANCZOS）——轻微拉伸模拟手机图像标准化

设计约束（基于 SheerID 官方文档）：
  - 普通边：单边最多裁剪 5%
  - 主裁剪边：额外裁剪 8%~15%（合计最多约 20%）
  - 不截断任何 SafeZone 核心数据区域（含 padding）
  - 返回与输入相同尺寸的 RGB 图像
"""

from __future__ import annotations

import random
from typing import List, Optional, Tuple

from PIL import Image

# 普通边：单边最大裁剪比例（相对于宽/高较短边）
_NORMAL_MAX_FRACTION = 0.05

# 主裁剪边：额外叠加的裁剪范围
_HEAVY_MIN_FRACTION = 0.08
_HEAVY_MAX_FRACTION = 0.15

# 出现主裁剪边的概率
_HEAVY_CROP_PROB = 0.70


# ══════════════════════════════════════════════════════════════════════════════
# 公共入口
# ══════════════════════════════════════════════════════════════════════════════

def apply_crop(
    img: Image.Image,
    rng: random.Random,
    doc_type: str = "",
    safe_zones: Optional[List] = None,
) -> Image.Image:
    """
    边缘裁剪效果主入口。

    模拟拍照时手机未完全对准文档，四边各有轻微、独立的随机截断。
    以一定概率随机选一条边做更大幅度裁剪（主裁剪边），
    模拟手机明显偏向一侧截断文档边距的场景。
    通过 SafeZone 机制保证核心数据字段不被裁剪。

    Args:
        img:        输入 PIL 图像（RGB）。
        rng:        确定性随机数生成器（由调用方传入）。
        doc_type:   文档类型字符串（当前未使用，预留扩展）。
        safe_zones: 核心数据保护区列表（SafeZone 实例）。
                    不传或传空列表时无约束（仅受最大裁剪比例限制）。

    Returns:
        与输入相同尺寸的 RGB 图像（裁剪 + resize 后）。
    """
    w, h = img.size

    # 计算本次裁剪量（含 SafeZone 约束）
    left, right, top, bottom = _calc_crop(w, h, rng, safe_zones or [])

    # 无效裁剪：四边裁剪量均为 0，直接返回
    if left == 0 and right == 0 and top == 0 and bottom == 0:
        return img

    # 执行裁剪
    cropped = img.crop((left, top, w - right, h - bottom))

    # Resize 回原始尺寸（LANCZOS 高质量插值，轻微拉伸模拟手机标准化处理）
    return cropped.resize((w, h), Image.LANCZOS)


# ══════════════════════════════════════════════════════════════════════════════
# 内部实现
# ══════════════════════════════════════════════════════════════════════════════

def _calc_crop(
    w: int,
    h: int,
    rng: random.Random,
    safe_zones: List,
) -> Tuple[int, int, int, int]:
    """
    计算四边裁剪量，含主裁剪边机制和 SafeZone 边界约束。

    采样策略：
      1. 各边基础裁剪量从 [0, normal_max] 均匀采样
      2. 以 _HEAVY_CROP_PROB 概率随机选一条边，叠加主裁剪量 [heavy_min, heavy_max]
      3. SafeZone 矩形边界碰撞检查（碰撞则该边置 0）

    Returns:
        (left, right, top, bottom) 最终裁剪像素数。
    """
    short = min(w, h)
    normal_max = int(short * _NORMAL_MAX_FRACTION)
    heavy_min  = int(short * _HEAVY_MIN_FRACTION)
    heavy_max  = int(short * _HEAVY_MAX_FRACTION)

    if normal_max < 1:
        return (0, 0, 0, 0)

    # 基础裁剪量：四边各自均匀采样
    left   = rng.randint(0, normal_max)
    right  = rng.randint(0, normal_max)
    top    = rng.randint(0, normal_max)
    bottom = rng.randint(0, normal_max)

    # 主裁剪边：以概率选一条边叠加更大幅度裁剪
    if heavy_min <= heavy_max and rng.random() < _HEAVY_CROP_PROB:
        heavy_side = rng.choice(["left", "right", "top", "bottom"])
        heavy_px = rng.randint(heavy_min, heavy_max)
        if heavy_side == "left":
            left += heavy_px
        elif heavy_side == "right":
            right += heavy_px
        elif heavy_side == "top":
            top += heavy_px
        else:
            bottom += heavy_px

    # SafeZone 矩形边界碰撞检查
    # 裁剪边界线含义：
    #   left  边界 x = left          若保护区 ex1 < left，截入保护区
    #   right 边界 x = w - right     若保护区 ex2 > w - right，截入保护区
    #   top   边界 y = top           若保护区 ey1 < top，截入保护区
    #   bottom边界 y = h - bottom    若保护区 ey2 > h - bottom，截入保护区
    for zone in safe_zones:
        ex1, ey1, ex2, ey2 = zone.expanded_bounds()
        if ex1 < left:
            left = 0
        if ex2 > w - right:
            right = 0
        if ey1 < top:
            top = 0
        if ey2 > h - bottom:
            bottom = 0

    return (left, right, top, bottom)
