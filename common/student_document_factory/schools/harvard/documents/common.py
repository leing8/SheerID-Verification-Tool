"""
哈佛文档生成 — 公共工具模块

包含所有文档共享的：
  - 字体加载
  - 文本绘制（支持坐标微偏移）
  - 头像获取
  - 确定性随机数工具
  - image_to_format()  —— 文档输出入口（内嵌混淆流水线，调用方无感）

文档混淆逻辑已迁移至：
  common.student_document_factory.document_obfuscation

字体直接使用项目内打包的 TTF 文件，不依赖宿主机。
"""

import hashlib
import random
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from ....document_obfuscation import DEFAULT_CONFIG, ObfuscationConfig, ObfuscationPipeline

if TYPE_CHECKING:
    from ..student_data import HarvardStudentData

# ============ 路径常量 ============

# documents/ 目录（fonts/ 和 templates/ 均在此目录下）
_DOCUMENTS_DIR = Path(__file__).parent

# 模板图片路径（templates/ 子目录）
_TEMPLATES_DIR = _DOCUMENTS_DIR / "templates"
TRANSCRIPT_TEMPLATE   = _TEMPLATES_DIR / "harvard-transcript.png"
TRANSCRIPT_TEMPLATE_1 = _TEMPLATES_DIR / "harvard-transcript1.png"
TRANSCRIPT_TEMPLATE_2 = _TEMPLATES_DIR / "harvard-transcript2.png"
INVOICE_TEMPLATE      = _TEMPLATES_DIR / "harvard-tuition-receipt.png"
INVOICE_TEMPLATE_1    = _TEMPLATES_DIR / "harvard-tuition-receipt1.png"
INVOICE_TEMPLATE_2    = _TEMPLATES_DIR / "harvard-tuition-receipt2.png"
STUDENT_ID_TEMPLATE   = _TEMPLATES_DIR / "harvard-student-id.png"

# 字体路径（fonts/ 子目录，项目内打包，不依赖宿主机）
_FONTS_DIR = _DOCUMENTS_DIR / "fonts"
_FONT_LETTER_GOTHIC      = _FONTS_DIR / "Letter Gothic Std.ttf"
_FONT_LETTER_GOTHIC_BOLD = _FONTS_DIR / "Letter Gothic Std Bold.ttf"
_FONT_TIMES              = _FONTS_DIR / "Times New Roman.ttf"
_FONT_TIMES_BOLD         = _FONTS_DIR / "Times New Roman Bold.ttf"
_FONT_HELVETICA_MEDIUM   = _FONTS_DIR / "Helvetica CE Medium.otf"
_FONT_HELVETICA_BOLD     = _FONTS_DIR / "Helvetica CE Bold.otf"

# ============ 字体加载 ============

_monospace_cache: dict = {}
_helvetica_cache: dict = {}


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
    bold_path    = str(_FONT_LETTER_GOTHIC_BOLD)

    fonts: dict = {}
    size_mapping = {14: "lg", 12: "md", 11: "sm", 10: "xs"}
    for size, key in size_mapping.items():
        if size in sizes:
            fonts[key]           = ImageFont.truetype(regular_path, size)
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
    bold_path   = str(_FONT_HELVETICA_BOLD)

    size_mapping = {14: "xs", 17: "sm", 26: "md", 28: "lg", 38: "xl"}
    for size, key in size_mapping.items():
        _helvetica_cache[key]           = ImageFont.truetype(medium_path, size)
        _helvetica_cache[f"{key}_bold"] = ImageFont.truetype(bold_path, size)

    return _helvetica_cache


def load_serif_font(size: int = 28) -> ImageFont.FreeTypeFont:
    """
    加载 Times New Roman Bold 字体（学生证专用）。
    直接使用项目内打包字体，不做回退。
    """
    return ImageFont.truetype(str(_FONT_TIMES_BOLD), size)


# ============ 文本绘制（打字机效果）============

def draw_text(
    draw: ImageDraw.Draw,
    pos: tuple,
    text: str,
    font,
    color: tuple = (30, 30, 30),
    spacing: int = -1,
) -> None:
    """
    逐字符绘制，模拟打字机紧凑字间距。

    感知哈希破坏由 ObfuscationPipeline 统一完成，
    避免相邻字段因独立偏移导致文字重叠。
    """
    x, y = pos
    for char in text:
        draw.text((x, y), char, fill=color, font=font)
        bbox = font.getbbox(char)
        x += (bbox[2] - bbox[0] if bbox else 6) + spacing


# ============ 文档输出（混淆流水线入口）============

def image_to_format(
    img: Image.Image,
    rng: random.Random,
    output_format: str = "png",
    config: ObfuscationConfig = DEFAULT_CONFIG,
    doc_type: str = "",
) -> bytes:
    """
    将图像转为指定格式字节（含完整文档混淆处理）。

    内部通过 ObfuscationPipeline 应用所有混淆效果（污渍 / 折痕 / 裁剪 /
    3D变换 / 拍照模拟），对调用方完全透明。

    Args:
        img:           原始 PIL 图像。
        rng:           确定性随机数生成器（由 student_id 派生）。
        output_format: 输出格式（"png" | "jpg" | "jpeg"），默认 "png"。
        config:        混淆配置，默认全部效果启用。
        doc_type:      文档类型字符串（影响部分效果，如 fading 仅限 student_id）。

    Returns:
        图像字节（PNG 或 JPEG）。
    """
    pipeline = ObfuscationPipeline(rng, config=config, doc_type=doc_type)
    img = pipeline.apply(img)

    buf = BytesIO()
    fmt = output_format.lower()
    if fmt in ("jpg", "jpeg"):
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
    unique_id  = hashlib.md5(seed.encode()).hexdigest()[:16]
    request_size = max(size[0], size[1])
    url = f"https://i.pravatar.cc/{request_size}?u={unique_id}"

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
        # 占位图：浅灰背景 + 深色边框
        avatar_img = Image.new("RGB", size, (200, 200, 200))
        avatar_draw = ImageDraw.Draw(avatar_img)
        avatar_draw.rectangle(
            [(0, 0), (size[0] - 1, size[1] - 1)],
            outline=(80, 80, 80), width=2,
        )
    else:
        # 裁剪到证件照比例
        w, h = avatar_img.size
        target_ratio  = size[0] / size[1]
        current_ratio = w / h
        if current_ratio > target_ratio:
            new_w = int(h * target_ratio)
            left  = (w - new_w) // 2
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
