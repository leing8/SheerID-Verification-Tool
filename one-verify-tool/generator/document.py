"""
文档生成模块 - 生成验证所需的虚拟文档图片

包含:
- generate_transcript: 生成学术成绩单图片
- generate_student_id: 生成学生证图片
- add_scan_effects: 添加扫描效果
- add_document_noise: 添加文档噪点
"""

import sys
import time
import random
from io import BytesIO
from typing import Tuple, Optional

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
except ImportError:
    print("❌ 错误: 需要 Pillow。请安装: pip install Pillow")
    sys.exit(1)


# ============ 文档模板配置 ============

TRANSCRIPT_TEMPLATES = [
    {
        "name": "classic",
        "header_bg": (240, 240, 240),
        "accent_color": (0, 51, 102),
        "border": True,
    },
    {
        "name": "modern",
        "header_bg": (0, 51, 102),
        "accent_color": (0, 102, 204),
        "border": False,
    },
    {
        "name": "minimal",
        "header_bg": (255, 255, 255),
        "accent_color": (50, 50, 50),
        "border": True,
    },
    {
        "name": "academic",
        "header_bg": (128, 0, 0),
        "accent_color": (139, 69, 19),
        "border": True,
    },
]

COURSE_POOLS = {
    "cs": [
        ("CS 101", "Introduction to Computer Science", "3.0"),
        ("CS 201", "Data Structures", "4.0"),
        ("CS 301", "Algorithms", "3.0"),
        ("CS 350", "Operating Systems", "3.0"),
        ("CS 401", "Software Engineering", "3.0"),
        ("CS 450", "Machine Learning", "3.0"),
    ],
    "math": [
        ("MATH 101", "Calculus I", "4.0"),
        ("MATH 102", "Calculus II", "4.0"),
        ("MATH 201", "Linear Algebra", "3.0"),
        ("MATH 301", "Probability & Statistics", "3.0"),
        ("MATH 350", "Discrete Mathematics", "3.0"),
    ],
    "general": [
        ("ENG 101", "English Composition", "3.0"),
        ("ENG 201", "Technical Writing", "3.0"),
        ("PHYS 101", "Physics I", "4.0"),
        ("PHYS 102", "Physics II", "4.0"),
        ("HIST 101", "World History", "3.0"),
        ("PSYCH 101", "Introduction to Psychology", "3.0"),
        ("ECON 101", "Principles of Economics", "3.0"),
        ("CHEM 101", "General Chemistry", "4.0"),
    ],
}

GRADES = ["A", "A", "A-", "A-", "B+", "B+", "B", "B-", "A", "A-"]  # 偏向好成绩
SEMESTERS = ["Fall 2024", "Spring 2025", "Fall 2023", "Spring 2024"]


def _get_random_courses(count: int = 5) -> list:
    """获取随机课程列表"""
    all_courses = []
    for pool in COURSE_POOLS.values():
        all_courses.extend(pool)
    
    selected = random.sample(all_courses, min(count, len(all_courses)))
    
    # 添加成绩
    result = []
    for code, name, credits in selected:
        grade = random.choice(GRADES)
        result.append((code, name, credits, grade))
    
    return result


def _load_font(name: str, size: int):
    """加载字体，失败时返回默认字体"""
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        try:
            # 尝试其他常见字体
            for fallback in ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "FreeSans.ttf"]:
                try:
                    return ImageFont.truetype(fallback, size)
                except OSError:
                    continue
        except:
            pass
        return ImageFont.load_default()


def add_scan_effects(img: Image.Image, intensity: float = 0.3) -> Image.Image:
    """
    添加扫描效果
    
    模拟文档扫描的真实效果：
    - 轻微模糊
    - 扫描线
    - 边缘阴影
    - 轻微倾斜
    
    Args:
        img: 原始图片
        intensity: 效果强度 (0-1)
    
    Returns:
        处理后的图片
    """
    # 1. 轻微倾斜 (随机 -1 到 1 度)
    if random.random() < 0.5:
        angle = random.uniform(-0.5, 0.5) * intensity
        img = img.rotate(angle, fillcolor=(255, 255, 255), expand=False)
    
    # 2. 添加轻微模糊
    if random.random() < 0.3:
        img = img.filter(ImageFilter.GaussianBlur(radius=0.3 * intensity))
    
    # 3. 调整对比度和亮度
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1 + 0.1 * intensity)
    
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1 - 0.05 * intensity)
    
    return img


