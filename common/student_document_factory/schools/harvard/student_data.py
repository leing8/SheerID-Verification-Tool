"""
哈佛大学专属学生数据

定义哈佛3种文档（学生证/成绩单/发票）所需的完整学生数据字段，
并提供基于 verificationId 的确定性数据生成函数。

包含：姓名、邮箱、出生日期、学号、专业、学院、GPA、学期、课程、
学费、附加费、地址。

学费、费用、课程代码均基于 2025-2026 学年哈佛官方公布数据。
"""

import hashlib
import random
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple


# ============ 姓名数据（丰富池，提高多样性）============

FIRST_NAMES = [
    # 男性常见名
    "James", "John", "Robert", "Michael", "William",
    "David", "Richard", "Joseph", "Thomas", "Christopher",
    "Charles", "Daniel", "Matthew", "Anthony", "Mark",
    "Steven", "Andrew", "Paul", "Joshua", "Kenneth",
    "Kevin", "Brian", "George", "Timothy", "Ronald",
    "Edward", "Jason", "Jeffrey", "Ryan", "Jacob",
    "Ethan", "Alexander", "Benjamin", "Samuel", "Nathan",
    "Henry", "Nicholas", "Dylan", "Logan", "Owen",
    # 女性常见名
    "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth",
    "Susan", "Jessica", "Sarah", "Karen", "Lisa",
    "Nancy", "Margaret", "Sandra", "Ashley", "Emily",
    "Donna", "Michelle", "Stephanie", "Rebecca", "Laura",
    "Emma", "Olivia", "Ava", "Isabella", "Sophia",
    "Mia", "Charlotte", "Amelia", "Harper", "Evelyn",
    "Abigail", "Ella", "Chloe", "Grace", "Victoria",
    "Hannah", "Natalie", "Lily", "Zoe", "Audrey",
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
    "Collins", "Stewart", "Morris", "Murphy", "Cook",
    "Rogers", "Reed", "Morgan", "Bell", "Bailey",
]


# ============ 哈佛专业与学院映射 ============

# 专业 → 学院缩写（用于学生证 GSAS/FAS 标签）
PROGRAM_SCHOOL_CODE = {
    "Computer Science (A.B.)":  "FAS",   # Faculty of Arts & Sciences (undergrad)
    "Computer Science (S.M.)":  "GSAS",  # Graduate School of Arts & Sciences
    "Computer Science (Ph.D.)": "GSAS",
    "Data Science (S.M.)":      "GSAS",
}

