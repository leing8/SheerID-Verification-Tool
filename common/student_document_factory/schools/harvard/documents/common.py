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
INVOICE_TEMPLATE_1 = _TEMPLATES_DIR / "harvard-tuition-receipt1.png"
INVOICE_TEMPLATE_2 = _TEMPLATES_DIR / "harvard-tuition-receipt2.png"
STUDENT_ID_TEMPLATE = _TEMPLATES_DIR / "harvard-student-id.png"

# 字体路径（fonts/ 子目录，项目内打包，不依赖宿主机）
_FONTS_DIR = _DOCUMENTS_DIR / "fonts"
_FONT_LETTER_GOTHIC = _FONTS_DIR / "Letter Gothic Std.ttf"
_FONT_LETTER_GOTHIC_BOLD = _FONTS_DIR / "Letter Gothic Std Bold.ttf"
_FONT_TIMES = _FONTS_DIR / "Times New Roman.ttf"
_FONT_TIMES_BOLD = _FONTS_DIR / "Times New Roman Bold.ttf"
_FONT_HELVETICA_MEDIUM = _FONTS_DIR / "Helvetica CE Medium.otf"
_FONT_HELVETICA_BOLD = _FONTS_DIR / "Helvetica CE Bold.otf"

# ============ 字体加载 ============

_monospace_cache = {}
_helvetica_cache = {}


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


def load_helvetica_fonts() -> dict:
    """
    加载 Helvetica CE Medium / Bold 字体（发票专用）。

    返回字典键名：
      - xs / xs_bold  (14px)
      - sm / sm_bold  (17px)
      - md / md_bold  (26px)  — 发票正文
      - lg / lg_bold  (28px)  — Total Due 金额
      - xl / xl_bold  (38px)  — Total Amount Due 大号标题
    """
    if _helvetica_cache:
        return _helvetica_cache

    medium_path = str(_FONT_HELVETICA_MEDIUM)
    bold_path = str(_FONT_HELVETICA_BOLD)

    size_mapping = {14: "xs", 17: "sm", 26: "md", 28: "lg", 38: "xl"}
    for size, key in size_mapping.items():
        _helvetica_cache[key] = ImageFont.truetype(medium_path, size)
        _helvetica_cache[f"{key}_bold"] = ImageFont.truetype(bold_path, size)

    return _helvetica_cache


def load_serif_font(size: int = 28) -> ImageFont.FreeTypeFont:
    """
    加载 Times New Roman Bold 字体（学生证专用）。
    直接使用项目内打包字体，不做回退。
    """
    return ImageFont.truetype(str(_FONT_TIMES_BOLD), size)


# ============ 文本绘制（打字机效果）============

