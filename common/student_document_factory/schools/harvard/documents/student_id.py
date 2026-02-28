"""
哈佛大学学生证生成器

在 harvard-student-id.png 模板上填充学生数据 + 头像：
  1. 照片区域 — 真人头像（pravatar.cc）或灰色占位
  2. 姓名（大写）
  3. 学号 + SP 标识
  4. VALID THRU 有效期
  5. 条形码扰乱
"""

from datetime import datetime
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw

from .common import (
    STUDENT_ID_TEMPLATE,
    draw_text,
    fetch_random_avatar,
    image_to_format,
    load_serif_font,
    seeded_rng,
)

if TYPE_CHECKING:
    from ..student_data import HarvardStudentData

# ============ 学生证模板坐标（基于 harvard-student-id.png）============

_COORDS = {
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
    在 harvard-student-id.png 模板上填充学生数据 + 头像，返回图片字节。
    """
    if not STUDENT_ID_TEMPLATE.exists():
        raise FileNotFoundError(f"哈佛学生证模板不存在: {STUDENT_ID_TEMPLATE}")

    rng = seeded_rng(student)

    img = Image.open(STUDENT_ID_TEMPLATE).convert("RGB")
    draw = ImageDraw.Draw(img)

    font = load_serif_font(28)
    text_color = (0, 0, 0)

    # 1. 头像
    photo = _COORDS["photo"]
    photo_size = (photo[2] - photo[0], photo[3] - photo[1])
    avatar = fetch_random_avatar(student.student_id, size=photo_size)
    if avatar:
        img.paste(avatar, (photo[0], photo[1]))

    # 重新获取 draw 引用（paste 之后可能失效）
    draw = ImageDraw.Draw(img)

    # 2. 姓名（大写，逐字符绘制）
    draw_text(draw, _COORDS["name"],
              f"{student.first_name} {student.last_name}".upper(),
              font, color=text_color, spacing=0)

    # 3. 学号 + SP
    draw_text(draw, _COORDS["id_number"],
              f"{student.student_id} 0",
              font, color=text_color, spacing=0)
    draw_text(draw, _COORDS["sp_label"],
              "SP",
              font, color=text_color, spacing=0)

    # 4. VALID THRU
    now = datetime.now()
    valid_year = now.year if now.month <= 5 else now.year + 1
    draw_text(draw, _COORDS["valid_thru"],
              f"05/31/{valid_year}",
              font, color=text_color, spacing=0)

    # 5. 条形码扰乱：在原有条形码上叠加随机黑线
    bx1, by1, bx2, by2 = _COORDS["barcode"]
    for _ in range(rng.randint(3, 6)):
        x = rng.randint(bx1 + 5, bx2 - 5)
        draw.rectangle([(x, by1 + 3), (x + rng.randint(1, 4), by2 - 3)], fill=(0, 0, 0))

    return image_to_format(img, rng, output_format)
