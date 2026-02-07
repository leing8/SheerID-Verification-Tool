"""
收据生成模块
生成学费或书店收据
"""

import random
from datetime import datetime, timedelta

from PIL import Image, ImageDraw

from ..anti_detection import load_fonts, image_to_bytes


def generate_receipt_items(rng: random.Random, receipt_type: str = "tuition") -> list:
    """
    生成收据项目列表
    
    参数:
        rng: 随机数生成器
        receipt_type: "tuition" 学费 或 "bookstore" 书店
    """
    if receipt_type == "tuition":
        items = [
            ("Tuition Fee", rng.randint(8000, 15000)),
            ("Student Activity Fee", rng.randint(100, 300)),
            ("Technology Fee", rng.randint(150, 400)),
            ("Health Services Fee", rng.randint(200, 500)),
        ]
        if rng.random() < 0.5:
            items.append(("Library Fee", rng.randint(50, 150)))
        if rng.random() < 0.3:
            items.append(("Lab Fee", rng.randint(100, 300)))
    else:
        books = [
            "Introduction to Computer Science",
            "Calculus: Early Transcendentals",
            "Principles of Economics",
            "Organic Chemistry",
            "Physics for Scientists",
            "American History",
            "Statistics for Business",
        ]
        items = [(book, rng.randint(50, 250)) for book in rng.sample(books, rng.randint(2, 5))]
        if rng.random() < 0.4:
            items.append(("Notebook Bundle", rng.randint(15, 40)))
        if rng.random() < 0.3:
            items.append(("Calculator", rng.randint(30, 80)))
    
    return items


def create_receipt_image(
    first: str,
    last: str,
    school: str,
    rng: random.Random,
    receipt_type: str = "tuition",
) -> Image.Image:
    """
    创建收据图像
    
    参数:
        first: 名
        last: 姓
        school: 学校名称
        rng: 种子随机数生成器
        receipt_type: 收据类型
    
    返回:
        PIL Image 对象
    """
    # 收据尺寸
    w = 500 + rng.randint(-10, 10)
    h = 700 + rng.randint(-20, 20)
    
    # 背景色（模拟收据纸）
    bg_shade = rng.randint(248, 255)
    img = Image.new("RGB", (w, h), (bg_shade, bg_shade, bg_shade - rng.randint(0, 5)))
    draw = ImageDraw.Draw(img)
    
    fonts = load_fonts((24, 18, 14))

    y = 30 + rng.randint(-5, 5)
    
    # 学校名称
    draw.text((w // 2, y), school.upper(), fill=(0, 0, 0), font=fonts["title"], anchor="mm")
    y += 35
    
    # 收据类型标题
    title = "TUITION RECEIPT" if receipt_type == "tuition" else "BOOKSTORE RECEIPT"
    draw.text((w // 2, y), title, fill=(80, 80, 80), font=fonts["md"], anchor="mm")
    y += 30
    
    # 分隔线
    draw.line([(30, y), (w - 30, y)], fill=(150, 150, 150), width=1)
    y += 20
    
    # 学生信息
    draw.text((30, y), f"Student Name: {first} {last}", fill=(0, 0, 0), font=fonts["bold_sm"])
    y += 25
    
    draw.text((30, y), f"Student ID: {rng.randint(10000000, 99999999)}", fill=(0, 0, 0), font=fonts["sm"])
    y += 25
    
    # 收据编号和日期
    draw.text((30, y), f"Receipt #: R{rng.randint(100000, 999999)}", fill=(0, 0, 0), font=fonts["sm"])
    receipt_date = datetime.now() - timedelta(days=rng.randint(0, 30))
    draw.text((w - 150, y), f"Date: {receipt_date.strftime('%m/%d/%Y')}", fill=(0, 0, 0), font=fonts["sm"])
    y += 35
    
    # 分隔线
    draw.line([(30, y), (w - 30, y)], fill=(150, 150, 150), width=1)
    y += 20
    
    # 项目列表标题
    draw.text((30, y), "Description", fill=(0, 0, 0), font=fonts["bold_sm"])
    draw.text((w - 100, y), "Amount", fill=(0, 0, 0), font=fonts["bold_sm"])
    y += 25
    
    # 生成项目
    items = generate_receipt_items(rng, receipt_type)
    total = sum(amount for _, amount in items)
    
    for desc, amount in items:
        draw.text((30, y), desc[:32] + "..." if len(desc) > 35 else desc, fill=(0, 0, 0), font=fonts["sm"])
        draw.text((w - 100, y), f"${amount:,.2f}", fill=(0, 0, 0), font=fonts["sm"])
        y += 22
    
    y += 15
    draw.line([(w - 180, y), (w - 30, y)], fill=(0, 0, 0), width=1)
    y += 15
    
    # 总计
    draw.text((w - 180, y), "TOTAL:", fill=(0, 0, 0), font=fonts["bold_sm"])
    draw.text((w - 100, y), f"${total:,.2f}", fill=(0, 0, 0), font=fonts["bold_sm"])
    y += 35
    
    # 支付状态
    draw.text((w // 2, y), "*** PAID ***", fill=(0, 120, 0), font=fonts["bold_sm"], anchor="mm")
    y += 30
    
    # 支付方式
    payment_method = rng.choice(["Credit Card", "Debit Card", "Financial Aid", "Student Account"])
    draw.text((w // 2, y), f"Payment Method: {payment_method}", fill=(80, 80, 80), font=fonts["sm"], anchor="mm")
    
    # 页脚
    draw.text((w // 2, h - 50), "Thank you for your payment", fill=(100, 100, 100), font=fonts["sm"], anchor="mm")

    return img


def generate_receipt_bytes(img: Image.Image, rng: random.Random) -> bytes:
    """将收据图像转换为 PNG 字节（含反检测处理）"""
    return image_to_bytes(img, rng, noise_intensity=0.01)
