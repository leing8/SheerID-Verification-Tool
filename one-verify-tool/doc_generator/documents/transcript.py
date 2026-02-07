"""
成绩单生成模块
提供成绩单相关的公共工具函数
"""

import random
import time
from datetime import datetime

from PIL import Image, ImageDraw

from ..anti_detection import load_fonts, image_to_bytes


def generate_unique_courses(rng: random.Random) -> list:
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
    
    return [
        (f"{prefix} {rng.choice(numbers)}", 
         rng.choice(course_names.get(prefix, ["General Course"])),
         rng.choice(credits),
         rng.choice(grades))
        for prefix in selected_prefixes
    ]


def calculate_gpa(courses: list, rng: random.Random) -> str:
    """根据课程成绩计算 GPA"""
    grade_points = {"A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7, "C+": 2.3, "C": 2.0}
    
    total_points = sum(float(c) * grade_points.get(g, 3.0) for _, _, c, g in courses)
    total_credits = sum(float(c) for _, _, c, _ in courses)
    
    gpa = (total_points / total_credits if total_credits > 0 else 3.5) + rng.uniform(-0.05, 0.05)
    return f"{min(4.0, max(2.5, gpa)):.2f}"


def get_current_semester() -> str:
    """根据当前日期动态生成学期信息"""
    now = datetime.now()
    year, month = now.year, now.month
    
    if month <= 5:
        return f"SPRING {year}"
    elif month <= 8:
        return f"SUMMER {year}"
    return f"FALL {year}"


def create_transcript_image(
    first: str,
    last: str,
    school: str,
    dob: str,
    rng: random.Random,
    header_color: tuple = (0, 0, 0),
    accent_color: tuple = (0, 100, 0),
) -> Image.Image:
    """
    创建成绩单图像
    
    参数:
        first: 名
        last: 姓
        school: 学校名称
        dob: 出生日期
        rng: 种子随机数生成器
        header_color: 页眉文字颜色
        accent_color: 强调色（用于状态文字）
    
    返回:
        PIL Image 对象
    """
    # 文档尺寸微调（防止固定尺寸检测）
    w = 850 + rng.randint(-10, 10)
    h = 1100 + rng.randint(-10, 10)
    
    # 背景色微调（非纯白，模拟纸张）
    bg_shade = rng.randint(250, 255)
    img = Image.new("RGB", (w, h), (bg_shade, bg_shade, bg_shade - rng.randint(0, 3)))
    draw = ImageDraw.Draw(img)
    
    fonts = load_fonts((32, 24, 16))

    # 1. 页眉（位置微调）
    header_y = 50 + rng.randint(-5, 5)
    draw.text((w // 2, header_y), school.upper(), fill=header_color, font=fonts["header"], anchor="mm")
    draw.text(
        (w // 2, header_y + 40),
        "OFFICIAL ACADEMIC TRANSCRIPT",
        fill=tuple(50 + rng.randint(-10, 10) for _ in range(3)),
        font=fonts["title"],
        anchor="mm",
    )
    line_y = header_y + 60
    draw.line([(50, line_y), (w - 50, line_y)], fill=(0, 0, 0), width=2)

    # 2. 学生信息
    y = line_y + 40
    student_id = rng.randint(10000000, 99999999)
    draw.text((50, y), f"Student Name: {first} {last}", fill=(0, 0, 0), font=fonts["bold"])
    draw.text((w - 300, y), f"Student ID: {student_id}", fill=(0, 0, 0), font=fonts["text"])
    y += 30
    draw.text((50, y), f"Date of Birth: {dob}", fill=(0, 0, 0), font=fonts["text"])
    draw.text((w - 300, y), f"Date Issued: {time.strftime('%Y-%m-%d')}", fill=(0, 0, 0), font=fonts["text"])
    y += 40

    # 3. 当前注册状态
    status_bg = tuple(240 + rng.randint(-5, 5) for _ in range(3))
    draw.rectangle([(50, y), (w - 50, y + 40)], fill=status_bg)
    status_color = tuple(max(0, min(255, c + rng.randint(-20, 20))) for c in accent_color)
    draw.text(
        (w // 2, y + 20),
        f"CURRENT STATUS: ENROLLED ({get_current_semester()})",
        fill=status_color,
        font=fonts["bold"],
        anchor="mm",
    )
    y += 70

    # 4. 课程列表（随机生成）
    courses = generate_unique_courses(rng)

    # 表头
    for text, x in [("Course Code", 50), ("Course Title", 200), ("Credits", 600), ("Grade", 700)]:
        draw.text((x, y), text, font=fonts["bold"], fill=(0, 0, 0))
    y += 20
    draw.line([(50, y), (w - 50, y)], fill=(0, 0, 0), width=1)
    y += 20

    for code, title, cred, grade in courses:
        for text, x in [(code, 50), (title, 200), (cred, 600), (grade, 700)]:
            draw.text((x, y), text, font=fonts["text"], fill=(0, 0, 0))
        y += 30

    y += 20
    draw.line([(50, y), (w - 50, y)], fill=(0, 0, 0), width=1)
    y += 30

    # 5. 汇总信息
    gpa = calculate_gpa(courses, rng)
    draw.text((50, y), f"Cumulative GPA: {gpa}", font=fonts["bold"], fill=(0, 0, 0))
    draw.text((w - 300, y), "Academic Standing: Good", font=fonts["bold"], fill=(0, 0, 0))

    # 6. 水印/页脚
    footer_text = rng.choice([
        "This document is electronically generated and valid without signature.",
        "Official transcript - electronically verified.",
        "This is an official academic record.",
    ])
    draw.text(
        (w // 2, h - 50),
        footer_text,
        fill=tuple(100 + rng.randint(-20, 20) for _ in range(3)),
        font=fonts["text"],
        anchor="mm",
    )

    return img


def generate_transcript_bytes(img: Image.Image, rng: random.Random) -> bytes:
    """将成绩单图像转换为 PNG 字节（含反检测处理）"""
    return image_to_bytes(img, rng, noise_intensity=0.015)
