"""
document_obfuscation.photo_simulation — 拍照物理效果模拟

从原 DocumentRandomizer 迁移而来，包含：
  - 光照变换（全局亮度 / 色温 / 渐变阴影）
  - 高斯传感器噪声
  - 高斯模糊（对焦偏差）
  - JPEG 重编码（引入自然压缩伪影）

这些效果模拟"用手机拍摄纸质文档"的光学过程，
与 effects/ 下的物理损坏效果（污渍/折痕等）分开管理。
"""

import random
from io import BytesIO

from PIL import Image, ImageFilter


class PhotoSimulation:
    """
    确定性拍照模拟变换。

    同一 RNG seed → 相同变换参数 → 相同输出。
    """

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        # 预采样所有参数（确保确定性，与后续 rng 调用隔离）
        self._brightness_offset  = rng.uniform(-0.10, 0.10)
        self._color_temp_shift   = rng.randint(-8, 8)
        self._noise_sigma        = rng.uniform(2.0, 5.0)
        self._blur_radius        = rng.uniform(0.3, 0.7)
        self._jpeg_quality       = rng.randint(87, 95)
        self._shadow_direction   = rng.choice(["top", "bottom", "left", "right"])
        self._shadow_intensity   = rng.uniform(0.03, 0.08)

    def apply(self, img: Image.Image) -> Image.Image:
        """
        依次应用：光照 → 噪声 → 模糊 → JPEG 重编码。

        返回经过完整拍照模拟处理的 PIL 图像（RGB）。
        """
        img = self._apply_lighting(img)
        img = self._apply_noise(img)
        img = self._apply_blur(img)
        img = self._apply_jpeg_cycle(img)
        return img

    # ── 光照 ──────────────────────────────────────────────────────────────────

    def _apply_lighting(self, img: Image.Image) -> Image.Image:
        """全局亮度偏移 + 色温调整 + 方向渐变阴影"""
        try:
            import numpy as np
        except ImportError:
            return img

        arr = np.array(img.convert("RGB"), dtype=np.float32)
        h, w = arr.shape[:2]

        # 1. 全局亮度
        arr *= (1.0 + self._brightness_offset)

        # 2. 色温偏移（R/B 通道微调）
        arr[:, :, 0] += self._color_temp_shift   # R 通道
        arr[:, :, 2] -= self._color_temp_shift   # B 通道

        # 3. 渐变阴影
        direction = self._shadow_direction
        intensity = self._shadow_intensity
        if direction == "top":
            g = np.linspace(1.0 - intensity, 1.0, h)[:, None, None]
        elif direction == "bottom":
            g = np.linspace(1.0, 1.0 - intensity, h)[:, None, None]
        elif direction == "left":
            g = np.linspace(1.0 - intensity, 1.0, w)[None, :, None]
        else:  # right
            g = np.linspace(1.0, 1.0 - intensity, w)[None, :, None]
        arr *= g

        arr = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)

    # ── 噪声 ──────────────────────────────────────────────────────────────────

    def _apply_noise(self, img: Image.Image) -> Image.Image:
        """高斯传感器噪声"""
        try:
            import numpy as np
        except ImportError:
            return img

        arr = np.array(img.convert("RGB"), dtype=np.float32)
        rs = np.random.RandomState(self.rng.randint(0, 2 ** 31 - 1))
        noise = rs.normal(0, self._noise_sigma, arr.shape)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)

    # ── 模糊 ──────────────────────────────────────────────────────────────────

    def _apply_blur(self, img: Image.Image) -> Image.Image:
        """轻微高斯模糊（对焦偏差）"""
        return img.filter(ImageFilter.GaussianBlur(radius=self._blur_radius))

    # ── JPEG 重编码 ────────────────────────────────────────────────────────────

    def _apply_jpeg_cycle(self, img: Image.Image) -> Image.Image:
        """JPEG 编解码循环，引入自然压缩伪影"""
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=self._jpeg_quality)
        buf.seek(0)
        return Image.open(buf).convert("RGB")
