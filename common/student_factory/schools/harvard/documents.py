"""
哈佛大学文档生成器（模板填充方式）

在已有的模板图片上，在预设坐标位置填充学生数据。
3张模板图片位于同目录下：
  - harvard-transcript1.png       成绩单模板
  - harvard-tuition-receipt1.png  学费发票模板
  - harvard-student-id1.png       学生证模板

依赖：
  - anti_detection.py 中的 load_letter_gothic_fonts() / image_to_format()
  - avatar.py 中的 fetch_random_avatar() / create_placeholder_avatar()
"""

import hashlib
import random
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from .student_data import HarvardStudentData

# ============ 模板图片路径 ============
_TEMPLATES_DIR = Path(__file__).parent
_TRANSCRIPT_TEMPLATE   = _TEMPLATES_DIR / "harvard-transcript.png"
_INVOICE_TEMPLATE      = _TEMPLATES_DIR / "harvard-tuition-receipt.png"
_STUDENT_ID_TEMPLATE   = _TEMPLATES_DIR / "harvard-student-id.png"

# ============ 字体加载（与参考代码一致的 Letter Gothic 打字机风格）============

_letter_gothic_cache = {}


def _load_letter_gothic_fonts(sizes: Tuple[int, ...] = (14, 12, 11, 10)) -> dict:
    """加载 Letter Gothic Std 等宽字体（Harvard 成绩单专用）"""
    cache_key = sizes
    if cache_key in _letter_gothic_cache:
        return _letter_gothic_cache[cache_key]

    font_paths = [
        Path.home() / "AppData/Local/Microsoft/Windows/Fonts/LetterGothicStd.otf",
        Path.home() / "AppData/Local/Microsoft/Windows/Fonts/LetterGothicStd-Bold.otf",
        Path("C:/Windows/Fonts/LetterGothicStd.otf"),
        Path("C:/Windows/Fonts/LetterGothicStd-Bold.otf"),
        _TEMPLATES_DIR.parent.parent.parent / "fonts" / "LetterGothicStd.otf",
    ]

    regular_font = bold_font = None
    for p in font_paths:
        if p.exists():
            if "Bold" in p.name:
                bold_font = bold_font or str(p)
            else:
                regular_font = regular_font or str(p)

    if not regular_font:
        # 回退到 Courier New（系统内置等宽字体）
        for fallback in ("cour.ttf", "consola.ttf", "arial.ttf"):
            try:
                regular_font = fallback
                ImageFont.truetype(fallback, 12)
                bold_font = bold_font or fallback
                break
            except OSError:
                regular_font = None

    if not regular_font:
        default = ImageFont.load_default()
        fonts = {k: default for k in ("lg","lg_bold","md","md_bold","sm","sm_bold","xs","xs_bold")}
        _letter_gothic_cache[cache_key] = fonts
        return fonts

    bold_font = bold_font or regular_font

    fonts = {}
    size_mapping = {14: "lg", 12: "md", 11: "sm", 10: "xs"}
    for size, key in size_mapping.items():
        if size in sizes:
            fonts[key] = ImageFont.truetype(regular_font, size)
            fonts[f"{key}_bold"] = ImageFont.truetype(bold_font, size)

    _letter_gothic_cache[cache_key] = fonts
    return fonts


def _load_student_id_font(size: int = 28) -> ImageFont.FreeTypeFont:
    """加载 Times New Roman Bold 字体（学生证用）"""
    for font_name in ("timesbd.ttf", "Times New Roman Bold.ttf", "TIMESBD.TTF"):
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            continue
    return ImageFont.load_default()


# ============ 反检测处理 ============

def _apply_anti_detection(img: Image.Image, rng: random.Random,
                          noise_intensity: float = 0.008) -> Image.Image:
    """
    简化的反检测处理：添加微弱噪声防止AI检测"过于完美"的文档。
    与参考代码 anti_detection.py 中的 apply_anti_detection 功能一致。
    """
    try:
        import numpy as np
        arr = np.array(img, dtype=np.float32)
        noise = np.random.RandomState(rng.randint(0, 2**31)).normal(0, noise_intensity * 255, arr.shape)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)
    except ImportError:
        return img


def _image_to_format(img: Image.Image, rng: random.Random,
                     output_format: str = "png",
                     noise_intensity: float = 0.008) -> bytes:
    """将图像转为指定格式字节（含反检测处理）"""
    img = _apply_anti_detection(img, rng, noise_intensity)

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


