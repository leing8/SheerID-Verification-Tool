"""
学生证生成模块
提供学生证相关的公共工具函数
"""

import random
from datetime import datetime

from PIL import Image, ImageDraw

from ..anti_detection import load_fonts, image_to_bytes


def create_student_id_image(
    first: str,
    last: str,
    school: str,
    rng: random.Random,
    header_color: tuple = None,
) -> Image.Image:
    """
    创建学生证图像
    
    参数:
        first: 名
        last: 姓
        school: 学校名称
        rng: 种子随机数生成器
        header_color: 页眉颜色（为 None 时随机生成）
    
    返回:
        PIL Image 对象
    """
    # 尺寸微调
    w = 650 + rng.randint(-5, 5)
    h = 400 + rng.randint(-5, 5)
    
    # 背景颜色使用确定性随机微调
    bg_color = tuple(rng.randint(242, 255) for _ in range(3))
    img = Image.new("RGB", (w, h), bg_color)
    draw = ImageDraw.Draw(img)
    
    fonts = load_fonts((26, 20, 18, 14))

    # 页眉颜色
    if header_color is None:
        header_color = (rng.randint(0, 60), rng.randint(0, 60), rng.randint(60, 160))

    draw.rectangle([(0, 0), (w, 80)], fill=header_color)
    draw.text((w // 2, 40), school.upper(), fill=(255, 255, 255), font=fonts["lg"], anchor="mm")

    # 照片占位符
    photo_x, photo_y = 30 + rng.randint(-3, 3), 100 + rng.randint(-3, 3)
    photo_shade = 220 + rng.randint(-10, 10)
    draw.rectangle(
        [(photo_x, photo_y), (photo_x + 130, photo_y + 180)], 
        outline=tuple(100 + rng.randint(-20, 20) for _ in range(3)), 
        width=2, 
        fill=(photo_shade, photo_shade, photo_shade)
    )
    draw.text((photo_x + 65, photo_y + 90), "PHOTO", fill=(150, 150, 150), font=fonts["md"], anchor="mm")

    # 个人信息
    x_info = 190 + rng.randint(-5, 5)
    y = 110
    draw.text((x_info, y), f"{first} {last}", fill=(0, 0, 0), font=fonts["bold_lg"])
    
    y += 40
    draw.text((x_info, y), "Student ID:", fill=(100, 100, 100), font=fonts["sm"])
    draw.text((x_info + 80, y), str(rng.randint(10000000, 99999999)), fill=(0, 0, 0), font=fonts["md"])
    
    y += 30
    draw.text((x_info, y), "Role:", fill=(100, 100, 100), font=fonts["sm"])
    draw.text((x_info + 80, y), "Student", fill=(0, 0, 0), font=fonts["md"])
    
    y += 30
    draw.text((x_info, y), "Valid Thru:", fill=(100, 100, 100), font=fonts["sm"])
    now = datetime.now()
    valid_year = now.year if now.month <= 5 else now.year + 1
    draw.text((x_info + 80, y), f"12/{valid_year}", fill=(0, 0, 0), font=fonts["md"])

    # 条码区域
    barcode_y = 320 + rng.randint(-5, 5)
    draw.rectangle([(0, barcode_y), (w, barcode_y + 60)], fill=(255, 255, 255))
    bar_start = 50 + rng.randint(-10, 10)
    bar_width = rng.randint(6, 10)
    bar_gap = rng.randint(12, 16)
    for i in range(40):
        if rng.random() > 0.3:
            x = bar_start + i * bar_gap
            draw.rectangle([(x, barcode_y + 10), (x + bar_width, barcode_y + 50)], fill=(0, 0, 0))

    return img


def generate_student_id_bytes(img: Image.Image, rng: random.Random) -> bytes:
    """将学生证图像转换为 PNG 字节（含反检测处理）"""
    return image_to_bytes(img, rng, noise_intensity=0.01)
