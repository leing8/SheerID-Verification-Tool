"""
哈佛文档生成 — 公共工具模块

包含所有文档共享的：
  - 字体加载
  - 文本绘制（支持坐标微偏移）
  - DocumentRandomizer（模拟手机拍照效果，对抗感知哈希 / ADR 重复检测）
  - 头像获取

字体直接使用项目内打包的 TTF 文件，不依赖宿主机。
"""

import hashlib
import random
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

if TYPE_CHECKING:
    from ..student_data import HarvardStudentData

# ============ 路径常量 ============

# documents/ 目录（fonts/ 和 templates/ 均在此目录下）
_DOCUMENTS_DIR = Path(__file__).parent

# 模板图片路径（templates/ 子目录）
_TEMPLATES_DIR = _DOCUMENTS_DIR / "templates"
TRANSCRIPT_TEMPLATE = _TEMPLATES_DIR / "harvard-transcript.png"
TRANSCRIPT_TEMPLATE_1 = _TEMPLATES_DIR / "harvard-transcript1.png"
TRANSCRIPT_TEMPLATE_2 = _TEMPLATES_DIR / "harvard-transcript2.png"
INVOICE_TEMPLATE = _TEMPLATES_DIR / "harvard-tuition-receipt.png"
STUDENT_ID_TEMPLATE = _TEMPLATES_DIR / "harvard-student-id.png"

# 字体路径（fonts/ 子目录，项目内打包，不依赖宿主机）
_FONTS_DIR = _DOCUMENTS_DIR / "fonts"
_FONT_LETTER_GOTHIC = _FONTS_DIR / "Letter Gothic Std.ttf"
_FONT_LETTER_GOTHIC_BOLD = _FONTS_DIR / "Letter Gothic Std Bold.ttf"
_FONT_TIMES = _FONTS_DIR / "Times New Roman.ttf"
_FONT_TIMES_BOLD = _FONTS_DIR / "Times New Roman Bold.ttf"

# ============ 字体加载 ============

_monospace_cache = {}


def load_monospace_fonts(sizes: Tuple[int, ...] = (14, 12, 11, 10)) -> dict:
    """
    加载 Letter Gothic Std 等宽字体（成绩单 / 发票专用）。
    直接使用项目内打包字体，不做回退。

    返回字典键名：lg, lg_bold, md, md_bold, sm, sm_bold, xs, xs_bold
    """
    cache_key = sizes
    if cache_key in _monospace_cache:
        return _monospace_cache[cache_key]

    regular_path = str(_FONT_LETTER_GOTHIC)
    bold_path = str(_FONT_LETTER_GOTHIC_BOLD)

    fonts = {}
    size_mapping = {14: "lg", 12: "md", 11: "sm", 10: "xs"}
    for size, key in size_mapping.items():
        if size in sizes:
            fonts[key] = ImageFont.truetype(regular_path, size)
            fonts[f"{key}_bold"] = ImageFont.truetype(bold_path, size)

    _monospace_cache[cache_key] = fonts
    return fonts


def load_serif_font(size: int = 28) -> ImageFont.FreeTypeFont:
    """
    加载 Times New Roman Bold 字体（学生证专用）。
    直接使用项目内打包字体，不做回退。
    """
    return ImageFont.truetype(str(_FONT_TIMES_BOLD), size)


# ============ 文本绘制（打字机效果，支持坐标微偏移）============

def draw_text(draw: ImageDraw.Draw, pos: tuple, text: str,
              font, color: tuple = (30, 30, 30), spacing: int = -1,
              randomizer: "DocumentRandomizer | None" = None):
    """
    逐字符绘制，模拟打字机紧凑字间距。

    如果传入 randomizer，则坐标会自动应用微偏移，
    破坏固定坐标模式以对抗感知哈希检测。
    """
    if randomizer is not None:
        pos = randomizer.jitter_coord(pos)
    x, y = pos
    for char in text:
        draw.text((x, y), char, fill=color, font=font)
        bbox = font.getbbox(char)
        x += (bbox[2] - bbox[0] if bbox else 6) + spacing


# ============ 拍照模拟 — DocumentRandomizer ============

