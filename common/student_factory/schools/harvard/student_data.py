"""
哈佛大学专属学生数据

定义哈佛3种文档（学生证/成绩单/发票）所需的完整学生数据字段，
并提供基于 verificationId 的确定性数据生成函数。
"""

import hashlib
import random
from dataclasses import dataclass
from typing import List, Tuple


# ============ 姓名数据 ============

FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William",
    "David", "Richard", "Joseph", "Thomas", "Christopher",
    "Charles", "Daniel", "Matthew", "Anthony", "Mark",
    "Donald", "Steven", "Andrew", "Paul", "Joshua",
    "Kenneth", "Kevin", "Brian", "George", "Timothy",
    "Ronald", "Edward", "Jason", "Jeffrey", "Ryan",
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara",
    "Elizabeth", "Susan", "Jessica", "Sarah", "Karen",
    "Lisa", "Nancy", "Betty", "Margaret", "Sandra",
    "Ashley", "Kimberly", "Emily", "Donna", "Michelle",
    "Dorothy", "Carol", "Amanda", "Melissa", "Deborah",
    "Stephanie", "Rebecca", "Sharon", "Laura", "Emma",
    "Olivia", "Ava", "Isabella", "Sophia", "Mia",
    "Charlotte", "Amelia",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones",
    "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris",
    "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
    "Walker", "Young", "Allen", "King", "Wright",
    "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall",
    "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
    "Turner", "Phillips", "Evans", "Parker", "Edwards",
]


# ============ 哈佛专业与学院映射 ============

# 专业 → 学院缩写（用于学生证 GSAS/SEAS/FAS 标签）
PROGRAM_SCHOOL_CODE = {
    "Computer Science (A.B.)":  "FAS",   # Faculty of Arts & Sciences (undergrad)
    "Computer Science (S.M.)":  "GSAS",  # Graduate School of Arts & Sciences
    "Computer Science (Ph.D.)": "GSAS",
    "Data Science (S.M.)":      "GSAS",
}

# 专业 → 课程列表 (course_code, title, credits, grade, level)
PROGRAM_COURSES = {
    "Computer Science (A.B.)": [
        ("CS 50",    "Introduction to Computer Science I",  4, "A",  "U"),
        ("MATH 21A", "Multivariable Calculus",               4, "A-", "U"),
        ("CS 124",   "Data Structures & Algorithms",         4, "A",  "U"),
        ("STAT 110", "Probability",                          4, "A",  "U"),
        ("CS 181",   "Machine Learning",                     4, "A-", "U"),
    ],
    "Computer Science (S.M.)": [
        ("CS 205",   "Computing Foundations for Comp Sci",  4, "A",  "G"),
        ("CS 249R",  "Special Topics in Edge Computing",    4, "A",  "G"),
        ("CS 290",   "Research Methods in Computer Science",4, "A-", "G"),
        ("STAT 195", "Statistical Computing",               4, "A",  "G"),
        ("CS 280",   "Graduate Seminar",                    2, "CR", "G"),
    ],
    "Computer Science (Ph.D.)": [
        ("CS 300",   "Research Seminar in CS",              2, "CR", "G"),
        ("CS 330",   "Advanced Topics in Algorithms",       4, "A",  "G"),
        ("CS 391",   "Dissertation Research",               8, "S",  "G"),
        ("CS 287",   "Advanced Robotics",                   4, "A-", "G"),
        ("STAT 211", "Statistical Inference I",             4, "A",  "G"),
    ],
    "Data Science (S.M.)": [
        ("STAT 110", "Probability",                         4, "A",  "G"),
        ("CS 109B",  "Advanced Data Science",               4, "A",  "G"),
        ("STAT 149", "Generalized Linear Models",           4, "A-", "G"),
        ("CS 205L",  "Continuous Math for Data Science",    4, "A",  "G"),
        ("APMTH 207","Advanced Scientific Computing",       4, "A",  "G"),
    ],
}