def _fetch_random_avatar(seed: str, size: tuple = (139, 169)) -> Optional[Image.Image]:
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


# ============ 紧凑文本绘制（打字机效果）============

def _draw_text(draw: ImageDraw.Draw, pos: tuple, text: str,
               font, color: tuple = (30, 30, 30), spacing: int = -1):
    """逐字符绘制，模拟打字机紧凑字间距"""
    x, y = pos
    for char in text:
        draw.text((x, y), char, fill=color, font=font)
        bbox = font.getbbox(char)
        x += (bbox[2] - bbox[0] if bbox else 6) + spacing


# ============ 美国地址数据 ============

US_ADDRESSES = [
    {"city": "Boston",        "state": "MA", "zip": "02101"},
    {"city": "Cambridge",     "state": "MA", "zip": "02138"},
    {"city": "New York",      "state": "NY", "zip": "10001"},
    {"city": "Los Angeles",   "state": "CA", "zip": "90001"},
    {"city": "Chicago",       "state": "IL", "zip": "60601"},
    {"city": "San Francisco", "state": "CA", "zip": "94102"},
    {"city": "Seattle",       "state": "WA", "zip": "98101"},
    {"city": "Denver",        "state": "CO", "zip": "80201"},
    {"city": "Austin",        "state": "TX", "zip": "78701"},
    {"city": "Miami",         "state": "FL", "zip": "33101"},
]

US_STREETS = [
    "Main St", "Oak Ave", "Maple Dr", "Park Rd", "Cedar Ln",
    "Elm St", "Pine Ave", "Washington Blvd", "Lincoln Way", "Madison Ave",
    "Jefferson St", "Adams Rd", "Franklin Dr", "Liberty Ln", "Union St",
]


# ══════════════════════════════════════════════════════════════
# 文档1: 成绩单 — 在 harvard-transcript1.png 模板上填充数据
# ══════════════════════════════════════════════════════════════

# 成绩单模板坐标（基于 harvard-transcript1.png 的像素位置）
_TRANSCRIPT_COORDS = {
    # ISSUED TO: 下方地址区域（4行）
    "issued_to_line1": (73, 200),
    "issued_to_line2": (73, 218),
    "issued_to_line3": (73, 236),
    "issued_to_line4": (73, 254),
    # Name: / ID: / Printed:
    "name":       (90,  372),
    "student_id": (90,  387),
    "printed":    (655, 372),
    # 课程区域
    "semester_label":  (40, 470),
    "courses_start_y": 495,
    "course_cols": {
        "course":  130,
        "title":   245,
        "credits": 455,
        "earned":  530,
        "level":   606,
        "grade":   685,
    },
}
_COURSE_LINE_HEIGHT = 20


def generate_transcript(student: "HarvardStudentData",
                        output_format: str = "png") -> bytes:
    """
    在 harvard-transcript1.png 模板上填充学生数据。

    填充位置：
      1. ISSUED TO 下方 — 学生地址（姓名/街道/城市/国家）
      2. Name: — 学生姓名
      3. ID: — 学号
      4. Printed: — 打印日期
      5. 学期标签 — 如 "Summer Term 2025"
      6. 课程列表 — COURSE / TITLE / CREDITS / EARNED / LEVEL / GRADE
    """
    if not _TRANSCRIPT_TEMPLATE.exists():
        raise FileNotFoundError(f"Harvard 成绩单模板不存在: {_TRANSCRIPT_TEMPLATE}")

    rng = _seeded_rng(student)
    fonts = _load_letter_gothic_fonts()

    img = Image.open(_TRANSCRIPT_TEMPLATE).convert("RGB")
    draw = ImageDraw.Draw(img)
    coords = _TRANSCRIPT_COORDS

    # 1. ISSUED TO 地址
    addr = _generate_us_address(student.first_name, student.last_name, rng)
    y = coords["issued_to_line1"][1]
    for line in addr:
        _draw_text(draw, (coords["issued_to_line1"][0], y), line, fonts["sm_bold"])
        y += 15

    # 2. Name
    _draw_text(draw, coords["name"],
               f"{student.first_name} {student.last_name}", fonts["sm_bold"])

    # 3. ID
    _draw_text(draw, coords["student_id"], student.student_id, fonts["sm_bold"])

    # 4. Printed
    printed_date = time.strftime("%B %d, %Y")
    _draw_text(draw, coords["printed"], printed_date, fonts["sm_bold"])

    # 5. 学期标签
    semester = _get_semester(rng)
    _draw_text(draw, coords["semester_label"], semester, fonts["sm_bold"])

    # 6. 课程列表
    y = coords["courses_start_y"]
    cols = coords["course_cols"]
    for code, title, credits_val, grade, level in student.courses:
        _draw_text(draw, (cols["course"],  y), code,                   fonts["sm_bold"])
        _draw_text(draw, (cols["title"],   y), title[:40],             fonts["sm_bold"])
        _draw_text(draw, (cols["credits"], y), f"{credits_val:.2f}" if isinstance(credits_val, (int, float)) else str(credits_val), fonts["sm_bold"])
        _draw_text(draw, (cols["earned"],  y), f"{credits_val:.2f}" if isinstance(credits_val, (int, float)) else str(credits_val), fonts["sm_bold"])
        _draw_text(draw, (cols["level"],   y), level,                  fonts["sm_bold"])
        _draw_text(draw, (cols["grade"],   y), grade,                  fonts["sm_bold"])
        y += _COURSE_LINE_HEIGHT

    return _image_to_format(img, rng, output_format)


