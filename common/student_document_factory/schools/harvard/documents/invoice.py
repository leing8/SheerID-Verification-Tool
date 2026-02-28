"""
哈佛大学学费发票生成器

在 harvard-tuition-receipt.png 模板上填充学生数据：
  1. 学生姓名和地址
  2. Invoice Number / Invoice Date
  3. 费用明细行（Tuition + Health Fee + Activity Fee + GSC Fee）
  4. Total Amount

所有数据均来自传入的 HarvardStudentData 对象，本模块不直接导入任何数据常量。
"""

import time
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw

from .common import (
    INVOICE_TEMPLATE,
    DocumentRandomizer,
    draw_text,
    image_to_format,
    load_monospace_fonts,
    seeded_rng,
)

if TYPE_CHECKING:
    from ..student_data import HarvardStudentData

# ============ 发票模板坐标（基于 harvard-tuition-receipt.png）============

_COORDS = {
    # 学生信息（左上方）
    "student_name":    (73, 185),
    "student_addr1":   (73, 203),
    "student_addr2":   (73, 221),
    "student_country": (73, 239),
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
    "total_amount": (680, 145),
}
_ITEM_LINE_HEIGHT = 22


def generate_invoice(student: "HarvardStudentData",
                     output_format: str = "png") -> bytes:
    """
    在 harvard-tuition-receipt.png 模板上填充学生数据，返回图片字节。

    费用明细直接读取 student 对象的 fee_health / fee_activity / fee_gsc 字段，
    不依赖任何外部常量。
    """
    if not INVOICE_TEMPLATE.exists():
        raise FileNotFoundError(f"哈佛学费发票模板不存在: {INVOICE_TEMPLATE}")

    rng = seeded_rng(student)
    fonts = load_monospace_fonts()
    randomizer = DocumentRandomizer(rng)

    img = Image.open(INVOICE_TEMPLATE).convert("RGB")
    draw = ImageDraw.Draw(img)

    # 1. 学生姓名与地址
    addr = student.address
    draw_text(draw, _COORDS["student_name"],    addr[0], fonts["sm_bold"],
              randomizer=randomizer)
    draw_text(draw, _COORDS["student_addr1"],   addr[1], fonts["sm_bold"],
              randomizer=randomizer)
    draw_text(draw, _COORDS["student_addr2"],   addr[2], fonts["sm_bold"],
              randomizer=randomizer)
    draw_text(draw, _COORDS["student_country"], addr[3], fonts["sm_bold"],
              randomizer=randomizer)

    # 2. 发票元数据
    draw_text(draw, _COORDS["invoice_number"], student.invoice_number, fonts["sm_bold"],
              randomizer=randomizer)
    draw_text(draw, _COORDS["invoice_date"],   time.strftime("%B %d, %Y"), fonts["sm_bold"],
              randomizer=randomizer)

    # 3. 费用明细行
    date_str = time.strftime("%m/%d/%Y")
    program_short = student.program.split("(")[0].strip()
    line_items = [
        (date_str, f"Tuition - {program_short}",              student.term, student.tuition_amount),
        (date_str, "Student Health Insurance Plan",            student.term, student.fee_health),
        (date_str, "Student Activities Fee",                   student.term, student.fee_activity),
        (date_str, "Harvard Griffin GSAS Student Council Fee", student.term, student.fee_gsc),
    ]

    y = _COORDS["items_start_y"]
    cols = _COORDS["item_cols"]
    for dt, desc, term, amt in line_items:
        draw_text(draw, (cols["date"],        y), dt,              fonts["sm_bold"],
                  randomizer=randomizer)
        draw_text(draw, (cols["description"], y), desc[:38],       fonts["sm_bold"],
                  randomizer=randomizer)
        draw_text(draw, (cols["term"],        y), term,            fonts["sm_bold"],
                  randomizer=randomizer)
        draw_text(draw, (cols["amount"],      y), f"${amt:,}.00",  fonts["sm_bold"],
                  randomizer=randomizer)
        y += _ITEM_LINE_HEIGHT

    # 4. 总额
    total = student.tuition_amount + student.fee_health + student.fee_activity + student.fee_gsc
    draw_text(draw, _COORDS["total_amount"], f"${total:,}.00", fonts["md_bold"],
              randomizer=randomizer)

    return image_to_format(img, rng, output_format)
