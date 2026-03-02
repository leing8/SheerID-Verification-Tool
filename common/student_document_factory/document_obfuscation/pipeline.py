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
"""

import random

from PIL import Image

from .config import DEFAULT_CONFIG, ObfuscationConfig
from .effects.creases import apply_creases
from .effects.crop import apply_crop
from .effects.stains import apply_stains
from .effects.transform_3d import apply_transform_3d
from .photo_simulation import PhotoSimulation


class ObfuscationPipeline:
    """
    文档混淆流水线。

    对调用方完全透明：调用 `pipeline.apply(img)` 返回处理后图像，
    与调用前接口一致（均为 PIL Image → PIL Image）。

    Args:
        rng:      确定性随机数生成器（由 student_id 或 verification_id 派生）。
        config:   混淆配置，默认启用全部效果。
        doc_type: 文档类型（影响部分效果，如 fading 仅限 student_id）。
    """

    def __init__(
        self,
        rng: random.Random,
        config: ObfuscationConfig = DEFAULT_CONFIG,
        doc_type: str = "",
    ) -> None:
        self._rng = rng
        self._config = config
        self._doc_type = doc_type

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

        # 1. 污渍
        if cfg.stains:
            img = apply_stains(img, rng, doc_type)

        # 2. 折痕（待实现，当前返回原图）
        if cfg.creases:
            img = apply_creases(img, rng, doc_type)

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