# ══════════════════════════════════════════════════════════════
# 文档2: 学费发票 — 在 harvard-tuition-receipt1.png 模板上填充数据
# ══════════════════════════════════════════════════════════════

# 发票模板坐标（基于 harvard-tuition-receipt1.png 的像素位置）
_INVOICE_COORDS = {
    # 学生信息（左上方，ISSUED TO 或 BILL TO 下方）
    "student_name":   (73, 185),
    "student_addr1":  (73, 203),
    "student_addr2":  (73, 221),
    "student_country":(73, 239),
    # 右上元数据
    "invoice_number": (640, 185),
    "invoice_date":   (640, 203),
    # 明细行起始
    "items_start_y":  310,
    "item_cols": {
        "date":        73,
        "description": 170,
        "term":        500,
        "amount":      680,
    },
    # 总额（大字）
    "total_amount":   (680, 145),
}
_ITEM_LINE_HEIGHT = 22


def generate_invoice(student: "HarvardStudentData",
                     output_format: str = "png") -> bytes:
    """
    在 harvard-tuition-receipt1.png 模板上填充学生数据。

    填充位置：
      1. 学生姓名和地址
      2. Invoice Number / Invoice Date
      3. 费用明细行（Tuition + 各种Fee）
      4. Total Amount
    """
    if not _INVOICE_TEMPLATE.exists():
        raise FileNotFoundError(f"Harvard 学费发票模板不存在: {_INVOICE_TEMPLATE}")

    rng = _seeded_rng(student)
    fonts = _load_letter_gothic_fonts()

    img = Image.open(_INVOICE_TEMPLATE).convert("RGB")
    draw = ImageDraw.Draw(img)
    coords = _INVOICE_COORDS

    # 1. 学生姓名与地址
    addr = _generate_us_address(student.first_name, student.last_name, rng)
    _draw_text(draw, coords["student_name"],    addr[0], fonts["sm_bold"])
    _draw_text(draw, coords["student_addr1"],   addr[1], fonts["sm_bold"])
    _draw_text(draw, coords["student_addr2"],   addr[2], fonts["sm_bold"])
    _draw_text(draw, coords["student_country"], addr[3], fonts["sm_bold"])

    # 2. 发票元数据
    _draw_text(draw, coords["invoice_number"], student.invoice_number, fonts["sm_bold"])
    _draw_text(draw, coords["invoice_date"],   time.strftime("%B %d, %Y"), fonts["sm_bold"])

    # 3. 费用明细行
    date_str = time.strftime("%m/%d/%Y")
    program_short = student.program.split("(")[0].strip()
    line_items = [
        (date_str, f"Tuition - {program_short}",        student.term, student.tuition_amount),
        (date_str, "Student Health Fee",                 student.term, 1682),
        (date_str, "Student Activities Fee",             student.term, 246),
        (date_str, "Student Facilities & Programs Fee",  student.term, 304),
    ]

    y = coords["items_start_y"]
    cols = coords["item_cols"]
    for dt, desc, term, amt in line_items:
        _draw_text(draw, (cols["date"],        y), dt,              fonts["sm_bold"])
        _draw_text(draw, (cols["description"], y), desc[:38],       fonts["sm_bold"])
        _draw_text(draw, (cols["term"],        y), term,            fonts["sm_bold"])
        _draw_text(draw, (cols["amount"],       y), f"${amt:,}.00", fonts["sm_bold"])
        y += _ITEM_LINE_HEIGHT

    # 4. 总额
    total = student.tuition_amount + 1682 + 246 + 304
    _draw_text(draw, coords["total_amount"], f"${total:,}.00", fonts["md_bold"])

    return _image_to_format(img, rng, output_format)


