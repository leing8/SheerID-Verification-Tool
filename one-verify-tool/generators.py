"""
数据生成器

姓名、邮箱、出生日期、浏览器指纹等随机数据生成。
"""

import hashlib
import random
import time
from typing import Tuple

from config import MIN_DELAY, MAX_DELAY

# ============ 姓名数据 ============
FIRST_NAMES = [
    "James",
    "John",
    "Robert",
    "Michael",
    "William",
    "David",
    "Richard",
    "Joseph",
    "Thomas",
    "Christopher",
    "Charles",
    "Daniel",
    "Matthew",
    "Anthony",
    "Mark",
    "Donald",
    "Steven",
    "Andrew",
    "Paul",
    "Joshua",
    "Kenneth",
    "Kevin",
    "Brian",
    "George",
    "Timothy",
    "Ronald",
    "Edward",
    "Jason",
    "Jeffrey",
    "Ryan",
    "Mary",
    "Patricia",
    "Jennifer",
    "Linda",
    "Barbara",
    "Elizabeth",
    "Susan",
    "Jessica",
    "Sarah",
    "Karen",
    "Lisa",
    "Nancy",
    "Betty",
    "Margaret",
    "Sandra",
    "Ashley",
    "Kimberly",
    "Emily",
    "Donna",
    "Michelle",
    "Dorothy",
    "Carol",
    "Amanda",
    "Melissa",
    "Deborah",
    "Stephanie",
    "Rebecca",
    "Sharon",
    "Laura",
    "Emma",
    "Olivia",
    "Ava",
    "Isabella",
    "Sophia",
    "Mia",
    "Charlotte",
    "Amelia",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
    "Lee",
    "Perez",
    "Thompson",
    "White",
    "Harris",
    "Sanchez",
    "Clark",
    "Ramirez",
    "Lewis",
    "Robinson",
    "Walker",
    "Young",
    "Allen",
    "King",
    "Wright",
    "Scott",
    "Torres",
    "Nguyen",
    "Hill",
    "Flores",
    "Green",
    "Adams",
    "Nelson",
    "Baker",
    "Hall",
    "Rivera",
    "Campbell",
    "Mitchell",
    "Carter",
    "Roberts",
    "Turner",
    "Phillips",
    "Evans",
    "Parker",
    "Edwards",
]


def random_delay():
    time.sleep(random.randint(MIN_DELAY, MAX_DELAY) / 1000)


def generate_fingerprint() -> str:
    """生成模拟真实浏览器指纹以规避欺诈检测"""
    # 常见屏幕分辨率
    resolutions = [
        "1920x1080",
        "1366x768",
        "1536x864",
        "1440x900",
        "1280x720",
        "2560x1440",
    ]
    # 常见时区
    timezones = [-8, -7, -6, -5, -4, 0, 1, 2, 3, 5.5, 8, 9, 10]
    # 常见语言
    languages = ["en-US", "en-GB", "en-CA", "en-AU", "es-ES", "fr-FR", "de-DE", "pt-BR"]
    # 常见平台
    platforms = ["Win32", "MacIntel", "Linux x86_64"]
    # 浏览器厂商
    vendors = ["Google Inc.", "Apple Computer, Inc.", ""]

    components = [
        str(int(time.time() * 1000)),
        str(random.random()),
        random.choice(resolutions),
        str(random.choice(timezones)),
        random.choice(languages),
        random.choice(platforms),
        random.choice(vendors),
        str(random.randint(1, 16)),  # CPU 核心数
        str(random.randint(2, 32)),  # 设备内存(GB)
        str(random.randint(0, 1)),   # 触屏支持
    ]
    return hashlib.md5("|".join(components).encode()).hexdigest()


def generate_name() -> Tuple[str, str]:
    return random.choice(FIRST_NAMES), random.choice(LAST_NAMES)


def generate_email(first: str, last: str, domain: str) -> str:
    patterns = [
        f"{first[0].lower()}{last.lower()}{random.randint(100, 999)}",
        f"{first.lower()}.{last.lower()}{random.randint(10, 99)}",
        f"{last.lower()}{first[0].lower()}{random.randint(100, 999)}",
    ]
    return f"{random.choice(patterns)}@{domain}"


def generate_birth_date() -> str:
    year = random.randint(2000, 2006)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"
