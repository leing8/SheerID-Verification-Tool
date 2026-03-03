"""
哈佛大学成绩单生成器

使用双模板拼接：
  1. harvard-transcript1.png — 主模板（头部/地址/课程表头）
  2. harvard-transcript2.png — 底部声明（课程末行下方叠加）

填充数据：
  1. ISSUED TO 下方 — 学生地址（姓名/街道/城市/国家）
  2. Name: — 学生姓名
  3. ID: — 学号
  4. Printed: — 打印日期
  5. 学期标签 — 如 "Spring Term 2026"
  6. 课程列表 — COURSE / TITLE / CREDITS / EARNED / LEVEL / GRADE
  7. 底部声明拼接
"""

import time
from datetime import datetime
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw

from .common import (
    TRANSCRIPT_TEMPLATE_1,
    TRANSCRIPT_TEMPLATE_2,
    draw_text,
    image_to_format,
    load_monospace_fonts,
    seeded_rng,
)

if TYPE_CHECKING:
    from ..student_data import HarvardStudentData

# ============ 成绩单模板坐标（基于 harvard-transcript1.png）============

_COORDS = {
    # ISSUED TO: 下方地址区域（4行）
    "issued_to_lines": (70, 185),
    # Name: / ID: / Printed:
    "name":       (87,  359),
    "student_id": (87,  375),
    "printed":    (652, 359),
    # 课程区域
    "semester_label":  (37, 450),
    "courses_start_y": 468,
    "course_cols": {
        "course":  120,
        "title":   230,
        "credits": 460,
        "earned":  530,
        "level":   606,
        "grade":   685,
    },
}
_COURSE_LINE_HEIGHT = 15

# 底部声明与课程末行的间距（像素）
_FOOTER_GAP = 30


def get_safe_zones(img_w: int, img_h: int) -> list:
    """
    返回成绩单图像的核心数据保护区列表。

    SheerID 审核要求以下字段必须清晰可读：
      - 学生姓名（ISSUED TO 地址区 + Name 行）
      - 学号（ID 行）
      - 学校与学期信息（学期标签 + 课程列表）
      - 打印日期（Printed 行）

    保护区覆盖上述区域及合理边距，确保污渍不遮挡任何关键字段。
    """
    from ....document_obfuscation.safe_zone import SafeZone
    return [
        # ISSUED TO: 下方学生地址（4 行，约 60px 高）
        SafeZone(x1=50, y1=175, x2=img_w - 20, y2=270,
                 padding=15, label="issued_to_address"),
        # Name: / ID: / Printed: 行
        SafeZone(x1=50, y1=345, x2=img_w - 20, y2=395,
                 padding=15, label="name_id_printed"),
        # 学期标签 + 完整课程列表区域（从标签到页面底部）
        SafeZone(x1=20, y1=435, x2=img_w - 20, y2=img_h - 20,
                 padding=10, label="semester_and_courses"),
    ]


def _get_semester(rng) -> str:
    """生成学期标签"""
    now = datetime.now()
    year = now.year
    if rng.random() < 0.3:
        year -= 1
    terms = ["Spring Term", "Summer Term", "Fall Term"]
    return f"{rng.choice(terms)} {year}"


def generate_transcript(student: "HarvardStudentData",
                        output_format: str = "png") -> bytes:
    """
    在 harvard-transcript1.png 上填充学生数据，
    课程末行下方拼接 harvard-transcript2.png，返回图片字节。
    """
    if not TRANSCRIPT_TEMPLATE_1.exists():
        raise FileNotFoundError(f"哈佛成绩单主模板不存在: {TRANSCRIPT_TEMPLATE_1}")

    rng = seeded_rng(student)
    fonts = load_monospace_fonts()

    img = Image.open(TRANSCRIPT_TEMPLATE_1).convert("RGB")
    draw = ImageDraw.Draw(img)

    # 1. ISSUED TO 地址
    addr = student.address
    y = _COORDS["issued_to_lines"][1]
    for line in addr:
        draw_text(draw, (_COORDS["issued_to_lines"][0], y), line, fonts["sm_bold"])
        y += 15

    # 2. Name
    draw_text(draw, _COORDS["name"], f"{student.first_name} {student.last_name}", fonts["sm_bold"])

    # 3. ID
    draw_text(draw, _COORDS["student_id"], student.student_id, fonts["sm_bold"])

    # 4. Printed
    printed_date = time.strftime("%B %d, %Y")
    draw_text(draw, _COORDS["printed"], printed_date, fonts["sm_bold"])

    # 5. 学期标签
    semester = _get_semester(rng)
    draw_text(draw, _COORDS["semester_label"], semester, fonts["sm_bold"])

    # 6. 课程列表
    y = _COORDS["courses_start_y"]
    cols = _COORDS["course_cols"]
    for code, title, credits_val, grade, level in student.courses:
        draw_text(draw, (cols["course"],  y), code,       fonts["sm_bold"])
        draw_text(draw, (cols["title"],   y), title[:40], fonts["sm_bold"])
        credits_str = f"{credits_val:.2f}" if isinstance(credits_val, (int, float)) else str(credits_val)
        draw_text(draw, (cols["credits"], y), credits_str, fonts["sm_bold"])
        draw_text(draw, (cols["earned"],  y), credits_str, fonts["sm_bold"])
        draw_text(draw, (cols["level"],   y), level,       fonts["sm_bold"])
        draw_text(draw, (cols["grade"],   y), grade,       fonts["sm_bold"])
        y += _COURSE_LINE_HEIGHT

    # 7. 拼接底部声明（transcript2）
    last_course_y = y
    img = _splice_footer(img, last_course_y, rng)

    return image_to_format(img, rng, output_format, doc_type="transcript")



def _splice_footer(img: Image.Image, last_course_y: int,
                   rng) -> Image.Image:
    """
    在课程末行下方叠加 transcript2.png 底部声明。
    transcript2 为透明背景 PNG，直接用 alpha 通道覆盖。
    """
    if not TRANSCRIPT_TEMPLATE_2.exists():
        return img

    footer = Image.open(TRANSCRIPT_TEMPLATE_2).convert("RGBA")
    paste_y = last_course_y + _FOOTER_GAP

    # 水平居中
    footer_x = (img.width - footer.width) // 2

    # 使用 alpha 通道作为 mask 实现透明叠加
    img.paste(footer.convert("RGB"), (footer_x, paste_y), mask=footer.split()[3])

    return img
