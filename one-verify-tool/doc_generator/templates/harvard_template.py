"""
Harvard 大学成绩单模板
基于真实 Harvard 成绩单样式，在模板图片上填充学生信息
"""

import random
import time
from datetime import datetime
from pathlib import Path
from typing import List

from PIL import Image, ImageDraw

from .base_template import UniversityTemplate
from ..anti_detection import load_letter_gothic_fonts, image_to_format
from ..base import get_seeded_random


class HarvardTemplate(UniversityTemplate):
    """
    Harvard 大学成绩单模板
    
    使用真实 Harvard 成绩单模板图片，在指定位置填充：
    - 学生地址信息（ISSUED TO 下方）
    - 姓名、ID、打印日期
    - 课程列表
    """
    
    # 模板文件路径（相对于当前文件）
    TEMPLATE_PATH = Path(__file__).parent / "harvard-transcript1.png"
    
    # 模板上的字段坐标
    # 实际模板尺寸: 800x1100 像素
    # 坐标格式: (x, y)，单位为像素
    COORDS = {
        # ISSUED TO: 下方的地址区域（4行）
        # "ISSUED TO:" 标签约在 y=167
        "issued_to_line1": (73, 200),   # 学生姓名
        "issued_to_line2": (73, 218),   # 街道地址
        "issued_to_line3": (73, 236),   # 城市 邮编
        "issued_to_line4": (73, 254),   # 国家
        
        # Name: 右侧（标签 "Name:" 约在 y=388）
        "name": (90, 372),
        # ID: 右侧（标签 "ID:" 约在 y=407）
        "student_id": (90, 387),
        # Printed: 右侧（标签 "Printed:" 约在 y=378，x 约 555）
        "printed": (655, 372),
        
        # 课程区域
        # 表头 "COURSE TITLE CREDITS EARNED LEVEL GRADE" 约在 y=447
        # 课程数据从表头下方开始
        "semester_label": (40, 470),    # 学期标签，如 "Summer Term 2024"
        "courses_start_y": 495,         # 课程数据起始 Y 坐标
        "course_cols": {                # 各列 X 坐标（根据表头位置对齐）
            "course": 130,
            "title": 245,
            "credits": 455,
            "earned": 530,
            "level": 606,
            "grade": 685,
        },
    }
    
    # 课程行高
    COURSE_LINE_HEIGHT = 20
    
    # 美国州和城市数据（用于生成地址）
    US_ADDRESSES = [
        {"city": "Boston", "state": "MA", "zip": "02101"},
        {"city": "Cambridge", "state": "MA", "zip": "02138"},
        {"city": "New York", "state": "NY", "zip": "10001"},
        {"city": "Los Angeles", "state": "CA", "zip": "90001"},
        {"city": "Chicago", "state": "IL", "zip": "60601"},
        {"city": "San Francisco", "state": "CA", "zip": "94102"},
        {"city": "Seattle", "state": "WA", "zip": "98101"},
        {"city": "Denver", "state": "CO", "zip": "80201"},
        {"city": "Austin", "state": "TX", "zip": "78701"},
        {"city": "Miami", "state": "FL", "zip": "33101"},
    ]
    
    # 美国街道名称
    US_STREETS = [
        "Main St", "Oak Ave", "Maple Dr", "Park Rd", "Cedar Ln",
        "Elm St", "Pine Ave", "Washington Blvd", "Lincoln Way", "Madison Ave",
        "Jefferson St", "Adams Rd", "Franklin Dr", "Liberty Ln", "Union St",
    ]
    
    @property
    def university_ids(self) -> List[int]:
        """Harvard 大学 ID"""
        return [1426]  # Harvard University ID in universities.py
    
    def _generate_us_address(self, first: str, last: str, rng: random.Random) -> tuple:
        """
        生成随机美国地址
        
        返回:
            (姓名, 街道地址, 城市州邮编, 国家) 四行元组
        """
        addr = rng.choice(self.US_ADDRESSES)
        street_num = rng.randint(100, 9999)
        street = rng.choice(self.US_STREETS)
        apt = f", Apt {rng.randint(1, 999)}" if rng.random() < 0.3 else ""
        
        return (
            f"{first} {last}",
            f"{street_num} {street}{apt}",
            f"{addr['city']}, {addr['state']} {addr['zip']}",
            "United States"
        )
    
    def _generate_student_id(self, rng: random.Random) -> str:
        """生成 Harvard 格式的学生 ID（如 800123456）"""
        return f"80{rng.randint(1000000, 9999999)}"
    
    def _generate_courses(self, rng: random.Random) -> list:
        """
        生成随机课程列表
        
        返回格式: [(course_code, title, credits, earned, level, grade), ...]
        """
        # 课程代码前缀
        prefixes = ["ECON S-", "GOVT S-", "MATH S-", "HIST S-", "PHYS S-", "CHEM S-", "BIOL S-", "PSYC S-"]
        
        # 课程名称库
        course_titles = {
            "ECON S-": ["Intro to Managerial Finance", "Microeconomics", "Macroeconomics", "International Trade"],
            "GOVT S-": ["American Government", "Political Theory", "International Relations"],
            "MATH S-": ["Calculus I", "Linear Algebra", "Statistics", "Discrete Mathematics"],
            "HIST S-": ["Western Civilization", "American History", "World History"],
            "PHYS S-": ["General Physics", "Mechanics", "Electromagnetism"],
            "CHEM S-": ["General Chemistry", "Organic Chemistry"],
            "BIOL S-": ["Cell Biology", "Genetics", "Microbiology"],
            "PSYC S-": ["Intro to Psychology", "Cognitive Psychology"],
        }
        
        # 成绩分布
        grades = ["A", "A", "A minus", "A minus", "B plus", "B plus", "B", "B minus", "C plus", "E"]
        
        # 生成 2-4 门课程
        num_courses = rng.randint(2, 4)
        selected_prefixes = rng.sample(prefixes, min(num_courses, len(prefixes)))
        
        courses = []
        for prefix in selected_prefixes:
            course_num = rng.randint(100, 299)
            title = rng.choice(course_titles.get(prefix, ["General Course"]))
            credits = "4.00"
            # 部分课程可能 earned 为 0.00（如挂科）
            earned = "4.00" if rng.random() > 0.1 else "0.00"
            level = "UN"  # Undergraduate
            grade = rng.choice(grades)
            
            courses.append((f"{prefix}{course_num}", title, credits, earned, level, grade))
        
        return courses
    
    def _get_current_semester(self, rng: random.Random) -> str:
        """生成学期标签，如 'Summer Term 2024'"""
        now = datetime.now()
        year = now.year
        # 可能是当前年份或前一年
        if rng.random() < 0.3:
            year -= 1
        
        terms = ["Spring Term", "Summer Term", "Fall Term"]
        return f"{rng.choice(terms)} {year}"
    
    def generate_transcript(
        self,
        first: str,
        last: str,
        school: str,
        dob: str,
        seed: str,
        output_format: str = "png"
    ) -> bytes:
        """
        生成 Harvard 成绩单
        
        参数:
            first: 名
            last: 姓
            school: 学校名称（忽略，固定为 Harvard）
            dob: 出生日期（未在成绩单上显示）
            seed: 随机种子（verificationId）
            output_format: 输出格式 ("png", "jpg", "pdf")
        
        返回:
            指定格式的图像字节数据
        """
        rng = get_seeded_random(seed)
        fonts = load_letter_gothic_fonts()
        
        # 加载模板图片
        if not self.TEMPLATE_PATH.exists():
            raise FileNotFoundError(f"Harvard 成绩单模板不存在: {self.TEMPLATE_PATH}")
        
        img = Image.open(self.TEMPLATE_PATH).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # 文本颜色（深灰/黑色，模拟打字机效果）
        text_color = (30, 30, 30)
        
        # 紧凑字符间距绘制函数（模拟打字机紧凑效果）
        def draw_tight_text(pos, text, font, spacing=-1):
            """绘制紧凑间距的文本"""
            x, y = pos
            for char in text:
                draw.text((x, y), char, fill=text_color, font=font)
                bbox = font.getbbox(char)
                char_width = bbox[2] - bbox[0] if bbox else 6
                x += char_width + spacing
        
        # 1. 填充 ISSUED TO 下方的地址
        address_lines = self._generate_us_address(first, last, rng)
        y = self.COORDS["issued_to_line1"][1]
        for line in address_lines:
            draw_tight_text((self.COORDS["issued_to_line1"][0], y), line, fonts["sm_bold"])
            y += 15
        
        # 2. 填充 Name
        draw_tight_text(self.COORDS["name"], f"{first} {last}", fonts["sm_bold"])
        
        # 3. 填充 ID
        student_id = self._generate_student_id(rng)
        draw_tight_text(self.COORDS["student_id"], student_id, fonts["sm_bold"])
        
        # 4. 填充 Printed 日期
        printed_date = time.strftime("%B %d, %Y")  # 如 "February 07, 2026"
        draw_tight_text(self.COORDS["printed"], printed_date, fonts["sm_bold"])
        
        # 5. 填充学期标签
        semester = self._get_current_semester(rng)
        draw_tight_text(self.COORDS["semester_label"], semester, fonts["sm_bold"])
        
        # 6. 填充课程列表
        courses = self._generate_courses(rng)
        y = self.COORDS["courses_start_y"]
        cols = self.COORDS["course_cols"]
        
        for course_code, title, credits, earned, level, grade in courses:
            draw_tight_text((cols["course"], y), course_code, fonts["sm_bold"])
            draw_tight_text((cols["title"], y), title, fonts["sm_bold"])
            draw_tight_text((cols["credits"], y), credits, fonts["sm_bold"])
            draw_tight_text((cols["earned"], y), earned, fonts["sm_bold"])
            draw_tight_text((cols["level"], y), level, fonts["sm_bold"])
            draw_tight_text((cols["grade"], y), grade, fonts["sm_bold"])
            y += self.COURSE_LINE_HEIGHT
        
        # 转换为指定格式并返回
        return image_to_format(img, rng, output_format=output_format)
    
    def generate_student_id(
        self,
        first: str,
        last: str,
        school: str,
        seed: str
    ) -> bytes:
        """
        生成学生证（Harvard 暂用通用模板）
        
        TODO: 实现 Harvard 专用学生证模板
        """
        # 回退到通用模板
        from .us_generic import default_us_template
        return default_us_template.generate_student_id(first, last, school, seed)


# 默认 Harvard 模板实例
harvard_template = HarvardTemplate()
