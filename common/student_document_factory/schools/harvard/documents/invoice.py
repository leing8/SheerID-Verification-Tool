"""
哈佛大学学费发票生成器

使用双模板拼接：
  1. harvard-tuition-receipt1.png (1395×1401) — 主模板（哈佛校徽/地址头/费用表格区域）
  2. harvard-tuition-receipt2.png (1244×537)  — 底部声明（透明背景，含 Note / Wire Transfer /
     Total Amount Due / No Degree 警告 / Important 免责声明）

字体：Helvetica CE Medium / Bold（与真实哈佛发票一致）
  - md  (26px Medium)  — 地址、Invoice Number/Date、Transactions 标签、费用明细行
  - lg_bold (28px Bold) — Total Due for 行的加粗金额
  - xl_bold (38px Bold) — 头部 & 底部 Total Amount Due 大号金额

填充数据（共 8 处）：
  ① To: 下方 — 学生地址（4 行：收件人名/街道/城市+州+邮编/国家）
  ② Invoice Number — 发票编号
  ③ Invoice Date   — 当前日期
  ④ Total Amount Due（头部大字）— 总金额
  ⑤ Transactions for [Last, First]: — 费用表标题
  ⑥ 费用明细行     — Date / Description / Term / Amount（4 行）
  ⑦ Total Due for [Last, First]: — 费用合计行
  ⑧ Total Amount Due（底部声明区域）— 叠加 receipt2 后在其上填写总金额
"""

import time
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw

from .common import (
    INVOICE_TEMPLATE_1,
    INVOICE_TEMPLATE_2,
    DocumentRandomizer,
    draw_text,
    image_to_format,
    load_helvetica_fonts,
    seeded_rng,
)

if TYPE_CHECKING:
    from ..student_data import HarvardStudentData

# ============ 发票模板坐标（基于 harvard-tuition-receipt1.png, 1395×1401）============

_COORDS = {
    # ① To: 下方地址（左侧，4 行，行距约 26px）
    "to_name":     (82, 313),    # 收件人名称（如 COLFUTURO）
    "to_addr1":    (82, 342),    # 街道地址
    "to_addr2":    (82, 370),    # 城市 + 州 + 邮编
    "to_country":  (82, 397),    # 国家

    # ② ③ Invoice Number / Date（右上角，"Invoice Number:" 标签右侧）
    "invoice_number": (1023, 153),
    "invoice_date":   (1023, 227),

    # ④ Total Amount Due — 头部大字金额（"Total Amount Due:  $" 后面）
    "total_header": (1090, 320),

    # ⑤ Transactions for [姓名]:（费用表标题）
    "transactions_label": (82, 536),

    # ⑥ 费用明细行（表头行下方开始）
    "items_start_y": 600,
    "item_cols": {
        "date":        95,       # Date 列
        "description": 270,      # Description 列
        "term":        927,      # Term 列
        "amount":      1185,     # Amount 列
    },

    # ⑦ Total Due for 行（紧接明细末行，偏移 5px）
    "total_due_label_y_offset": 5,
}

# 每行费用明细的行高
_ITEM_LINE_HEIGHT = 30

# 底部声明（receipt2）与费用区域的间距
_FOOTER_GAP = 30

# ⑧ receipt2 叠加后，"Total Amount Due:" 金额的相对坐标
# 相对于 receipt2 粘贴起点 (footer_x, paste_y) 的偏移
_FOOTER_TOTAL_OFFSET = (1020, 110)

# Helvetica 字体在发票中使用的字间距（像素）
# 默认 draw_text spacing=-1 过于紧凑，此处使用 0 以匹配真实发票
_INVOICE_CHAR_SPACING = 0