def add_document_noise(img: Image.Image, amount: float = 0.1) -> Image.Image:
    """
    添加文档噪点
    
    模拟纸张纹理和扫描噪点。
    
    Args:
        img: 原始图片
        amount: 噪点量 (0-1)
    
    Returns:
        处理后的图片
    """
    # 转换为 RGB（如果不是）
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    pixels = img.load()
    width, height = img.size
    
    # 添加随机噪点
    noise_pixels = int(width * height * amount * 0.01)
    for _ in range(noise_pixels):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        
        # 获取当前像素值
        r, g, b = pixels[x, y]
        
        # 轻微调整（模拟纸张纹理）
        delta = random.randint(-15, 15)
        r = max(0, min(255, r + delta))
        g = max(0, min(255, g + delta))
        b = max(0, min(255, b + delta))
        
        pixels[x, y] = (r, g, b)
    
    return img


def add_compression_artifacts(img: Image.Image, quality: int = 85) -> bytes:
    """
    添加 JPEG 压缩伪影后转回 PNG
    
    模拟经过压缩的文档图片。
    
    Args:
        img: 原始图片
        quality: JPEG 质量 (1-100)
    
    Returns:
        PNG 格式的字节数据
    """
    # 先保存为 JPEG（添加压缩伪影）
    jpeg_buf = BytesIO()
    img.save(jpeg_buf, format="JPEG", quality=quality)
    jpeg_buf.seek(0)
    
    # 重新加载
    img = Image.open(jpeg_buf)
    
    # 保存为 PNG
    png_buf = BytesIO()
    img.save(png_buf, format="PNG")
    return png_buf.getvalue()


def enhance_for_ocr(img: Image.Image) -> Image.Image:
    """
    OCR 优化增强
    
    提高文字对比度和清晰度，有利于 SheerID 的 OCR 识别。
    
    增强步骤:
    1. 提高对比度 - 让文字更突出
    2. 锐化处理 - 让边缘更清晰
    3. 亮度调整 - 确保背景足够亮
    
    Args:
        img: 原始图片
    
    Returns:
        OCR 优化后的图片
    """
    # 确保是 RGB 模式
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    # 1. 提高对比度 (1.0 = 原始, > 1.0 = 更高对比度)
    contrast_enhancer = ImageEnhance.Contrast(img)
    img = contrast_enhancer.enhance(1.15)  # 轻微提高对比度
    
    # 2. 锐化处理 (1.0 = 原始, > 1.0 = 更锐利)
    sharpness_enhancer = ImageEnhance.Sharpness(img)
    img = sharpness_enhancer.enhance(1.3)  # 提高锐度
    
    # 3. 轻微提高亮度确保背景白色清晰
    brightness_enhancer = ImageEnhance.Brightness(img)
    img = brightness_enhancer.enhance(1.02)  # 非常轻微
    
    return img


