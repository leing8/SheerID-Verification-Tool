"""
文档生成模块
生成虚拟学术成绩单和学生证

反检测优化：
- EXIF 元数据清理/伪造
- 文档多样性（课程、布局变体）
- 真实感噪声和纹理
- 唯一性增强防止相似度检测
"""

import random
import time
from datetime import datetime
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from anti_detect.fingerprint.base import get_seeded_random


def _clean_exif_metadata(img: Image.Image, rng: random.Random) -> Image.Image:
    """
    清理/伪造 EXIF 元数据
    
    SheerID 可能检测：
    - 创建软件标识（PIL/Pillow vs 真实相机/扫描仪）
    - 时间戳异常
    - 缺少真实设备信息
    """
    # 创建一个干净的副本，去除所有元数据
    clean_img = Image.new(img.mode, img.size)
    clean_img.putdata(list(img.getdata()))
    return clean_img


def _add_realistic_noise(img: Image.Image, rng: random.Random, intensity: float = 0.02) -> Image.Image:
    """
    添加真实感噪声（模拟扫描/拍摄效果）
    
    防止 AI 检测"过于完美"的数字生成文档
    """
    pixels = img.load()
    width, height = img.size
    
    # 添加随机噪点
    for _ in range(int(width * height * intensity)):
        x = rng.randint(0, width - 1)
        y = rng.randint(0, height - 1)
        r, g, b = pixels[x, y]
        # 微小的颜色变化
        delta = rng.randint(-8, 8)
        pixels[x, y] = (
            max(0, min(255, r + delta)),
            max(0, min(255, g + delta)),
            max(0, min(255, b + delta)),
        )
    
    return img


def _add_paper_texture(img: Image.Image, rng: random.Random) -> Image.Image:
    """
    添加纸张纹理效果（模拟真实打印/扫描文档）
    """
    # 轻微模糊模拟扫描效果
    if rng.random() < 0.3:
        img = img.filter(ImageFilter.GaussianBlur(radius=0.3))
    
    # 随机轻微旋转（模拟扫描偏斜）
    if rng.random() < 0.4:
        angle = rng.uniform(-0.5, 0.5)
        img = img.rotate(angle, fillcolor=(255, 255, 255), expand=False)
    
    return img


def _generate_unique_courses(rng: random.Random) -> list:
    """
    生成随机课程列表（防止相似度检测）
    
    每次生成不同的课程组合
    """
    # 课程代码前缀
    prefixes = ["CS", "MATH", "ENG", "PHYS", "CHEM", "BIO", "HIST", "ECON", "PSYCH", "SOC", "ART", "MUS"]
    # 课程编号
    numbers = ["101", "102", "110", "150", "201", "202", "210", "250", "301", "302"]
    
    # 课程名称库
    course_names = {
        "CS": ["Intro to Computer Science", "Data Structures", "Algorithms", "Software Engineering", "Database Systems"],
        "MATH": ["Calculus I", "Calculus II", "Linear Algebra", "Statistics", "Discrete Math"],
        "ENG": ["Academic Writing", "Literature", "Technical Writing", "Creative Writing", "Composition"],
        "PHYS": ["Physics for Engineers", "General Physics", "Mechanics", "Electromagnetism", "Thermodynamics"],
        "CHEM": ["General Chemistry", "Organic Chemistry", "Biochemistry", "Analytical Chemistry"],
        "BIO": ["Biology I", "Cell Biology", "Genetics", "Microbiology", "Ecology"],
        "HIST": ["World History", "US History", "European History", "Ancient Civilizations"],
        "ECON": ["Microeconomics", "Macroeconomics", "International Economics", "Economic Policy"],
        "PSYCH": ["Intro to Psychology", "Developmental Psychology", "Cognitive Psychology"],
        "SOC": ["Intro to Sociology", "Social Theory", "Research Methods"],
        "ART": ["Art History", "Drawing I", "Digital Art", "Sculpture"],
        "MUS": ["Music Theory", "Music History", "Performance"],
    }
    
    # 学分选项
    credits = ["3.0", "4.0"]
    
    # 成绩分布（偏向好成绩）
    grades = ["A", "A", "A-", "A-", "B+", "B+", "B", "B-", "C+"]
    
    # 随机选择 4-6 门课程
    num_courses = rng.randint(4, 6)
    selected_prefixes = rng.sample(prefixes, num_courses)
    
    courses = []
    for prefix in selected_prefixes:
        number = rng.choice(numbers)
        name = rng.choice(course_names.get(prefix, ["General Course"]))
        credit = rng.choice(credits)
        grade = rng.choice(grades)
        courses.append((f"{prefix} {number}", name, credit, grade))
    
    return courses


