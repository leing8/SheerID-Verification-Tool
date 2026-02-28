"""
哈佛文档生成 — 公共工具模块

包含所有文档共享的：字体加载、文本绘制、反检测处理、头像获取、地址生成。
字体直接使用项目内打包的 TTF 文件，不依赖宿主机。
"""

import hashlib
import random
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from ..student_data import HarvardStudentData

# ============ 路径常量 ============

# 上层 harvard/ 目录（fonts/ 和 templates/ 均在此目录下）
_HARVARD_DIR = Path(__file__).parent.parent

# 模板图片路径（templates/ 子目录）
_TEMPLATES_DIR = _HARVARD_DIR / "templates"
TRANSCRIPT_TEMPLATE = _TEMPLATES_DIR / "harvard-transcript.png"
INVOICE_TEMPLATE = _TEMPLATES_DIR / "harvard-tuition-receipt.png"
STUDENT_ID_TEMPLATE = _TEMPLATES_DIR / "harvard-student-id.png"

# 字体路径（fonts/ 子目录，项目内打包，不依赖宿主机）
_FONTS_DIR = _HARVARD_DIR / "fonts"
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


# ============ 文本绘制（打字机效果）============

def draw_text(draw: ImageDraw.Draw, pos: tuple, text: str,
              font, color: tuple = (30, 30, 30), spacing: int = -1):
    """逐字符绘制，模拟打字机紧凑字间距"""
    x, y = pos
    for char in text:
        draw.text((x, y), char, fill=color, font=font)
        bbox = font.getbbox(char)
        x += (bbox[2] - bbox[0] if bbox else 6) + spacing


# ============ 反检测处理 ============

def apply_anti_detection(img: Image.Image, rng: random.Random,
                         noise_intensity: float = 0.008) -> Image.Image:
    """
    添加微弱噪声防止AI检测"过于完美"的文档。
    """
    try:
        import numpy as np
        arr = np.array(img, dtype=np.float32)
        noise = np.random.RandomState(rng.randint(0, 2 ** 31)).normal(
            0, noise_intensity * 255, arr.shape
        )
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)
    except ImportError:
        return img


def image_to_format(img: Image.Image, rng: random.Random,
                    output_format: str = "png",
                    noise_intensity: float = 0.008) -> bytes:
    """将图像转为指定格式字节（含反检测处理）"""
    img = apply_anti_detection(img, rng, noise_intensity)

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
    """从 pravatar.cc 获取真人头像，失败返回占位灰色渐变图"""
    cache_key = hashlib.md5(f"{seed}_{size}".encode()).hexdigest()
    if cache_key in _avatar_cache:
        return _avatar_cache[cache_key].copy()

    avatar_img = None
    try:
        unique_id = hashlib.md5(seed.encode()).hexdigest()[:16]
        url = f"https://i.pravatar.cc/{max(size)}?u={unique_id}"

        try:
            from curl_cffi import requests as cffi_requests
            resp = cffi_requests.get(url, timeout=10, impersonate="chrome120")
        except ImportError:
            import requests
            resp = requests.get(url, timeout=10)

        if resp.status_code == 200 and len(resp.content) > 1000:
            avatar_img = Image.open(BytesIO(resp.content)).convert("RGB")
    except Exception:
        pass

    if avatar_img is None:
        # 占位灰色渐变
        avatar_img = Image.new("RGB", size, (180, 180, 180))
        pixels = avatar_img.load()
        for y in range(size[1]):
            for x in range(size[0]):
                gray = 160 + int(40 * y / size[1])
                pixels[x, y] = (gray, gray, gray)
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


# ============ 美国地址数据 ============

US_ADDRESSES = [
    {"city": "Boston", "state": "MA", "zip": "02101"},
    {"city": "Cambridge", "state": "MA", "zip": "02138"},
    {"city": "New York", "state": "NY", "zip": "10001"},
    {"city": "Los Angeles", "state": "CA", "zip": "90001"},
    {"city": "Chicago", "state": "IL", "zip": "60601"},
    {"city": "San Francisco", "state": "CA", "zip": "94102"},
    {"city": "Seattle", "state": "WA", "zip": "98101"},
    {"city": "Denver", "state": "CO", "zip": "80201"},
    {"city": "Austin", "state": "TX", "zip": "78701"},
    {"city": "Miami", "state": "FL", "zip": "33101"},
]

US_STREETS = [
    "Main St", "Oak Ave", "Maple Dr", "Park Rd", "Cedar Ln",
    "Elm St", "Pine Ave", "Washington Blvd", "Lincoln Way", "Madison Ave",
    "Jefferson St", "Adams Rd", "Franklin Dr", "Liberty Ln", "Union St",
]


def generate_us_address(first: str, last: str, rng: random.Random) -> tuple:
    """生成随机美国地址（4行元组）"""
    addr = rng.choice(US_ADDRESSES)
    street_num = rng.randint(100, 9999)
    street = rng.choice(US_STREETS)
    apt = f", Apt {rng.randint(1, 999)}" if rng.random() < 0.3 else ""

    return (
        f"{first} {last}",
        f"{street_num} {street}{apt}",
        f"{addr['city']}, {addr['state']} {addr['zip']}",
        "United States",
    )