# 哈佛学费（按学期，美元）
TUITION_PER_TERM = {
    "Computer Science (A.B.)":  23499,   # FAS undergrad (half-year)
    "Computer Science (S.M.)":  29937,   # GSAS
    "Computer Science (Ph.D.)": 14968,   # GSAS (stipend-based)
    "Data Science (S.M.)":      29937,
}

# 附加费用
FEE_HEALTH      = 1682
FEE_ACTIVITY    = 246
FEE_FACILITIES  = 304


@dataclass
class HarvardStudentData:
    """
    哈佛大学3种文档所需的完整学生数据。

    学生证用到：first_name, last_name, student_id, program, school_code, valid_thru
    成绩单用到：first_name, last_name, student_id, printed_date, courses, gpa
    发票用到：  first_name, last_name, student_id, invoice_number, tuition, term, fees
    """
    # === 通用字段（所有文档共用）===
    first_name: str
    last_name:  str
    email:      str
    birth_date: str          # YYYY-MM-DD

    # === 哈佛专属字段 ===
    student_id:     str      # 8位学号
    program:        str      # 专业名
    school_code:    str      # FAS / GSAS
    enrollment_year: int     # 入学年份
    gpa:            str      # 如 "3.85"
    term:           str      # 如 "Spring 2026"
    invoice_number: str      # 如 "INV-20260125-12345678"

    # 课程列表：[(code, title, credits, grade, level), ...]
    courses: List[Tuple[str, str, int, str, str]]

    # 学费明细
    tuition_amount: int      # 当期学费（不含附加费）


def _seeded_random(verification_id: str) -> random.Random:
    seed = int(hashlib.sha256(verification_id.encode()).hexdigest(), 16) % (2 ** 32)
    return random.Random(seed)


def build(verification_id: str, program: str) -> HarvardStudentData:
    """
    基于 verificationId 确定性生成 HarvardStudentData。
    同一 vid + program → 完全相同的学生数据。
    """
    rng = _seeded_random(verification_id)

    first = rng.choice(FIRST_NAMES)
    last  = rng.choice(LAST_NAMES)

    # 邮箱生成（三种格式之一）
    patterns = [
        f"{first[0].lower()}{last.lower()}{rng.randint(100,999)}",
        f"{first.lower()}.{last.lower()}{rng.randint(10,99)}",
        f"{last.lower()}{first[0].lower()}{rng.randint(100,999)}",
    ]
    email = f"{rng.choice(patterns)}@g.harvard.edu"

    # 出生日期（适合18-26岁在校生）
    birth_year  = rng.randint(1998, 2006)
    birth_month = rng.randint(1, 12)
    birth_day   = rng.randint(1, 28)
    birth_date  = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"

    # 学号（8位，哈佛学号范围参考）
    student_id = str(rng.randint(10000000, 99999999))

    # GPA（3.50-3.99）
    gpa = f"{3.50 + rng.random() * 0.49:.2f}"

    # 入学年份（2021-2024）
    enrollment_year = rng.randint(2021, 2024)

    # 当前学期
    import time
    month = int(time.strftime("%m"))
    year  = int(time.strftime("%Y"))
    term  = f"Spring {year}" if month <= 6 else f"Fall {year}"

    # 发票号
    import time as _t
    invoice_number = f"INV-{_t.strftime('%Y%m%d')}-{student_id}"

    school_code   = PROGRAM_SCHOOL_CODE.get(program, "GSAS")
    courses       = PROGRAM_COURSES.get(program, PROGRAM_COURSES["Computer Science (A.B.)"])
    tuition_amount = TUITION_PER_TERM.get(program, 29937)

    return HarvardStudentData(
        first_name=first,
        last_name=last,
        email=email,
        birth_date=birth_date,
        student_id=student_id,
        program=program,
        school_code=school_code,
        enrollment_year=enrollment_year,
        gpa=gpa,
        term=term,
        invoice_number=invoice_number,
        courses=courses,
        tuition_amount=tuition_amount,
    )
