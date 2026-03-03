"""
document_obfuscation.pipeline — 混淆流水线编排

ObfuscationPipeline 将所有效果按固定顺序串联，对调用方透明。
config.enabled=False 时直接返回原图，零开销。

流水线顺序（与视觉自然性匹配）：
  1. stains        — 污渍（物理损坏，在几何变换之前）
  2. creases       — 折痕（物理损坏）
  3. crop          — 边缘裁剪
  4. transform_3d  — 3D 透视变换（yaw / pitch / roll 相机角度模拟）
  5. background_scene — 背景场景叠加（桌面 / 地毯等背景 + 投影阴影）
  6. photo_sim     — 光照 / 噪声 / 模糊 / JPEG（拍照光学）

各步骤格式契约（I/O）：
  - stains       : 输入 RGB → 输出 RGB
  - creases      : 输入 RGB → 输出 RGB
  - crop         : 输入 RGB → 输出 RGB
  - transform_3d : 输入 RGB → 输出 RGBA（透明区域 = 文档轮廓外）
  - background_scene : 输入 RGB 或 RGBA → 输出 RGB
  - photo_sim    : 输入 RGB → 输出 RGB

步骤独立性保证：
  禁用任意步骤不影响其他步骤的行为。Pipeline 在步骤之间负责格式归一化：
  - transform_3d 输出 RGBA；若 background_scene 已禁用，pipeline 将其转为
    RGB（白底合成）再传给后续步骤，保证下游始终收到 RGB。
  - 其余步骤均接受并输出 RGB，无需额外适配。

safe_zones 注入：
  调用方在构建 ObfuscationPipeline 时传入 list[SafeZone]，
  流水线将其透传给支持的效果（stains / creases）；不传则无保护区约束。
  每种文档自行定义保护区，pipeline.py 不感知文档细节。
"""

import random
from typing import List, Optional

from PIL import Image

from .config import DEFAULT_CONFIG, ObfuscationConfig
from .effects.background_scene import apply_background_scene
from .effects.creases import apply_creases
from .effects.crop import apply_crop
from .effects.stains import apply_stains
from .effects.transform_3d import apply_transform_3d
from .photo_simulation import PhotoSimulation
from .safe_zone import SafeZone


class ObfuscationPipeline:
    """
    文档混淆流水线。

    对调用方完全透明：调用 `pipeline.apply(img)` 返回处理后图像（RGB）。
    流水线负责步骤间的格式归一化，确保各步骤独立可用。

    Args:
        rng:        确定性随机数生成器（由 student_id 或 verification_id 派生）。
        config:     混淆配置，默认启用全部效果。
        doc_type:   文档类型（影响部分效果，如 fading 仅限 student_id）。
        safe_zones: 核心数据保护区列表。stains / creases 通过 Rejection Sampling
                    确保效果不落在这些区域内。None 或空列表表示无约束。
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
        对图像依次应用各混淆效果，返回结果图像（RGB）。

        若 config.enabled=False，原图原样返回（零副作用）。
        各步骤可通过 config 独立开关，互不影响。
        """
        if not self._config.enabled:
            return img

        # 确保输入为 RGB（兼容调用方传入非 RGB 图像的情况）
        if img.mode != "RGB":
            img = img.convert("RGB")

        cfg = self._config
        rng = self._rng
        doc_type = self._doc_type

        # ── Step 1: 污渍 ──────────────────────────────────────────────────────
        # 输入 RGB → 输出 RGB
        # safe_zones 透传，确保污渍不落在核心数据区域内
        if cfg.stains:
            img = apply_stains(img, rng, doc_type, safe_zones=self._safe_zones)

        # ── Step 2: 折痕 ──────────────────────────────────────────────────────
        # 输入 RGB → 输出 RGB
        # safe_zones 透传，确保折痕不穿过核心数据区域
        if cfg.creases:
            img = apply_creases(img, rng, doc_type, safe_zones=self._safe_zones)

        # ── Step 3: 边缘裁剪 ─────────────────────────────────────────────────
        # 输入 RGB → 输出 RGB
        # safe_zones 透传（待实现时启用），确保裁剪不截断核心数据区域
        if cfg.crop:
            img = apply_crop(img, rng, doc_type)

        # ── Step 4: 3D 透视变换 ──────────────────────────────────────────────
        # 输入 RGB → 输出 RGBA（透明区域 = 文档轮廓外的空白）
        # 输出 RGBA 保留透明通道，供 background_scene 通过 alpha 蒙版自然合成背景。
        # 若 background_scene 已禁用，pipeline 在此步骤后将 RGBA 转为 RGB（白底），
        # 保证 Step 5/6 始终接收 RGB，各步骤无需感知上游格式。
        if cfg.transform_3d:
            img = apply_transform_3d(img, rng, doc_type)
            # 格式归一化：background_scene 禁用时，将 RGBA → RGB（白底合成）
            if not cfg.background_scene and img.mode == "RGBA":
                rgb = Image.new("RGB", img.size, (255, 255, 255))
                rgb.paste(img.convert("RGB"), mask=img.split()[3])
                img = rgb

        # ── Step 5: 背景场景叠加 ─────────────────────────────────────────────
        # 输入 RGB 或 RGBA → 输出 RGB
        # 接受来自 transform_3d 的 RGBA（通过 alpha 蒙版合成，无白色边框割裂感），
        # 也接受普通 RGB 文档（transform_3d 禁用时）。
        # 输出始终为 RGB（背景填充了透明区域）。
        if cfg.background_scene:
            img = apply_background_scene(img, rng, doc_type)

        # ── Step 6: 拍照模拟 ─────────────────────────────────────────────────
        # 输入 RGB → 输出 RGB
        # 统一施加光照偏移、噪声、模糊、JPEG 重编码，模拟手机拍照的光学效果。
        # 作用于完整照片（含背景），使背景与文档处于同一拍照环境。
        if cfg.photo_simulation:
            sim = PhotoSimulation(rng)
            img = sim.apply(img)

        # 确保最终输出为 RGB（兼容所有下游调用方）
        if img.mode != "RGB":
            img = img.convert("RGB")

        return img
