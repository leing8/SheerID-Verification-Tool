"""
document_obfuscation.pipeline — 混淆流水线编排

ObfuscationPipeline 将所有效果按固定顺序串联，对调用方透明。
config.enabled=False 时直接返回原图，零开销。

流水线顺序（与视觉自然性匹配）：
  1. stains        — 污渍（物理损坏，在几何变换之前）
  2. creases       — 折痕（物理损坏）
  3. crop          — 边缘裁剪（待实现）
  4. transform_3d  — 3D 透视 + 旋转（待实现）
  5. photo_sim     — 光照 / 噪声 / 模糊 / JPEG（拍照光学）

safe_zones 注入：
  调用方在构建 ObfuscationPipeline 时传入 list[SafeZone]，
  流水线将其透传给 apply_stains()；不传则无保护区约束。
  每种文档自行定义保护区，pipeline.py 不感知文档细节。
"""

import random
from typing import List, Optional

from PIL import Image

from .config import DEFAULT_CONFIG, ObfuscationConfig
from .effects.creases import apply_creases
from .effects.crop import apply_crop
from .effects.stains import apply_stains
from .effects.transform_3d import apply_transform_3d
from .photo_simulation import PhotoSimulation
from .safe_zone import SafeZone


class ObfuscationPipeline:
    """
    文档混淆流水线。

    对调用方完全透明：调用 `pipeline.apply(img)` 返回处理后图像。

    Args:
        rng:        确定性随机数生成器（由 student_id 或 verification_id 派生）。
        config:     混淆配置，默认启用全部效果。
        doc_type:   文档类型（影响部分效果，如 fading 仅限 student_id）。
        safe_zones: 核心数据保护区列表。apply_stains() 通过 Rejection Sampling
                    确保污渍不落在这些区域内。None 或空列表表示无约束。
    """

    def __init__(
        self,
        rng: random.Random,
        config: ObfuscationConfig = DEFAULT_CONFIG,
        doc_type: str = "",
        safe_zones: Optional[List[SafeZone]] = None,
    ) -> None:
        self._rng = rng
        self._config = config
        self._doc_type = doc_type
        self._safe_zones: List[SafeZone] = safe_zones or []

    def apply(self, img: Image.Image) -> Image.Image:
        """
        对图像依次应用各混淆效果，返回结果图像。

        若 config.enabled=False，原图原样返回（零副作用）。
        """
        if not self._config.enabled:
            return img

        cfg = self._config
        rng = self._rng
        doc_type = self._doc_type

        # 1. 污渍（safe_zones 透传，确保不遮挡核心数据）
        if cfg.stains:
            img = apply_stains(img, rng, doc_type, safe_zones=self._safe_zones)

        # 2. 折痕（safe_zones 透传，确保折痕不穿过核心数据区）
        if cfg.creases:
            img = apply_creases(img, rng, doc_type, safe_zones=self._safe_zones)

        # 3. 边缘裁剪（待实现，当前返回原图）
        if cfg.crop:
            img = apply_crop(img, rng, doc_type)

        # 4. 3D 透视变换（待实现，当前返回原图）
        if cfg.transform_3d:
            img = apply_transform_3d(img, rng, doc_type)

        # 5. 拍照模拟（光照 / 噪声 / 模糊 / JPEG）
        if cfg.photo_simulation:
            sim = PhotoSimulation(rng)
            img = sim.apply(img)

        return img