def generate_invoice(student: "HarvardStudentData",
                     output_format: str = "png") -> bytes:
    """
    在 harvard-tuition-receipt1.png 上填充学生数据，
    叠加透明背景的 receipt2.png 并填写底部金额，返回图片字节。
    """
    if not INVOICE_TEMPLATE_1.exists():
        raise FileNotFoundError(f"哈佛学费发票模板不存在: {INVOICE_TEMPLATE_1}")

    rng = seeded_rng(student)
    fonts = load_helvetica_fonts()
    randomizer = DocumentRandomizer(rng)

    img = Image.open(INVOICE_TEMPLATE_1).convert("RGB")
    draw = ImageDraw.Draw(img)

    full_name = f"{student.last_name}, {student.first_name}"
    total = student.tuition_amount + student.fee_health + student.fee_activity + student.fee_gsc
    total_str = f"${total:,}.00"

    # ① To: 地址（Helvetica Medium 26px）
    addr = student.address
    draw_text(draw, _COORDS["to_name"],    addr[0], fonts["md"],
              spacing=_INVOICE_CHAR_SPACING, randomizer=randomizer)
    draw_text(draw, _COORDS["to_addr1"],   addr[1], fonts["md"],
              spacing=_INVOICE_CHAR_SPACING, randomizer=randomizer)
    draw_text(draw, _COORDS["to_addr2"],   addr[2], fonts["md"],
              spacing=_INVOICE_CHAR_SPACING, randomizer=randomizer)
    draw_text(draw, _COORDS["to_country"], addr[3], fonts["md"],
              spacing=_INVOICE_CHAR_SPACING, randomizer=randomizer)

    # ② Invoice Number（Helvetica Medium 26px）
    draw_text(draw, _COORDS["invoice_number"], student.invoice_number, fonts["md"],
              spacing=_INVOICE_CHAR_SPACING, randomizer=randomizer)

    # ③ Invoice Date（Helvetica Medium 26px）
    draw_text(draw, _COORDS["invoice_date"], time.strftime("%m/%d/%Y"), fonts["md"],
              spacing=_INVOICE_CHAR_SPACING, randomizer=randomizer)

    # ④ Total Amount Due 头部大字金额（Helvetica Bold 38px）
    draw_text(draw, _COORDS["total_header"], total_str, fonts["xl_bold"],
              spacing=_INVOICE_CHAR_SPACING, randomizer=randomizer)

    # ⑤ Transactions for [姓名]:（Helvetica Medium 26px）
    draw_text(draw, _COORDS["transactions_label"],
              f"Transactions for {full_name}:", fonts["md"],
              spacing=_INVOICE_CHAR_SPACING, randomizer=randomizer)

    # ⑥ 费用明细行（Helvetica Medium 26px）
    date_str = time.strftime("%Y-%m-%d")
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
        draw_text(draw, (cols["date"],        y), dt,             fonts["md"],
                  spacing=_INVOICE_CHAR_SPACING, randomizer=randomizer)
        draw_text(draw, (cols["description"], y), desc[:42],      fonts["md"],
                  spacing=_INVOICE_CHAR_SPACING, randomizer=randomizer)
        draw_text(draw, (cols["term"],        y), term,           fonts["md"],
                  spacing=_INVOICE_CHAR_SPACING, randomizer=randomizer)
        draw_text(draw, (cols["amount"],      y), f"${amt:,}.00", fonts["md"],
                  spacing=_INVOICE_CHAR_SPACING, randomizer=randomizer)
        y += _ITEM_LINE_HEIGHT

    # ⑦ Total Due for [姓名]:（标签 Medium 26px + 金额 Bold 28px）
    draw_text(draw, (cols["description"] + 510, y),
              f"Total Due for {full_name}:", fonts["md"],
              spacing=_INVOICE_CHAR_SPACING, randomizer=randomizer)
    draw_text(draw, (cols["amount"], y),
              total_str, fonts["lg_bold"],
              spacing=_INVOICE_CHAR_SPACING, randomizer=randomizer)

    # ⑧ 叠加底部声明（receipt2 透明背景）并填写底部 Total Amount Due 金额
    last_item_y = y + _ITEM_LINE_HEIGHT
    _overlay_footer(img, last_item_y, total_str, fonts, randomizer)

    return image_to_format(img, rng, output_format)


def _overlay_footer(img: Image.Image, last_item_y: int,
                    total_str: str, fonts: dict,
                    randomizer: DocumentRandomizer) -> None:
    """
    在费用明细末行下方叠加 receipt2.png 底部声明，
    并在 receipt2 的 "Total Amount Due:" 后面填写金额。

    receipt2 为透明背景 PNG，使用 alpha 通道覆盖。
    叠加后再在目标位置绘制金额文本。
    """
    if not INVOICE_TEMPLATE_2.exists():
        return

    footer = Image.open(INVOICE_TEMPLATE_2).convert("RGBA")
    paste_y = last_item_y + _FOOTER_GAP

    # 水平居中
    footer_x = (img.width - footer.width) // 2

    # 使用 alpha 通道作为 mask 实现透明叠加
    img.paste(footer.convert("RGB"), (footer_x, paste_y), mask=footer.split()[3])

    # 在 receipt2 的 "Total Amount Due:" 后面填写金额
    # 坐标 = receipt2 粘贴起点 + 相对偏移
    amount_x = footer_x + _FOOTER_TOTAL_OFFSET[0]
    amount_y = paste_y + _FOOTER_TOTAL_OFFSET[1]
    draw = ImageDraw.Draw(img)
    draw_text(draw, (amount_x, amount_y), total_str, fonts["xl_bold"],
              spacing=_INVOICE_CHAR_SPACING, randomizer=randomizer)
