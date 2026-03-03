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
    "photo":      (48, 32, 242, 235),    # 头像区域 (x1, y1, x2, y2)
    "birthday":   (373, 212),            # 生日（STUDENT 下方）
    "name":       (21, 243),             # 姓名
    "id_number":  (21, 273),             # 学号
    "sp_label":   (201, 273),            # SP 标识
    "valid_thru": (419, 273),            # 过期日期
    "barcode":    (21, 308, 234, 359),   # 条形码扰乱区域
    "school_code": (476, 330),           # 学院缩写（右下角，动态渲染）
}


def get_safe_zones(img_w: int, img_h: int) -> list:
    """
    返回学生证图像的核心数据保护区列表。

    SheerID 审核要求以下字段必须清晰可读：
      - 学生头像（证件照）
      - 学生姓名（大写）
      - 学号
      - 有效期（VALID THRU）
      - 生日

    保护区覆盖上述区域及合理边距，确保污渍不遮挡任何关键字段。
    """
    from ....document_obfuscation.safe_zone import SafeZone
    p = _COORDS
    return [
        # 头像区域（关键身份标识）
        SafeZone(x1=p["photo"][0], y1=p["photo"][1],
                 x2=p["photo"][2], y2=p["photo"][3],
                 padding=15, label="photo"),
        # 生日行
        SafeZone(x1=p["birthday"][0], y1=p["birthday"][1],
                 x2=img_w - 10, y2=p["birthday"][1] + 30,
                 padding=12, label="birthday"),
        # 姓名行
        SafeZone(x1=p["name"][0], y1=p["name"][1],
                 x2=img_w - 10, y2=p["name"][1] + 30,
                 padding=12, label="name"),
        # 学号 + SP + VALID THRU 行
        SafeZone(x1=p["id_number"][0], y1=p["id_number"][1],
                 x2=img_w - 10, y2=p["id_number"][1] + 30,
                 padding=12, label="id_and_valid_thru"),
    ]


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

    # 1.5 生日（MM/DD/YY 格式，位于 STUDENT 下方）
    birth_dt = datetime.strptime(student.birth_date, "%Y-%m-%d")
    birthday_text = birth_dt.strftime("%m/%d/%y")
    draw_text(draw, _COORDS["birthday"], birthday_text, font, color=text_color, spacing=0)

    # 2. 姓名（大写，逐字符绘制）
    draw_text(draw, _COORDS["name"], f"{student.first_name} {student.last_name}".upper(), font, color=text_color, spacing=0)

    # 3. 学号 + SP
    draw_text(draw, _COORDS["id_number"], f"{student.student_id} 0", font, color=text_color, spacing=0)
    draw_text(draw, _COORDS["sp_label"], "SP", font, color=text_color, spacing=0)

    # 4. VALID THRU
    now = datetime.now()
    valid_year = now.year if now.month <= 5 else now.year + 1
    draw_text(draw, _COORDS["valid_thru"], f"05/31/{valid_year}", font, color=text_color, spacing=0)

    # 5. 条形码扰乱：在原有条形码上叠加随机黑线
    bx1, by1, bx2, by2 = _COORDS["barcode"]
    for _ in range(rng.randint(3, 6)):
        x = rng.randint(bx1 + 5, bx2 - 5)
        draw.rectangle([(x, by1 + 3), (x + rng.randint(1, 4), by2 - 3)], fill=(0, 0, 0))

    # 6. 学院缩写（右下角动态渲染）
    draw_text(draw, _COORDS["school_code"], student.school_code, font, color=text_color, spacing=0)

    return image_to_format(img, rng, output_format, doc_type="student_id")