# 专业 → 课程池 (course_code, title, credits, grade, level)
# 课程代码使用哈佛官方 COMPSCI / MATH / STAT / APMTH 前缀
# 来源：Harvard SEAS 课程目录、FAS 注册处、my.harvard 课程搜索
# build() 会从中随机选取 8-12 门，模拟真实学期修课记录
PROGRAM_COURSES = {
    "Computer Science (A.B.)": [
        # 核心必修
        ("COMPSCI 50",  "Introduction to Computer Science I",     4, "A",  "U"),
        ("COMPSCI 61",  "Systems Programming and Machine Org",    4, "A-", "U"),
        ("COMPSCI 121", "Introduction to Formal Languages",       4, "A",  "U"),
        ("COMPSCI 124", "Data Structures & Algorithms",           4, "A",  "U"),
        ("COMPSCI 134", "Operating Systems",                      4, "B+", "U"),
        ("COMPSCI 136", "Economics and Computation",              4, "A-", "U"),
        ("COMPSCI 141", "Computing Hardware",                     4, "B+", "U"),
        ("COMPSCI 152", "Programming Languages",                  4, "A",  "U"),
        ("COMPSCI 161", "Operating Systems",                      4, "A-", "U"),
        ("COMPSCI 171", "Visualization",                          4, "A",  "U"),
        ("COMPSCI 181", "Machine Learning",                       4, "A-", "U"),
        ("COMPSCI 182", "Artificial Intelligence",                4, "A",  "U"),
        # 跨系必修（MATH / STAT）
        ("MATH 21A",    "Multivariable Calculus",                 4, "A-", "U"),
        ("MATH 21B",    "Linear Algebra and Differential Eqs",    4, "B+", "U"),
        ("STAT 110",    "Probability",                            4, "A",  "U"),
    ],
    "Computer Science (S.M.)": [
        # 研究生核心
        ("COMPSCI 205", "Computing Foundations for Comp Sci",     4, "A",  "G"),
        ("COMPSCI 207", "Systems Development for Comp Research",  4, "A-", "G"),
        ("COMPSCI 223", "Probabilistic Analysis and Algorithms",  4, "A",  "G"),
        ("COMPSCI 224", "Advanced Algorithms",                    4, "B+", "G"),
        ("COMPSCI 226", "Distributed Computing",                  4, "A",  "G"),
        ("COMPSCI 228", "Computational Learning Theory",          4, "A-", "G"),
        ("COMPSCI 243", "Advanced Computer Networks",             4, "A",  "G"),
        ("COMPSCI 246", "Advanced Computer Architecture",         4, "B+", "G"),
        ("COMPSCI 249R", "Special Topics in Edge Computing",      4, "A-", "G"),
        ("COMPSCI 261", "Research Topics in Operating Systems",   4, "A",  "G"),
        ("COMPSCI 265", "Big Data Systems",                       4, "A-", "G"),
        ("COMPSCI 280", "Graduate Seminar",                       2, "CR", "G"),
        ("COMPSCI 290", "Research Methods in Computer Science",   4, "A",  "G"),
        # 跨系选修（STAT / APMTH）
        ("STAT 195",    "Statistical Computing",                  4, "B+", "G"),
        ("APMTH 207",   "Advanced Scientific Computing",          4, "A",  "G"),
    ],
    "Computer Science (Ph.D.)": [
        # 博士核心 + 研讨
        ("COMPSCI 223", "Probabilistic Analysis and Algorithms",  4, "A",  "G"),
        ("COMPSCI 224", "Advanced Algorithms",                    4, "A",  "G"),
        ("COMPSCI 226", "Distributed Computing",                  4, "A-", "G"),
        ("COMPSCI 228", "Computational Learning Theory",          4, "A",  "G"),
        ("COMPSCI 252", "Advanced Programming Language Design",   4, "A-", "G"),
        ("COMPSCI 260", "Advanced Topics in Comp Architecture",   4, "B+", "G"),
        ("COMPSCI 263", "Systems Security",                       4, "A",  "G"),
        ("COMPSCI 271", "Topics in Machine Learning",             4, "A-", "G"),
        ("COMPSCI 281", "Advanced Machine Learning",              4, "A",  "G"),
        ("COMPSCI 287", "Advanced Robotics",                      4, "A-", "G"),
        ("COMPSCI 300", "Research Seminar in CS",                 2, "CR", "G"),
        ("COMPSCI 330", "Advanced Topics in Algorithms",          4, "A",  "G"),
        ("COMPSCI 391", "Dissertation Research",                  8, "S",  "G"),
        # 跨系（STAT / MATH）
        ("STAT 211",    "Statistical Inference I",                4, "A",  "G"),
        ("MATH 232BR",  "Algebraic Geometry II",                  4, "A-", "G"),
    ],
    "Data Science (S.M.)": [
        # 核心 + 统计
        ("COMPSCI 109A", "Data Science 1: Intro to Data Science", 4, "A",  "G"),
        ("COMPSCI 109B", "Data Science 2: Advanced Topics",       4, "A-", "G"),
        ("COMPSCI 205",  "Computing Foundations for Comp Sci",    4, "A",  "G"),
        ("COMPSCI 207",  "Systems Development for Comp Research", 4, "B+", "G"),
        ("COMPSCI 281",  "Advanced Machine Learning",             4, "A",  "G"),
        ("STAT 110",     "Probability",                           4, "A",  "G"),
        ("STAT 111",     "Introduction to Statistical Inference", 4, "A-", "G"),
        ("STAT 139",     "Linear Models",                         4, "B+", "G"),
        ("STAT 149",     "Generalized Linear Models",             4, "A",  "G"),
        ("STAT 195",     "Statistical Computing",                 4, "A",  "G"),
        ("STAT 211",     "Statistical Inference I",               4, "A-", "G"),
        ("APMTH 207",    "Advanced Scientific Computing",         4, "A",  "G"),
        ("APMTH 231",    "Decision Theory",                       4, "B+", "G"),
        # 跨系选修
        ("COMPSCI 265",  "Big Data Systems",                      4, "A-", "G"),
        ("MATH 154",     "Probability Theory",                    4, "A",  "G"),
    ],
}

# ============ 哈佛学费 — 2025-2026 官方数据（按学期，美元）============