class DocumentRandomizer:
    """
    模拟手机拍摄纸质文档的随机变换。

    同一 RNG seed → 确定性变换（同一 verificationId 生成相同结果）。
    不同 seed → 不同的变换参数 → 视觉上唯一的文档图像。

    变换流水线（按顺序）：
      1. 坐标微偏移（draw_text 阶段）
      2. 透视变形  — 模拟纸张不平整 / 拍摄角度
      3. 轻微旋转  — 模拟手机未完全对齐
      4. 光照变换  — 亮度 / 色温偏移 + 渐变阴影
      5. 高斯噪声  — 模拟传感器噪声
      6. 高斯模糊  — 模拟轻微对焦偏差
      7. JPEG 重编码 — 引入自然压缩伪影

    所有参数范围精心设计：足以改变感知哈希，但不影响人眼可读性。
    """

    def __init__(self, rng: random.Random):
        self.rng = rng
        # 预先采样所有变换参数（确保确定性）
        self._jitter_max = rng.randint(2, 3)
        self._rotation_angle = rng.uniform(-1.2, 1.2)
        self._brightness_offset = rng.uniform(-0.10, 0.10)
        self._color_temp_shift = rng.randint(-8, 8)
        self._noise_sigma = rng.uniform(2.0, 5.0)
        self._blur_radius = rng.uniform(0.3, 0.7)
        self._jpeg_quality = rng.randint(87, 95)
        # 透视变形：四角偏移量
        self._perspective_offsets = [
            (rng.randint(-6, 6), rng.randint(-6, 6)),  # 左上
            (rng.randint(-6, 6), rng.randint(-6, 6)),  # 右上
            (rng.randint(-6, 6), rng.randint(-6, 6)),  # 右下
            (rng.randint(-6, 6), rng.randint(-6, 6)),  # 左下
        ]
        # 渐变阴影方向和强度
        self._shadow_direction = rng.choice(["top", "bottom", "left", "right"])
        self._shadow_intensity = rng.uniform(0.03, 0.08)

    def jitter_coord(self, pos: tuple, max_offset: int = 0) -> tuple:
        """坐标微偏移 ±N 像素，破坏固定坐标特征"""
        offset = max_offset if max_offset > 0 else self._jitter_max
        dx = self.rng.randint(-offset, offset)
        dy = self.rng.randint(-offset, offset)
        return (pos[0] + dx, pos[1] + dy)

    def _apply_perspective(self, img: Image.Image) -> Image.Image:
        """透视变形 — 四角独立微偏移模拟纸张不平整"""
        w, h = img.size
        # 原始四角坐标
        src = [(0, 0), (w, 0), (w, h), (0, h)]
        # 偏移后的四角坐标
        dst = [
            (src[i][0] + self._perspective_offsets[i][0],
             src[i][1] + self._perspective_offsets[i][1])
            for i in range(4)
        ]
        # 使用 PIL 的 PERSPECTIVE 变换
        coeffs = self._find_perspective_coeffs(dst, src)
        return img.transform(
            (w, h), Image.Transform.PERSPECTIVE, coeffs,
            Image.Resampling.BICUBIC,
            fillcolor=(255, 255, 255),
        )

    @staticmethod
    def _find_perspective_coeffs(src_pts, dst_pts):
        """计算透视变换的 8 个系数"""
        matrix = []
        for (sx, sy), (dx, dy) in zip(src_pts, dst_pts):
            matrix.append([dx, dy, 1, 0, 0, 0, -sx * dx, -sx * dy])
            matrix.append([0, 0, 0, dx, dy, 1, -sy * dx, -sy * dy])
        A = matrix
        B = []
        for (sx, _sy) in src_pts:
            B.append(sx)
            B.append(_sy)
        # 求解线性方程组 Ax = B
        # 简单高斯消元（8x8，足够小）
        n = 8
        for col in range(n):
            max_row = max(range(col, n), key=lambda r: abs(A[r][col]))
            A[col], A[max_row] = A[max_row], A[col]
            B[col], B[max_row] = B[max_row], B[col]
            for row in range(col + 1, n):
                if A[col][col] == 0:
                    continue
                f = A[row][col] / A[col][col]
                for j in range(col, n):
                    A[row][j] -= f * A[col][j]
                B[row] -= f * B[col]
        # 回代
        x = [0.0] * n
        for i in range(n - 1, -1, -1):
            if A[i][i] == 0:
                x[i] = 0
                continue
            x[i] = B[i]
            for j in range(i + 1, n):
                x[i] -= A[i][j] * x[j]
            x[i] /= A[i][i]
        return tuple(x)

    def _apply_rotation(self, img: Image.Image) -> Image.Image:
        """轻微旋转 — 模拟手机未完全对齐（≤1.5°）"""
        if abs(self._rotation_angle) < 0.05:
            return img
        return img.rotate(
            self._rotation_angle,
            resample=Image.Resampling.BICUBIC,
            expand=False,
            fillcolor=(255, 255, 255),
        )

    def _apply_lighting(self, img: Image.Image) -> Image.Image:
        """
        光照模拟：
          - 全局亮度偏移
          - 色温偏移（R/B 通道微调）
          - 方向性渐变阴影
        """
        try:
            import numpy as np
        except ImportError:
            return img

        arr = np.array(img, dtype=np.float32)
        h, w = arr.shape[:2]

        # 1. 全局亮度
        arr *= (1.0 + self._brightness_offset)

        # 2. 色温偏移：暖光增加 R 减少 B，冷光相反
        if arr.ndim == 3 and arr.shape[2] >= 3:
            arr[:, :, 0] += self._color_temp_shift   # R
            arr[:, :, 2] -= self._color_temp_shift   # B

        # 3. 渐变阴影
        if self._shadow_direction == "top":
            gradient = np.linspace(1.0 - self._shadow_intensity, 1.0, h)
            gradient = gradient[:, np.newaxis, np.newaxis]
        elif self._shadow_direction == "bottom":
            gradient = np.linspace(1.0, 1.0 - self._shadow_intensity, h)
            gradient = gradient[:, np.newaxis, np.newaxis]
        elif self._shadow_direction == "left":
            gradient = np.linspace(1.0 - self._shadow_intensity, 1.0, w)
            gradient = gradient[np.newaxis, :, np.newaxis]
        else:  # right
            gradient = np.linspace(1.0, 1.0 - self._shadow_intensity, w)
            gradient = gradient[np.newaxis, :, np.newaxis]
        arr *= gradient

        arr = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)

    def _apply_noise(self, img: Image.Image) -> Image.Image:
        """高斯噪声 — 模拟传感器噪声（比旧版更强）"""
        try:
            import numpy as np
        except ImportError:
            return img
        arr = np.array(img, dtype=np.float32)
        rs = np.random.RandomState(self.rng.randint(0, 2 ** 31))
        noise = rs.normal(0, self._noise_sigma, arr.shape)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)

    def _apply_blur(self, img: Image.Image) -> Image.Image:
        """轻微高斯模糊 — 模拟对焦偏差"""
        return img.filter(ImageFilter.GaussianBlur(radius=self._blur_radius))

    def _apply_jpeg_cycle(self, img: Image.Image) -> Image.Image:
        """JPEG 编解码循环 — 引入自然压缩伪影"""
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=self._jpeg_quality)
        buf.seek(0)
        return Image.open(buf).convert("RGB")

    def apply_photo_simulation(self, img: Image.Image) -> Image.Image:
        """
        完整的拍照模拟流水线。

        执行顺序经过设计：几何变换在前（避免模糊后再变换），
        像素级变换在后（噪声 / 模糊 / JPEG 作为最终步骤）。
        """
        img = self._apply_perspective(img)
        img = self._apply_rotation(img)
        img = self._apply_lighting(img)
        img = self._apply_noise(img)
        img = self._apply_blur(img)
        img = self._apply_jpeg_cycle(img)
        return img