def draw_text(draw: ImageDraw.Draw, pos: tuple, text: str,
              font, color: tuple = (30, 30, 30), spacing: int = -1,
              randomizer: "DocumentRandomizer | None" = None):
    """
    逐字符绘制，模拟打字机紧凑字间距。

    注意：不对坐标做微偏移。感知哈希破坏由图像级变换
    （透视/旋转/光照/噪声/模糊/JPEG）统一完成，
    避免相邻字段因独立偏移导致文字重叠。
    randomizer 参数保留以维持接口兼容，不再使用。
    """
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
        # 边缘裁剪（模拟手机拍摄未完全对准），每边独立，单位：像素
        self._crop_margins = (
            rng.randint(0, 15),   # 上
            rng.randint(0, 15),   # 右
            rng.randint(0, 15),   # 下
            rng.randint(0, 15),   # 左
        )
        # 折痕（0~2 条水平/垂直线条阴影，仅在边缘 15% 区域内）
        self._fold_count = rng.randint(0, 2)
        self._fold_params = [
            (
                rng.choice(["h", "v"]),            # 方向：水平/垂直
                rng.uniform(0.05, 0.15),           # 位置比例（仅边缘 15%）
                rng.choice([True, False]),          # True=靠近起始边，False=靠近末尾边
                rng.randint(3, 8),                  # 线宽（像素）
                rng.uniform(0.05, 0.15),            # 不透明度
            )
            for _ in range(self._fold_count)
        ]
        # 污渍（0~2 个椭圆色斑，仅在边缘 15% 区域内）
        self._stain_count = rng.randint(0, 2)
        self._stain_params = [
            (
                rng.choice(["tl", "tr", "bl", "br"]),   # 角落位置
                rng.randint(20, 50),                     # 椭圆 x 半径（像素）
                rng.randint(15, 40),                     # 椭圆 y 半径（像素）
                rng.randint(0, 30),                      # 相对角落的 x 偏移
                rng.randint(0, 30),                      # 相对角落的 y 偏移
                rng.uniform(0.06, 0.18),                 # 不透明度
                (rng.randint(140, 200),
                 rng.randint(110, 170),
                 rng.randint(60, 120)),                  # 污渍颜色（棕/黄调）
            )
            for _ in range(self._stain_count)
        ]

    def _apply_crop(self, img: Image.Image) -> Image.Image:
        """边缘裁剪 — 模拟手机拍摄未完全对准纸张"""
        top, right, bottom, left = self._crop_margins
        w, h = img.size
        new_left = left
        new_top = top
        new_right = w - right
        new_bottom = h - bottom
        # 保证不会裁剪过度（至少保留 80% 图像）
        if new_right - new_left < w * 0.8 or new_bottom - new_top < h * 0.8:
            return img
        return img.crop((new_left, new_top, new_right, new_bottom)).resize(
            (w, h), Image.Resampling.LANCZOS
        )

    def _apply_fold_lines(self, img: Image.Image) -> Image.Image:
        """折痕效果 — 在图像边缘区域叠加半透明线条阴影，模拟纸张折叠"""
        if not self._fold_params:
            return img
        try:
            import numpy as np
        except ImportError:
            return img

        arr = np.array(img, dtype=np.float32)
        h, w = arr.shape[:2]

        for direction, pos_ratio, near_start, thickness, opacity in self._fold_params:
            if direction == "h":
                # 水平折痕，限制在顶部或底部 15% 区域
                if near_start:
                    y_center = int(h * pos_ratio)              # 靠近顶部
                else:
                    y_center = int(h * (1.0 - pos_ratio))      # 靠近底部
                y1 = max(0, y_center - thickness // 2)
                y2 = min(h, y_center + thickness // 2 + 1)
                arr[y1:y2, :] *= (1.0 - opacity)
            else:
                # 垂直折痕，限制在左侧或右侧 15% 区域
                if near_start:
                    x_center = int(w * pos_ratio)              # 靠近左侧
                else:
                    x_center = int(w * (1.0 - pos_ratio))      # 靠近右侧
                x1 = max(0, x_center - thickness // 2)
                x2 = min(w, x_center + thickness // 2 + 1)
                arr[:, x1:x2] *= (1.0 - opacity)

        arr = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)

    def _apply_stains(self, img: Image.Image) -> Image.Image:
        """污渍效果 — 在图像角落区域叠加高斯模糊椭圆色斑，模拟咖啡渍/墨水点"""
        if not self._stain_params:
            return img
        try:
            import numpy as np
        except ImportError:
            return img

        arr = np.array(img, dtype=np.float32)
        h, w = arr.shape[:2]
        # 边缘安全区域：污渍中心只能出现在距边 15% 范围内
        edge_x = int(w * 0.15)
        edge_y = int(h * 0.15)

        for corner, rx, ry, ox, oy, opacity, color in self._stain_params:
            # 计算角落基准坐标
            if corner == "tl":
                cx, cy = ox + rx, oy + ry
            elif corner == "tr":
                cx, cy = w - ox - rx, oy + ry
            elif corner == "bl":
                cx, cy = ox + rx, h - oy - ry
            else:  # br
                cx, cy = w - ox - rx, h - oy - ry

            # 约束污渍中心在边缘区域
            cx = max(rx, min(edge_x + rx, cx))
            cy = max(ry, min(edge_y + ry, cy))

            # 构建椭圆高斯掩码
            ys, xs = np.ogrid[:h, :w]
            dist = ((xs - cx) / max(rx, 1)) ** 2 + ((ys - cy) / max(ry, 1)) ** 2
            mask = np.exp(-dist * 2.0)  # 高斯衰减
            mask = mask[:, :, np.newaxis] * opacity  # 扩展到 RGB

            # 混合污渍颜色
            stain_color = np.array(color, dtype=np.float32)
            arr = arr * (1.0 - mask) + stain_color * mask

        arr = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)

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

        执行顺序经过设计：
          1. 裁剪      — 模拟手机未完全对准纸张
          2. 透视变形  — 模拟纸张不平整 / 拍摄角度
          3. 轻微旋转  — 模拟手机未完全对齐
          4. 折痕      — 叠加边缘折叠线条阴影（几何变换后添加，避免被扭曲）
          5. 污渍      — 叠加边缘角落色斑（限制在图像边缘 15% 区域）
          6. 光照变换  — 亮度 / 色温偏移 + 渐变阴影
          7. 高斯噪声  — 模拟传感器噪声
          8. 高斯模糊  — 模拟轻微对焦偏差
          9. JPEG 重编码 — 引入自然压缩伪影

        折痕/污渍只出现在图像边缘区域，不影响核心数据字段可读性。
        """
        img = self._apply_crop(img)
        img = self._apply_perspective(img)
        img = self._apply_rotation(img)
        img = self._apply_fold_lines(img)
        img = self._apply_stains(img)
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