TUITION_PER_TERM = {
    "Computer Science (A.B.)":  29660,   # FAS 本科 $59,320/年 ÷ 2
    "Computer Science (S.M.)":  28664,   # GSAS 硕士 $57,328/年 ÷ 2
    "Computer Science (Ph.D.)": 14332,   # GSAS 博士（减免后）$28,664/年 ÷ 2
    "Data Science (S.M.)":      28664,   # GSAS 硕士
}

# 附加费用 — 2025-2026 官方数据（按学期，仅 build() 内部使用）
_FEE_HEALTH   = 3054    # 学生健康保险计划 (HUSHP) $6,108/年 ÷ 2
_FEE_ACTIVITY = 225     # 学生活动费 $450/年 ÷ 2
_FEE_GSC      = 35      # Harvard Griffin GSAS Student Council 费（秋季学期收取）


# ============ 美国地址数据 ============

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

US_STREETS = [
    "Main St", "Oak Ave", "Maple Dr", "Park Rd", "Cedar Ln",
    "Elm St", "Pine Ave", "Washington Blvd", "Lincoln Way", "Madison Ave",
    "Jefferson St", "Adams Rd", "Franklin Dr", "Liberty Ln", "Union St",
]


@dataclass
class HarvardStudentData:
    """
    哈佛大学3种文档所需的完整学生数据。

    学生证用到：first_name, last_name, student_id, program, school_code, valid_thru
    成绩单用到：first_name, last_name, student_id, printed_date, courses, gpa, address
    发票用到：  first_name, last_name, student_id, invoice_number, tuition, term, fees, address
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

    # 学费与附加费明细（发票生成直接读取这些字段）
    tuition_amount: int      # 当期学费（不含附加费）
    fee_health:     int      # 健康保险费
    fee_activity:   int      # 学生活动费
    fee_gsc:        int      # GSC 费用

    # 美国地址（4行：姓名、街道、城市州邮编、国家）
    address: Tuple[str, str, str, str]


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
    last = rng.choice(LAST_NAMES)

    # 邮箱生成（三种格式之一）
    patterns = [
        f"{first[0].lower()}{last.lower()}{rng.randint(100, 999)}",
        f"{first.lower()}.{last.lower()}{rng.randint(10, 99)}",
        f"{last.lower()}{first[0].lower()}{rng.randint(100, 999)}",
    ]
    email = f"{rng.choice(patterns)}@g.harvard.edu"

    # 出生日期（适合18-26岁在校生）
    now = datetime.now()
    birth_year = rng.randint(now.year - 26, now.year - 18)
    birth_month = rng.randint(1, 12)
    birth_day = rng.randint(1, 28)
    birth_date = f"{birth_year}-{birth_month:02d}-{birth_day:02d}"

    # 学号（8位，哈佛学号范围参考）
    student_id = str(rng.randint(10000000, 99999999))

    # GPA（3.50-3.99，哈佛平均 GPA 约 3.7）
    gpa = f"{3.50 + rng.random() * 0.49:.2f}"

    # 入学年份（近4年）
    enrollment_year = rng.randint(now.year - 4, now.year - 1)

    # 当前学期
    month = now.month
    year = now.year
    term = f"Spring {year}" if month <= 6 else f"Fall {year}"

    # 发票号
    invoice_number = f"INV-{time.strftime('%Y%m%d')}-{student_id}"

    school_code = PROGRAM_SCHOOL_CODE.get(program, "GSAS")
    course_pool = PROGRAM_COURSES.get(program, PROGRAM_COURSES["Computer Science (A.B.)"])
    # 从课程池中随机选取 8-12 门，模拟真实学期修课记录
    num_courses = rng.randint(8, min(12, len(course_pool)))
    courses = rng.sample(course_pool, num_courses)
    tuition_amount = TUITION_PER_TERM.get(program, 28664)

    # 地址生成
    addr_info = rng.choice(US_ADDRESSES)
    street_num = rng.randint(100, 9999)
    street = rng.choice(US_STREETS)
    apt = f", Apt {rng.randint(1, 999)}" if rng.random() < 0.3 else ""
    address = (
        f"{first} {last}",
        f"{street_num} {street}{apt}",
        f"{addr_info['city']}, {addr_info['state']} {addr_info['zip']}",
        "United States",
    )

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
        fee_health=_FEE_HEALTH,
        fee_activity=_FEE_ACTIVITY,
        fee_gsc=_FEE_GSC,
        address=address,
    )