def _generate_gpa(courses: list, rng: random.Random) -> str:
    """
    根据课程成绩计算 GPA
    """
    grade_points = {"A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7, "C+": 2.3, "C": 2.0}
    
    total_points = 0
    total_credits = 0
    for _, _, credit, grade in courses:
        c = float(credit)
        total_credits += c
        total_points += c * grade_points.get(grade, 3.0)
    
    gpa = total_points / total_credits if total_credits > 0 else 3.5
    # 添加微小随机变化
    gpa = round(gpa + rng.uniform(-0.05, 0.05), 2)
    return f"{min(4.0, max(2.5, gpa)):.2f}"


def get_current_semester() -> str:
    """根据当前日期动态生成学期信息"""
    now = datetime.now()
    year = now.year
    month = now.month

    # 1-5月: 春季学期
    # 6-8月: 夏季学期
    # 9-12月: 秋季学期
    if month <= 5:
        return f"SPRING {year}"
    elif month <= 8:
        return f"SUMMER {year}"
    else:
        return f"FALL {year}"


def generate_transcript(first: str, last: str, school: str, dob: str, seed: str = None) -> bytes:
    """
    生成虚拟学术成绩单（增强反检测版）
    
    参数:
        first: 名
        last: 姓
        school: 学校名称
        dob: 出生日期
        seed: 随机种子（verificationId），用于确定性生成
    """
    rng = get_seeded_random(seed)

    # 文档尺寸微调（防止固定尺寸检测）
    w = 850 + rng.randint(-10, 10)
    h = 1100 + rng.randint(-10, 10)
    
    # 背景色微调（非纯白，模拟纸张）
    bg_shade = rng.randint(250, 255)
    img = Image.new("RGB", (w, h), (bg_shade, bg_shade, bg_shade - rng.randint(0, 3)))
    draw = ImageDraw.Draw(img)

    try:
        font_header = ImageFont.truetype("arial.ttf", 32)
        font_title = ImageFont.truetype("arial.ttf", 24)
        font_text = ImageFont.truetype("arial.ttf", 16)
        font_bold = ImageFont.truetype("arialbd.ttf", 16)
    except Exception as e:
        raise RuntimeError(
            f"无法加载字体文件，请确保系统已安装 Arial 字体: {e}"
        )

    # 1. 页眉（位置微调）
    header_y = 50 + rng.randint(-5, 5)
    draw.text(
        (w // 2, header_y), school.upper(), fill=(0, 0, 0), font=font_header, anchor="mm"
    )
    draw.text(
        (w // 2, header_y + 40),
        "OFFICIAL ACADEMIC TRANSCRIPT",
        fill=(50 + rng.randint(-10, 10), 50 + rng.randint(-10, 10), 50 + rng.randint(-10, 10)),
        font=font_title,
        anchor="mm",
    )
    line_y = header_y + 60
    draw.line([(50, line_y), (w - 50, line_y)], fill=(0, 0, 0), width=2)

    # 2. 学生信息
    y = line_y + 40
    # 使用确定性随机生成学生 ID
    student_id = rng.randint(10000000, 99999999)
    draw.text((50, y), f"Student Name: {first} {last}", fill=(0, 0, 0), font=font_bold)
    draw.text(
        (w - 300, y),
        f"Student ID: {student_id}",
        fill=(0, 0, 0),
        font=font_text,
    )
    y += 30
    draw.text((50, y), f"Date of Birth: {dob}", fill=(0, 0, 0), font=font_text)
    draw.text(
        (w - 300, y),
        f"Date Issued: {time.strftime('%Y-%m-%d')}",
        fill=(0, 0, 0),
        font=font_text,
    )
    y += 40

    # 3. 当前注册状态（背景色随机微调）
    status_bg = (240 + rng.randint(-5, 5), 240 + rng.randint(-5, 5), 240 + rng.randint(-5, 5))
    draw.rectangle([(50, y), (w - 50, y + 40)], fill=status_bg)
    draw.text(
        (w // 2, y + 20),
        f"CURRENT STATUS: ENROLLED ({get_current_semester()})",
        fill=(0, 100 + rng.randint(-20, 20), 0),
        font=font_bold,
        anchor="mm",
    )
    y += 70

    # 4. 课程列表（随机生成）
    courses = _generate_unique_courses(rng)

    # 表头
    draw.text((50, y), "Course Code", font=font_bold, fill=(0, 0, 0))
    draw.text((200, y), "Course Title", font=font_bold, fill=(0, 0, 0))
    draw.text((600, y), "Credits", font=font_bold, fill=(0, 0, 0))
    draw.text((700, y), "Grade", font=font_bold, fill=(0, 0, 0))
    y += 20
    draw.line([(50, y), (w - 50, y)], fill=(0, 0, 0), width=1)
    y += 20

    for code, title, cred, grade in courses:
        draw.text((50, y), code, font=font_text, fill=(0, 0, 0))
        draw.text((200, y), title, font=font_text, fill=(0, 0, 0))
        draw.text((600, y), cred, font=font_text, fill=(0, 0, 0))
        draw.text((700, y), grade, font=font_text, fill=(0, 0, 0))
        y += 30

    y += 20
    draw.line([(50, y), (w - 50, y)], fill=(0, 0, 0), width=1)
    y += 30

    # 5. 汇总信息（GPA 根据课程计算）
    gpa = _generate_gpa(courses, rng)
    draw.text((50, y), f"Cumulative GPA: {gpa}", font=font_bold, fill=(0, 0, 0))
    draw.text((w - 300, y), "Academic Standing: Good", font=font_bold, fill=(0, 0, 0))

    # 6. 水印/页脚
    footer_text = rng.choice([
        "This document is electronically generated and valid without signature.",
        "Official transcript - electronically verified.",
        "This is an official academic record.",
    ])
    draw.text(
        (w // 2, h - 50),
        footer_text,
        fill=(100 + rng.randint(-20, 20), 100 + rng.randint(-20, 20), 100 + rng.randint(-20, 20)),
        font=font_text,
        anchor="mm",
    )

    # 7. 添加真实感效果
    img = _add_realistic_noise(img, rng, intensity=0.015)
    img = _add_paper_texture(img, rng)
    
    # 8. 清理 EXIF 元数据
    img = _clean_exif_metadata(img, rng)

    buf = BytesIO()
    # 使用 PNG 保存时不添加额外元数据
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def generate_student_id(first: str, last: str, school: str, seed: str = None) -> bytes:
    """
    生成虚拟学生证（增强反检测版）
    
    参数:
        first: 名
        last: 姓
        school: 学校名称
        seed: 随机种子（verificationId），用于确定性生成
    """
    rng = get_seeded_random(seed)

    # 尺寸微调
    w = 650 + rng.randint(-5, 5)
    h = 400 + rng.randint(-5, 5)
    
    # 背景颜色使用确定性随机微调
    bg_color = (
        rng.randint(245, 255),
        rng.randint(245, 255),
        rng.randint(242, 252),
    )
    img = Image.new("RGB", (w, h), bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font_lg = ImageFont.truetype("arial.ttf", 26)
        font_md = ImageFont.truetype("arial.ttf", 18)
        font_sm = ImageFont.truetype("arial.ttf", 14)
        font_bold = ImageFont.truetype("arialbd.ttf", 20)
    except Exception as e:
        raise RuntimeError(
            f"无法加载字体文件，请确保系统已安装 Arial 字体: {e}"
        )

    # 根据种子生成一致但多样化的页眉颜色
    header_color = (
        rng.randint(0, 60),
        rng.randint(0, 60),
        rng.randint(60, 160),
    )

    draw.rectangle([(0, 0), (w, 80)], fill=header_color)
    draw.text(
        (w // 2, 40), school.upper(), fill=(255, 255, 255), font=font_lg, anchor="mm"
    )

    # 照片占位符（增加变化）
    photo_x = 30 + rng.randint(-3, 3)
    photo_y = 100 + rng.randint(-3, 3)
    photo_shade = 220 + rng.randint(-10, 10)
    draw.rectangle(
        [(photo_x, photo_y), (photo_x + 130, photo_y + 180)], 
        outline=(100 + rng.randint(-20, 20), 100 + rng.randint(-20, 20), 100 + rng.randint(-20, 20)), 
        width=2, 
        fill=(photo_shade, photo_shade, photo_shade)
    )
    draw.text((photo_x + 65, photo_y + 90), "PHOTO", fill=(150, 150, 150), font=font_md, anchor="mm")

    # 个人信息
    x_info = 190 + rng.randint(-5, 5)
    y = 110
    draw.text((x_info, y), f"{first} {last}", fill=(0, 0, 0), font=font_bold)
    y += 40
    draw.text((x_info, y), "Student ID:", fill=(100, 100, 100), font=font_sm)
    # 使用确定性随机生成学生 ID
    student_id = rng.randint(10000000, 99999999)
    draw.text(
        (x_info + 80, y),
        str(student_id),
        fill=(0, 0, 0),
        font=font_md,
    )
    y += 30
    draw.text((x_info, y), "Role:", fill=(100, 100, 100), font=font_sm)
    draw.text((x_info + 80, y), "Student", fill=(0, 0, 0), font=font_md)
    y += 30
    draw.text((x_info, y), "Valid Thru:", fill=(100, 100, 100), font=font_sm)
    # 有效期：如果当前月份 <= 5月，有效期为当年12月；否则为下一年12月
    now = datetime.now()
    valid_year = now.year if now.month <= 5 else now.year + 1
    draw.text(
        (x_info + 80, y),
        f"12/{valid_year}",
        fill=(0, 0, 0),
        font=font_md,
    )

    # 条码区域（增加变化）
    barcode_y = 320 + rng.randint(-5, 5)
    draw.rectangle([(0, barcode_y), (w, barcode_y + 60)], fill=(255, 255, 255))
    bar_start = 50 + rng.randint(-10, 10)
    bar_width = rng.randint(6, 10)
    bar_gap = rng.randint(12, 16)
    for i in range(40):
        x = bar_start + i * bar_gap
        # 使用确定性随机生成条码
        if rng.random() > 0.3:
            draw.rectangle([(x, barcode_y + 10), (x + bar_width, barcode_y + 50)], fill=(0, 0, 0))

    # 添加真实感效果
    img = _add_realistic_noise(img, rng, intensity=0.01)
    img = _add_paper_texture(img, rng)
    
    # 清理 EXIF 元数据
    img = _clean_exif_metadata(img, rng)

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()

