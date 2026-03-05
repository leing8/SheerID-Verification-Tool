"""
哈佛大学学生证生成器

在 harvard-student-id.png 模板上填充学生数据 + 头像：
  1. 照片区域 — 真人头像（pravatar.cc）或灰色占位
  2. 姓名（大写）
  3. 学号 + SP 标识
  4. VALID THRU 有效期
  5. 条形码扰乱
"""

import logging
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

logger = logging.getLogger(__name__)

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


def generate_student_id_card(
    student: "HarvardStudentData",
    output_format: str = "png",
    *,
    fetch_avatar: bool = True,
) -> bytes:
    """
    在 harvard-student-id.png 模板上填充学生数据 + 头像，返回图片字节。

    Args:
        student:       学生数据
        output_format: 输出格式
        fetch_avatar:  是否从网络获取真人头像（False 时使用灰色占位图）
    """
    if not STUDENT_ID_TEMPLATE.exists():
        raise FileNotFoundError(f"哈佛学生证模板不存在: {STUDENT_ID_TEMPLATE}")

    logger.debug("学生证生成开始: student_id=%s, fetch_avatar=%s", student.student_id, fetch_avatar)

    rng = seeded_rng(student)

    img = Image.open(STUDENT_ID_TEMPLATE).convert("RGBA")
    draw = ImageDraw.Draw(img)

    font = load_serif_font(28)
    text_color = (0, 0, 0)

    # 1. 头像
    photo = _COORDS["photo"]
    photo_size = (photo[2] - photo[0], photo[3] - photo[1])
    if fetch_avatar:
        avatar = fetch_random_avatar(student.student_id, size=photo_size)
        logger.debug("[学生证 1/6] 头像: 网络获取, size=%s, 结果=%s", photo_size, "成功" if avatar else "占位图")
    else:
        avatar = Image.new("RGB", photo_size, (200, 200, 200))
        avatar_draw = ImageDraw.Draw(avatar)
        avatar_draw.rectangle(
            [(0, 0), (photo_size[0] - 1, photo_size[1] - 1)],
            outline=(80, 80, 80), width=2,
        )
        logger.debug("[学生证 1/6] 头像: 使用占位灰色图 (fetch_avatar=False)")
    if avatar:
        img.paste(avatar, (photo[0], photo[1]))

    # 重新获取 draw 引用（paste 之后可能失效）
    draw = ImageDraw.Draw(img)

    # 1.5 生日（MM/DD/YY 格式，位于 STUDENT 下方）
    birth_dt = datetime.strptime(student.birth_date, "%Y-%m-%d")
    birthday_text = birth_dt.strftime("%m/%d/%y")
    draw_text(draw, _COORDS["birthday"], birthday_text, font, color=text_color, spacing=0)
    logger.debug("[学生证 2/6] 生日: %s", birthday_text)

    # 2. 姓名（大写，逐字符绘制）
    name_text = f"{student.first_name} {student.last_name}".upper()
    draw_text(draw, _COORDS["name"], name_text, font, color=text_color, spacing=0)
    logger.debug("[学生证 3/6] 姓名: %s", name_text)

    # 3. 学号 + SP
    draw_text(draw, _COORDS["id_number"], f"{student.student_id} 0", font, color=text_color, spacing=0)
    draw_text(draw, _COORDS["sp_label"], "SP", font, color=text_color, spacing=0)
    logger.debug("[学生证 4/6] 学号: %s", student.student_id)

    # 4. VALID THRU
    now = datetime.now()
    valid_year = now.year if now.month <= 5 else now.year + 1
    valid_text = f"05/31/{valid_year}"
    draw_text(draw, _COORDS["valid_thru"], valid_text, font, color=text_color, spacing=0)
    logger.debug("[学生证 5/6] 有效期: %s", valid_text)

    # 5. 条形码扰乱：在原有条形码上叠加随机黑线
    bx1, by1, bx2, by2 = _COORDS["barcode"]
    for _ in range(rng.randint(3, 6)):
        x = rng.randint(bx1 + 5, bx2 - 5)
        draw.rectangle([(x, by1 + 3), (x + rng.randint(1, 4), by2 - 3)], fill=(0, 0, 0))

    # 6. 学院缩写（右下角动态渲染）
    draw_text(draw, _COORDS["school_code"], student.school_code, font, color=text_color, spacing=0)
    logger.debug("[学生证 6/6] 学院: %s, 条码扰乱完成", student.school_code)

    return image_to_format(img, rng, output_format, doc_type="student_id")