def image_to_format(img: Image.Image, rng: random.Random,
                    output_format: str = "png") -> bytes:
    """
    将图像转为指定格式字节（含完整拍照模拟反检测处理）。

    使用 DocumentRandomizer 替代旧版简单噪声注入，
    应用透视变形 / 旋转 / 光照 / 噪声 / 模糊 / JPEG 循环等
    全套拍照模拟变换。
    """
    randomizer = DocumentRandomizer(rng)
    img = randomizer.apply_photo_simulation(img)

    buf = BytesIO()
    fmt = output_format.lower()
    if fmt == "png":
        img.save(buf, format="PNG", optimize=True)
    elif fmt in ("jpg", "jpeg"):
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=92, optimize=True)
    else:
        img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ============ 头像获取 ============

_avatar_cache: dict = {}


def fetch_random_avatar(seed: str, size: tuple = (139, 169)) -> Optional[Image.Image]:
    """从 pravatar.cc 获取真人头像，失败返回带边框的占位灰色图"""
    cache_key = hashlib.md5(f"{seed}_{size}".encode()).hexdigest()
    if cache_key in _avatar_cache:
        return _avatar_cache[cache_key].copy()

    avatar_img = None
    unique_id = hashlib.md5(seed.encode()).hexdigest()[:16]
    request_size = max(size[0], size[1])
    url = f"https://i.pravatar.cc/{request_size}?u={unique_id}"

    # 最多尝试 2 次（应对偶发超时）
    for attempt in range(2):
        try:
            try:
                from curl_cffi import requests as cffi_requests
                resp = cffi_requests.get(url, timeout=15, impersonate="chrome120")
            except ImportError:
                import requests
                resp = requests.get(url, timeout=15)

            if resp.status_code == 200 and len(resp.content) > 1000:
                avatar_img = Image.open(BytesIO(resp.content)).convert("RGB")
                break
        except Exception:
            if attempt == 0:
                continue  # 重试一次

    if avatar_img is None:
        # 占位图：浅灰背景 + 深色边框（确保在白色背景上可见）
        avatar_img = Image.new("RGB", size, (200, 200, 200))
        avatar_draw = ImageDraw.Draw(avatar_img)
        avatar_draw.rectangle(
            [(0, 0), (size[0] - 1, size[1] - 1)],
            outline=(80, 80, 80), width=2
        )
    else:
        # 裁剪到证件照比例
        w, h = avatar_img.size
        target_ratio = size[0] / size[1]
        current_ratio = w / h
        if current_ratio > target_ratio:
            new_w = int(h * target_ratio)
            left = (w - new_w) // 2
            avatar_img = avatar_img.crop((left, 0, left + new_w, h))
        else:
            new_h = int(w / target_ratio)
            avatar_img = avatar_img.crop((0, 0, w, new_h))
        avatar_img = avatar_img.resize(size, Image.Resampling.LANCZOS)

    _avatar_cache[cache_key] = avatar_img.copy()
    return avatar_img


# ============ 确定性随机数 ============

def seeded_rng(student: "HarvardStudentData") -> random.Random:
    """从学号创建确定性 RNG"""
    seed = int(hashlib.sha256(student.student_id.encode()).hexdigest(), 16) % (2 ** 32)
    return random.Random(seed)