def generate_transcript(
    first: str, last: str, school: str, dob: str,
    template: str = None,
    add_effects: bool = True,
) -> bytes:
    """
    生成虚拟学术成绩单图片
    
    Args:
        first: 名
        last: 姓
        school: 学校名称
        dob: 出生日期
        template: 模板名称 (classic, modern, minimal, academic)
        add_effects: 是否添加扫描效果
    
    Returns:
        bytes: PNG 图片的二进制数据
    """
    # 选择模板
    if template:
        tmpl = next((t for t in TRANSCRIPT_TEMPLATES if t["name"] == template), None)
    if not template or not tmpl:
        tmpl = random.choice(TRANSCRIPT_TEMPLATES)
    
    # 随机调整尺寸（增加变化）
    base_w, base_h = 850, 1100
    w = base_w + random.randint(-20, 20)
    h = base_h + random.randint(-30, 30)
    
    # 创建画布
    bg_variation = random.randint(-5, 5)
    bg_color = (255 + bg_variation, 255 + bg_variation, 253 + bg_variation)
    img = Image.new("RGB", (w, h), bg_color)
    draw = ImageDraw.Draw(img)
    
    # 加载字体
    font_header = _load_font("arialbd.ttf", 28 + random.randint(-2, 2))
    font_title = _load_font("arial.ttf", 22 + random.randint(-1, 1))
    font_text = _load_font("arial.ttf", 15 + random.randint(-1, 1))
    font_bold = _load_font("arialbd.ttf", 15 + random.randint(-1, 1))
    
    # 边框
    if tmpl["border"]:
        border_color = (100, 100, 100)
        draw.rectangle([(20, 20), (w - 20, h - 20)], outline=border_color, width=1)
    
    # 页眉
    header_h = 100
    if tmpl["name"] == "modern":
        draw.rectangle([(0, 0), (w, header_h)], fill=tmpl["header_bg"])
        text_color = (255, 255, 255)
    else:
        text_color = tmpl["accent_color"]
    
    # 学校名称
    y = 40 if tmpl["name"] == "modern" else 50
    draw.text((w // 2, y), school.upper(), fill=text_color, font=font_header, anchor="mm")
    draw.text((w // 2, y + 40), "OFFICIAL ACADEMIC TRANSCRIPT", fill=text_color if tmpl["name"] != "modern" else (220, 220, 220), font=font_title, anchor="mm")
    
    if tmpl["border"] or tmpl["name"] != "modern":
        draw.line([(50, header_h + 20), (w - 50, header_h + 20)], fill=(150, 150, 150), width=1)
    
    # 学生信息
    y = header_h + 50
    student_id = random.randint(10000000, 99999999)
    
    draw.text((50, y), f"Student Name:", fill=(100, 100, 100), font=font_text)
    draw.text((180, y), f"{first} {last}", fill=(0, 0, 0), font=font_bold)
    draw.text((w - 280, y), f"Student ID:", fill=(100, 100, 100), font=font_text)
    draw.text((w - 180, y), str(student_id), fill=(0, 0, 0), font=font_text)
    
    y += 28
    draw.text((50, y), f"Date of Birth:", fill=(100, 100, 100), font=font_text)
    draw.text((180, y), dob, fill=(0, 0, 0), font=font_text)
    draw.text((w - 280, y), f"Issue Date:", fill=(100, 100, 100), font=font_text)
    draw.text((w - 180, y), time.strftime('%Y-%m-%d'), fill=(0, 0, 0), font=font_text)
    
    y += 45
    
    # 入学状态
    semester = random.choice(SEMESTERS)
    status_bg = (235, 245, 235)
    status_text_color = (0, 100, 0)
    draw.rectangle([(50, y), (w - 50, y + 35)], fill=status_bg)
    draw.text((w // 2, y + 17), f"CURRENT STATUS: ENROLLED ({semester.upper()})", 
              fill=status_text_color, font=font_bold, anchor="mm")
    
    y += 60
    
    # 课程列表
    courses = _get_random_courses(random.randint(4, 6))
    
    # 表头
    col_x = [60, 180, 550, 680]
    draw.text((col_x[0], y), "Course", font=font_bold, fill=(0, 0, 0))
    draw.text((col_x[1], y), "Course Title", font=font_bold, fill=(0, 0, 0))
    draw.text((col_x[2], y), "Credits", font=font_bold, fill=(0, 0, 0))
    draw.text((col_x[3], y), "Grade", font=font_bold, fill=(0, 0, 0))
    
    y += 22
    draw.line([(50, y), (w - 50, y)], fill=(180, 180, 180), width=1)
    y += 12
    
    # 课程行
    total_credits = 0
    grade_points = {"A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7, "C+": 2.3, "C": 2.0}
    total_points = 0
    
    for code, title, cred, grade in courses:
        # 交替行背景
        if courses.index((code, title, cred, grade)) % 2 == 0:
            draw.rectangle([(50, y - 3), (w - 50, y + 22)], fill=(250, 250, 250))
        
        draw.text((col_x[0], y), code, font=font_text, fill=(0, 0, 0))
        # 截断过长的标题
        display_title = title[:35] + "..." if len(title) > 35 else title
        draw.text((col_x[1], y), display_title, font=font_text, fill=(0, 0, 0))
        draw.text((col_x[2], y), cred, font=font_text, fill=(0, 0, 0))
        draw.text((col_x[3], y), grade, font=font_text, fill=(0, 0, 0))
        
        total_credits += float(cred)
        total_points += grade_points.get(grade, 3.0) * float(cred)
        y += 28
    
    y += 15
    draw.line([(50, y), (w - 50, y)], fill=(180, 180, 180), width=1)
    y += 20
    
    # GPA
    gpa = total_points / total_credits if total_credits > 0 else 3.5
    gpa = round(gpa, 2)
    
    draw.text((50, y), f"Term Credits: {total_credits:.1f}", font=font_text, fill=(0, 0, 0))
    draw.text((250, y), f"Term GPA: {gpa:.2f}", font=font_bold, fill=(0, 0, 0))
    draw.text((450, y), f"Cumulative GPA: {gpa:.2f}", font=font_bold, fill=tmpl["accent_color"])
    draw.text((w - 200, y), "Standing: Good", font=font_text, fill=(0, 100, 0))
    
    # 页脚
    footer_text = "This document is electronically generated and valid without signature."
    draw.text((w // 2, h - 50), footer_text, fill=(120, 120, 120), font=font_text, anchor="mm")
    
    # 添加效果
    if add_effects:
        if random.random() < 0.6:
            img = add_scan_effects(img, intensity=random.uniform(0.15, 0.35))
        if random.random() < 0.4:
            img = add_document_noise(img, amount=random.uniform(0.05, 0.15))
    
    # 保存（随机选择是否添加轻微压缩伪影）
    if add_effects and random.random() < 0.3:
        return add_compression_artifacts(img, quality=random.randint(80, 95))
    
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_student_id(
    first: str, last: str, school: str,
    add_effects: bool = True,
) -> bytes:
    """
    生成虚拟学生证图片
    
    Args:
        first: 名
        last: 姓
        school: 学校名称
        add_effects: 是否添加扫描效果
    
    Returns:
        bytes: PNG 图片的二进制数据
    """
    # 随机调整尺寸
    w = 650 + random.randint(-20, 20)
    h = 400 + random.randint(-15, 15)
    
    # 随机背景色
    bg_variation = random.randint(0, 10)
    bg_color = (245 + bg_variation, 245 + bg_variation, 250 + bg_variation)
    img = Image.new("RGB", (w, h), bg_color)
    draw = ImageDraw.Draw(img)
    
    # 加载字体
    font_lg = _load_font("arialbd.ttf", 24 + random.randint(-2, 2))
    font_md = _load_font("arial.ttf", 17 + random.randint(-1, 1))
    font_sm = _load_font("arial.ttf", 13 + random.randint(-1, 1))
    font_bold = _load_font("arialbd.ttf", 18 + random.randint(-1, 1))
    
    # 随机头部颜色
    header_colors = [
        (random.randint(0, 40), random.randint(0, 40), random.randint(80, 140)),  # 深蓝
        (random.randint(100, 140), random.randint(0, 30), random.randint(0, 30)),  # 深红
        (random.randint(0, 40), random.randint(60, 100), random.randint(0, 40)),  # 深绿
        (random.randint(60, 100), random.randint(0, 40), random.randint(80, 120)),  # 紫色
    ]
    header_color = random.choice(header_colors)
    
    # 头部
    header_h = 75 + random.randint(-5, 5)
    draw.rectangle([(0, 0), (w, header_h)], fill=header_color)
    draw.text((w // 2, header_h // 2), school.upper(), fill=(255, 255, 255), font=font_lg, anchor="mm")
    
    # 照片区域
    photo_x = 30 + random.randint(-5, 5)
    photo_y = header_h + 20 + random.randint(-5, 5)
    photo_w = 130 + random.randint(-10, 10)
    photo_h = 170 + random.randint(-10, 10)
    
    draw.rectangle(
        [(photo_x, photo_y), (photo_x + photo_w, photo_y + photo_h)],
        outline=(100, 100, 100), width=2, fill=(220, 220, 220)
    )
    draw.text((photo_x + photo_w // 2, photo_y + photo_h // 2), "PHOTO",
              fill=(150, 150, 150), font=font_md, anchor="mm")
    
    # 信息区域
    x_info = photo_x + photo_w + 30
    y = photo_y + 10
    
    # 姓名
    draw.text((x_info, y), f"{first} {last}", fill=(0, 0, 0), font=font_bold)
    y += 45
    
    # 学号
    student_id = random.randint(10000000, 99999999)
    draw.text((x_info, y), "Student ID:", fill=(100, 100, 100), font=font_sm)
    draw.text((x_info + 80, y), str(student_id), fill=(0, 0, 0), font=font_md)
    y += 32
    
    # 身份
    draw.text((x_info, y), "Status:", fill=(100, 100, 100), font=font_sm)
    draw.text((x_info + 80, y), "Student", fill=(0, 0, 0), font=font_md)
    y += 32
    
    # 有效期
    year = int(time.strftime('%Y'))
    valid_month = random.choice(["05", "08", "12"])
    valid_year = year + random.randint(0, 2)
    draw.text((x_info, y), "Valid Thru:", fill=(100, 100, 100), font=font_sm)
    draw.text((x_info + 80, y), f"{valid_month}/{valid_year}", fill=(0, 0, 0), font=font_md)
    
    # 条形码区域
    barcode_y = h - 70
    draw.rectangle([(0, barcode_y), (w, h)], fill=(255, 255, 255))
    
    # 绘制条形码
    bar_start = 40 + random.randint(-10, 10)
    bar_width = random.choice([2, 3])
    bar_gap = random.choice([1, 2])
    
    x = bar_start
    while x < w - 50:
        if random.random() > 0.35:
            bar_h = random.randint(35, 45)
            draw.rectangle([(x, barcode_y + 10), (x + bar_width, barcode_y + 10 + bar_h)], fill=(0, 0, 0))
        x += bar_width + bar_gap
    
    # 添加效果
    if add_effects:
        if random.random() < 0.5:
            img = add_scan_effects(img, intensity=random.uniform(0.2, 0.4))
        if random.random() < 0.3:
            img = add_document_noise(img, amount=random.uniform(0.05, 0.1))
    
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_enrollment_letter(
    first: str, last: str, school: str,
    add_effects: bool = True,
) -> bytes:
    """
    生成入学证明信
    
    Args:
        first: 名
        last: 姓
        school: 学校名称
        add_effects: 是否添加扫描效果
    
    Returns:
        bytes: PNG 图片的二进制数据
    """
    w, h = 850, 1100
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    font_header = _load_font("arialbd.ttf", 28)
    font_title = _load_font("arialbd.ttf", 20)
    font_text = _load_font("arial.ttf", 14)
    font_bold = _load_font("arialbd.ttf", 14)
    
    # 学校抬头
    y = 60
    draw.text((w // 2, y), school.upper(), fill=(0, 51, 102), font=font_header, anchor="mm")
    y += 40
    draw.text((w // 2, y), "Office of the Registrar", fill=(100, 100, 100), font=font_text, anchor="mm")
    y += 60
    draw.line([(50, y), (w - 50, y)], fill=(0, 51, 102), width=2)
    
    # 日期
    y += 40
    draw.text((w - 100, y), time.strftime('%B %d, %Y'), fill=(0, 0, 0), font=font_text, anchor="rm")
    
    # 标题
    y += 60
    draw.text((w // 2, y), "ENROLLMENT VERIFICATION LETTER", fill=(0, 0, 0), font=font_title, anchor="mm")
    
    # 正文
    y += 60
    draw.text((50, y), "To Whom It May Concern:", fill=(0, 0, 0), font=font_bold)
    
    y += 40
    semester = random.choice(SEMESTERS)
    lines = [
        f"This letter confirms that {first} {last} is currently enrolled as a",
        f"full-time student at {school} for the {semester} semester.",
        "",
        f"Student Name: {first} {last}",
        f"Student ID: {random.randint(10000000, 99999999)}",
        f"Enrollment Status: Full-time undergraduate",
        f"Expected Graduation: {random.choice(['May', 'December'])} {random.randint(2025, 2028)}",
        "",
        "This letter is issued upon the student's request for verification purposes.",
        "",
        "If you have any questions regarding this verification, please contact",
        "the Office of the Registrar.",
        "",
        "Sincerely,",
        "",
        "",
        "Office of the Registrar",
        school,
    ]
    
    for line in lines:
        draw.text((50, y), line, fill=(0, 0, 0), font=font_text)
        y += 24
    
    # 页脚
    footer = "This document is electronically generated and is valid without a signature."
    draw.text((w // 2, h - 50), footer, fill=(120, 120, 120), font=font_text, anchor="mm")
    
    if add_effects:
        img = add_scan_effects(img, intensity=random.uniform(0.2, 0.35))

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ============ Harvard 模板相关课程数据 ============

HARVARD_COURSE_POOLS = {
    "business": [
        ("MGMT S-2020", "Managerial Finance", "4.00", "GR"),
        ("MGMT E-5000", "Financial Accounting", "4.00", "GR"),
        ("MGMT E-5010", "Corporate Finance", "4.00", "GR"),
        ("MGMT E-5060", "Investments", "4.00", "GR"),
        ("MGMT E-5075", "Private Equity", "4.00", "GR"),
        ("MGMT S-5500", "Strategic Management", "4.00", "GR"),
    ],
    "economics": [
        ("ECON E-1010", "Principles of Economics", "4.00", "GR"),
        ("ECON E-1020", "Intermediate Microeconomics", "4.00", "GR"),
        ("ECON E-1030", "Intermediate Macroeconomics", "4.00", "GR"),
        ("ECON S-1316", "International Trade", "4.00", "GR"),
    ],
    "computer_science": [
        ("CSCI E-10", "Introduction to Computer Science", "4.00", "GR"),
        ("CSCI E-50", "Intensive Intro to CS", "4.00", "GR"),
        ("CSCI E-124", "Data Structures and Algorithms", "4.00", "GR"),
        ("CSCI S-111", "Computational Thinking", "4.00", "GR"),
    ],
    "mathematics": [
        ("MATH E-21A", "Multivariable Calculus", "4.00", "GR"),
        ("MATH E-21B", "Linear Algebra", "4.00", "GR"),
        ("MATH E-23A", "Linear Algebra and Real Analysis", "4.00", "GR"),
        ("STAT E-100", "Probability and Statistics", "4.00", "GR"),
    ],
}

def _get_current_sessions() -> list:
    """生成当前学年的 Session 列表"""
    from datetime import datetime
    now = datetime.now()
    year = now.year
    
    # 根据当前月份确定学年
    if now.month >= 8:  # 8月后是新学年
        academic_year = year
    else:
        academic_year = year - 1
    
    return [
        f"Fall Semester {academic_year}",
        f"Spring Semester {academic_year + 1}",
        f"Summer Intensive Session I {academic_year + 1}",
        f"Summer Intensive Session II {academic_year + 1}",
        f"January Term {academic_year + 1}",
    ]

# 使用动态生成的 Session 列表
HARVARD_SESSIONS = _get_current_sessions()

HARVARD_GRADES = ["A", "A", "A minus", "A minus", "B plus", "B plus", "B", "A", "A minus"]


def _get_harvard_courses(count: int = 1) -> list:
    """获取随机 Harvard 课程列表"""
    all_courses = []
    for pool in HARVARD_COURSE_POOLS.values():
        all_courses.extend(pool)
    
    selected = random.sample(all_courses, min(count, len(all_courses)))
    
    result = []
    for code, name, credits, level in selected:
        grade = random.choice(HARVARD_GRADES)
        result.append({
            "course": code,
            "title": name,
            "credits": credits,
            "earned": credits,
            "level": level,
            "grade": grade,
        })
    
    return result


def _generate_student_address() -> list:
    """生成随机学生地址（多行）"""
    street_types = ["St", "Ave", "Blvd", "Dr", "Ln", "Way", "Ct", "Rd"]
    street_names = ["Oak", "Main", "Park", "Cedar", "Maple", "Pine", "Washington", "Lake", "Hill", "Cherry"]
    
    cities_states = [
        ("Cambridge", "MA", "02138"),
        ("Boston", "MA", "02115"),
        ("Somerville", "MA", "02143"),
        ("Brookline", "MA", "02445"),
        ("Newton", "MA", "02458"),
        ("Bristol", "BS1", "3NH"),
        ("Los Angeles", "CA", "90024"),
        ("New York", "NY", "10001"),
    ]
    
    apt_types = ["Flat", "Apt", "Unit", "Room", "Suite"]
    apt_designators = ["A", "B", "C", "D", "1", "2", "3", "101", "201", "301", "BG01"]
    
    lines = []
    
    if random.random() < 0.5:
        apt_type = random.choice(apt_types)
        apt_num = random.choice(apt_designators)
        if random.random() < 0.3:
            lines.append(f"{apt_type} {apt_num} Room {random.choice(['A', 'B', 'C', 'D'])}")
        else:
            lines.append(f"{apt_type} {apt_num}")
    
    street_num = random.randint(1, 999)
    street_name = random.choice(street_names)
    street_type = random.choice(street_types)
    
    if random.random() < 0.3:
        extra = random.choice(["Court", "Lane", "Place", "Square"])
        lines.append(f"{street_name} {extra}, {random.choice(street_names)} Street")
    else:
        lines.append(f"{street_num} {street_name} {street_type}")
    
    city, state, zip_code = random.choice(cities_states)
    lines.append(f"{city} {state} {zip_code}")
    
    if random.random() < 0.3:
        countries = ["United States", "United Kingdom", "Canada"]
        lines.append(random.choice(countries))
    
    return lines


def generate_harvard_transcript(
    first: str, 
    last: str, 
    school: str, 
    dob: str,
    student_id: str = None,
    add_effects: bool = True,
) -> bytes:
    """
    使用 Harvard 模板生成成绩单图片
    
    基于 Harvard-Template.png 模板，在指定位置填充学生信息。
    
    Args:
        first: 名
        last: 姓
        school: 学校名称（仅用于兼容，实际使用 Harvard）
        dob: 出生日期
        student_id: 可选的学生 ID（格式 @XXXXXXXX）
        add_effects: 是否添加扫描效果
    
    Returns:
        bytes: PNG 图片的二进制数据
    """
    from pathlib import Path
    
    # 加载模板
    template_path = Path(__file__).parent / "Harvard-Template.png"
    if not template_path.exists():
        raise FileNotFoundError(f"Harvard template not found: {template_path}")
    
    img = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    # 图片尺寸 (800 x 673)
    w, h = img.size
    
    # 加载字体
    # 字体: Courier New, 字重: Regular, 字号: 12pt
    font_regular = _load_font("cour.ttf", 12)       # ← Courier New Regular 12pt
    font_small = _load_font("cour.ttf", 12)         # ← 课程表也用 12pt
    
    # ============================================================
    # 位置调整说明:
    # - 模板尺寸: 800 x 673 像素
    # - x 坐标: 左边=0, 右边=800
    # - y 坐标: 上边=0, 下边=673
    # - 增大 x 值 = 向右移动
    # - 增大 y 值 = 向下移动
    # - 字体: font_regular=12px, font_small=11px
    # ============================================================
    
    # 文本颜色（黑色）
    text_color = (0, 0, 0)
    
    # ============ 1. ISSUED TO 区域 - 学生姓名和地址 ============
    # 位置: 左上角 "ISSUED TO:" 标签下方
    # 调整: 修改 issued_to_x/issued_to_y 改变起始位置
    #       修改 line_height 改变行间距
    issued_to_x = 75      # ← 水平位置 (向右移动增大此值)
    issued_to_y = 200     # ← 垂直位置 (向下移动增大此值)
    line_height = 15      # ← 地址行间距
    
    full_name = f"{first} {last}"
    draw.text((issued_to_x, issued_to_y), full_name, fill=text_color, font=font_regular)
    
    # 地址行 (自动生成多行地址)
    address_lines = _generate_student_address()
    y = issued_to_y + line_height
    for line in address_lines:
        draw.text((issued_to_x, y), line, fill=text_color, font=font_regular)
        y += line_height
    
    # ============ 2. Name 字段 ============
    # 位置: 在模板 "Name:" 标签后面
    # 调整: 修改 name_x/name_y 移动姓名位置
    name_x = 90          # ← 水平位置 (标签结束约 x=72)
    name_y = 363         # ← 垂直位置
    draw.text((name_x, name_y), full_name, fill=text_color, font=font_regular)
    
    # ============ 3. ID 字段 ============
    # 位置: 在模板 "ID:" 标签后面
    # 格式: @XXXXXXXX (8位数字)
    # 调整: 修改 id_x/id_y 移动ID位置
    id_x = 90             # ← 水平位置 (标签结束约 x=47)
    id_y = 378            # ← 垂直位置
    if not student_id:
        student_id = f"@{random.randint(10000000, 99999999):08d}"
    draw.text((id_x, id_y), student_id, fill=text_color, font=font_regular)
    
    # ============ 4. Printed 日期 ============
    # 位置: 在模板 "Printed:" 标签后面
    # 格式: Month DD, YYYY
    # 重要: SheerID 要求日期必须在 90 天内！
    # 调整: 修改 printed_x/printed_y 移动日期位置
    printed_x = 655       # ← 水平位置 (标签结束约 x=602)
    printed_y = 363       # ← 垂直位置
    
    # 生成 90 天内的随机日期（推荐 1-30 天内）
    from datetime import datetime, timedelta
    days_ago = random.randint(1, 30)  # 1-30 天前（确保在 90 天内）
    print_date = datetime.now() - timedelta(days=days_ago)
    months = ["January", "February", "March", "April", "May", "June", 
              "July", "August", "September", "October", "November", "December"]
    printed_date = f"{months[print_date.month - 1]} {print_date.day}, {print_date.year}"
    draw.text((printed_x, printed_y), printed_date, fill=text_color, font=font_regular)
    
    # ============ 5. 课程数据 ============
    # 位置: 课程表区域
    # 调整: 修改 course_start_y 改变整体垂直位置
    #       修改 col_* 改变各列水平位置
    course_start_y = 455  # ← 课程区域起始 y 位置
    
    # 学期/Session 标题 (例如 "Summer Intensive Session I 2024")
    session_x = 40        # ← Session 标题 x 位置
    session = random.choice(HARVARD_SESSIONS)
    draw.text((session_x, course_start_y), session, fill=text_color, font=font_small)
    
    # 课程表列位置
    col_course = 130       # ← COURSE 列 (课程代码)
    col_title = 245       # ← TITLE 列 (课程名称)
    col_credits = 455     # ← CREDITS 列 (学分)
    col_earned = 530      # ← EARNED 列 (获得学分)
    col_level = 605       # ← LEVEL 列 (级别)
    col_grade = 685       # ← GRADE 列 (成绩)
    row_height = 18       # ← 课程行间距
    
    courses = _get_harvard_courses(count=random.randint(1, 2))
    y = course_start_y + 22  # ← 第一行课程的 y 位置
    
    for course in courses:
        draw.text((col_course, y), course["course"], fill=text_color, font=font_small)
        draw.text((col_title, y), course["title"], fill=text_color, font=font_small)
        draw.text((col_credits, y), course["credits"], fill=text_color, font=font_small)
        draw.text((col_earned, y), course["earned"], fill=text_color, font=font_small)
        draw.text((col_level, y), course["level"], fill=text_color, font=font_small)
        draw.text((col_grade, y), course["grade"], fill=text_color, font=font_small)
        y += row_height
    
    # ============ 添加效果（可选）============
    
    # 首先应用 OCR 增强，提高文字识别度
    img = enhance_for_ocr(img)
    
    if add_effects:
        # 注意：扫描效果和噪点可能降低 OCR 识别率
        # 如果 SheerID 拒绝，尝试设置 add_effects=False
        if random.random() < 0.3:  # 降低扫描效果概率
            img = add_scan_effects(img, intensity=random.uniform(0.05, 0.15))  # 降低强度
        # 暂时禁用噪点以提高 OCR 识别率
        # if random.random() < 0.3:
        #     img = add_document_noise(img, amount=random.uniform(0.02, 0.08))
    
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