# ══════════════════════════════════════════════════════════════
# 文档3: 学生证 — 在 harvard-student-id1.png 模板上填充数据
# ══════════════════════════════════════════════════════════════

# 学生证模板坐标（基于 harvard-student-id1.png 的像素位置）
_STUDENT_ID_COORDS = {
    "photo":      (52, 40, 244, 240),    # 头像区域 (x1, y1, x2, y2)
    "name":       (25, 253),             # 姓名
    "id_number":  (25, 284),             # 学号
    "sp_label":   (205, 284),            # SP 标识
    "valid_thru": (423, 284),            # 过期日期
    "barcode":    (25, 316, 240, 366),   # 条形码扰乱区域
}


def generate_student_id_card(student: "HarvardStudentData",
                             output_format: str = "png") -> bytes:
    """
    在 harvard-student-id1.png 模板上填充学生数据 + 头像。

    填充位置：
      1. 照片区域 — 真人头像（pravatar.cc）或灰色占位
      2. 姓名（大写）
      3. 学号 + SP 标识
      4. VALID THRU 有效期
      5. 条形码扰乱
    """
    if not _STUDENT_ID_TEMPLATE.exists():
        raise FileNotFoundError(f"Harvard 学生证模板不存在: {_STUDENT_ID_TEMPLATE}")

    rng = _seeded_rng(student)

    img = Image.open(_STUDENT_ID_TEMPLATE).convert("RGB")
    draw = ImageDraw.Draw(img)
    coords = _STUDENT_ID_COORDS

    font = _load_student_id_font(28)
    text_color = (0, 0, 0)

    # 1. 头像
    photo = coords["photo"]
    photo_size = (photo[2] - photo[0], photo[3] - photo[1])
    avatar = _fetch_random_avatar(student.student_id, size=photo_size)
    if avatar:
        img.paste(avatar, (photo[0], photo[1]))

    # 重新获取 draw 引用（paste 之后可能失效）
    draw = ImageDraw.Draw(img)

    # 2. 姓名（大写，逐字符绘制）
    _draw_text(draw, coords["name"],
               f"{student.first_name} {student.last_name}".upper(),
               font, color=text_color, spacing=0)

    # 3. 学号 + SP
    _draw_text(draw, coords["id_number"],
               f"{student.student_id} 0",
               font, color=text_color, spacing=0)
    _draw_text(draw, coords["sp_label"],
               "SP",
               font, color=text_color, spacing=0)

    # 4. VALID THRU
    now = datetime.now()
    valid_year = now.year if now.month <= 5 else now.year + 1
    _draw_text(draw, coords["valid_thru"],
               f"05/31/{valid_year}",
               font, color=text_color, spacing=0)

    # 5. 条形码扰乱：在原有条形码上叠加随机黑线
    bx1, by1, bx2, by2 = coords["barcode"]
    for _ in range(rng.randint(3, 6)):
        x = rng.randint(bx1 + 5, bx2 - 5)
        draw.rectangle([(x, by1 + 3), (x + rng.randint(1, 4), by2 - 3)], fill=(0, 0, 0))

    return _image_to_format(img, rng, output_format)


# ============ 辅助函数 ============

def _seeded_rng(student: "HarvardStudentData") -> random.Random:
    """从学号创建确定性 RNG"""
    import hashlib
    seed = int(hashlib.sha256(student.student_id.encode()).hexdigest(), 16) % (2 ** 32)
    return random.Random(seed)


def _generate_us_address(first: str, last: str, rng: random.Random) -> tuple:
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


def _get_semester(rng: random.Random) -> str:
    """生成学期标签"""
    now = datetime.now()
    year = now.year
    if rng.random() < 0.3:
        year -= 1
    terms = ["Spring Term", "Summer Term", "Fall Term"]
    return f"{rng.choice(terms)} {year}"
