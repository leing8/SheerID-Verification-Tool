"""
哈佛大学成绩单生成器

在 harvard-transcript.png 模板上填充学生数据：
  1. ISSUED TO 下方 — 学生地址（姓名/街道/城市/国家）
  2. Name: — 学生姓名
  3. ID: — 学号
  4. Printed: — 打印日期
  5. 学期标签 — 如 "Spring Term 2026"
  6. 课程列表 — COURSE / TITLE / CREDITS / EARNED / LEVEL / GRADE
"""

import time
from datetime import datetime
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw

from .common import (
    TRANSCRIPT_TEMPLATE,
    draw_text,
    generate_us_address,
    image_to_format,
    load_monospace_fonts,
    seeded_rng,
)

if TYPE_CHECKING:
    from ..student_data import HarvardStudentData

# ============ 成绩单模板坐标（基于 harvard-transcript.png）============

_COORDS = {
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
    在 harvard-transcript.png 模板上填充学生数据，返回图片字节。
    """
    if not TRANSCRIPT_TEMPLATE.exists():
        raise FileNotFoundError(f"哈佛成绩单模板不存在: {TRANSCRIPT_TEMPLATE}")

    rng = seeded_rng(student)
    fonts = load_monospace_fonts()

    img = Image.open(TRANSCRIPT_TEMPLATE).convert("RGB")
    draw = ImageDraw.Draw(img)

    # 1. ISSUED TO 地址
    addr = generate_us_address(student.first_name, student.last_name, rng)
    y = _COORDS["issued_to_line1"][1]
    for line in addr:
        draw_text(draw, (_COORDS["issued_to_line1"][0], y), line, fonts["sm_bold"])
        y += 15

    # 2. Name
    draw_text(draw, _COORDS["name"],
              f"{student.first_name} {student.last_name}", fonts["sm_bold"])

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

    return image_to_format(img, rng, output_format)
