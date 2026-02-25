"""
Google One (Gemini) 学生验证工具
SheerID 学生验证 - Google One AI Premium

⚠️  重要提示 (2026年1月):
Google 已将 Gemini 学生验证限制为仅限美国新注册用户
其他国家用户可能遇到较高的失败率

增强功能:
- 按组织追踪成功率
- 加权大学选择 (美国院校优先)
- 指数退避重试
- 反速率限制
- Chrome TLS 模拟反检测

依赖:
- curl_cffi: pip install curl_cffi (TLS 伪装必需)
- 匹配美国位置的住宅代理 (强烈推荐)

Author: ThanhNguyxn
"""

import hashlib
import json
import random
import re
import sys
import time
from io import BytesIO
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    import httpx
except ImportError:
    print("❌ 错误: 需要 httpx，请安装: pip install httpx")
    sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("❌ 错误: 需要 Pillow，请安装: pip install Pillow")
    sys.exit(1)

# 导入反检测模块
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from anti_detect import (
        get_headers,
        get_fingerprint,
        get_random_user_agent,
        random_delay as anti_delay,
        create_session,
        get_matched_ua_for_impersonate,
        make_request,
        handle_fraud_rejection,
        should_retry_fraud,
    )

    HAS_ANTI_DETECT = True
    print("[信息] 反检测模块已加载")
except ImportError:
    HAS_ANTI_DETECT = False
    print("[警告] 未找到 anti_detect.py，使用基础请求头")
    print("[警告] 没有反检测模块检测风险极高!")


# ============ 配置 ============
PROGRAM_ID = "67c8c14f5f17a83b745e3f82"
SHEERID_API_URL = "https://services.sheerid.com/rest/v2"
MIN_DELAY = 300
MAX_DELAY = 800


# ============ 成功率追踪 ============
class Stats:
    """按组织追踪成功率"""

    def __init__(self):
        self.file = Path(__file__).parent / "stats.json"
        self.data = self._load()

    def _load(self) -> Dict:
        if self.file.exists():
            try:
                return json.loads(self.file.read_text())
            except:
                pass
        return {"total": 0, "success": 0, "failed": 0, "orgs": {}}

    def _save(self):
        self.file.write_text(json.dumps(self.data, indent=2))

    def record(self, org: str, success: bool):
        self.data["total"] += 1
        self.data["success" if success else "failed"] += 1

        if org not in self.data["orgs"]:
            self.data["orgs"][org] = {"success": 0, "failed": 0}
        self.data["orgs"][org]["success" if success else "failed"] += 1
        self._save()

    def get_rate(self, org: str = None) -> float:
        if org:
            o = self.data["orgs"].get(org, {})
            total = o.get("success", 0) + o.get("failed", 0)
            return o.get("success", 0) / total * 100 if total else 50
        return (
            self.data["success"] / self.data["total"] * 100 if self.data["total"] else 0
        )

    def print_stats(self):
        print("\n📊 统计:")
        print(
            f"   Total: {self.data['total']} | ✅ {self.data['success']} | ❌ {self.data['failed']}"
        )
        if self.data["total"]:
            print(f"   成功率: {self.get_rate():.1f}%")


stats = Stats()


# ============ 大学列表与权重 ============
# 注意: 2026年1月起，Gemini 学生新注册仅限美国
# 其他国家可能对现有用户有效，但新注册受限

UNIVERSITIES = [
    # =========== 美国 - 高优先级 ===========
    # 新注册成功率最高
    {
        "id": 2565,
        "name": "Pennsylvania State University-Main Campus",
        "domain": "psu.edu",
        "weight": 100,
    },
    {
        "id": 3499,
        "name": "University of California, Los Angeles",
        "domain": "ucla.edu",
        "weight": 98,
    },
    {
        "id": 3491,
        "name": "University of California, Berkeley",
        "domain": "berkeley.edu",
        "weight": 97,
    },
    {
        "id": 1953,
        "name": "Massachusetts Institute of Technology",
        "domain": "mit.edu",
        "weight": 95,
    },
    {"id": 3113, "name": "Stanford University", "domain": "stanford.edu", "weight": 95},
    {"id": 2285, "name": "New York University", "domain": "nyu.edu", "weight": 96},
    {"id": 1426, "name": "Harvard University", "domain": "harvard.edu", "weight": 92},
    {"id": 590759, "name": "Yale University", "domain": "yale.edu", "weight": 90},
    {
        "id": 2626,
        "name": "Princeton University",
        "domain": "princeton.edu",
        "weight": 90,
    },
    {"id": 698, "name": "Columbia University", "domain": "columbia.edu", "weight": 92},
    {
        "id": 3508,
        "name": "University of Chicago",
        "domain": "uchicago.edu",
        "weight": 88,
    },
    {"id": 943, "name": "Duke University", "domain": "duke.edu", "weight": 88},
    {"id": 751, "name": "Cornell University", "domain": "cornell.edu", "weight": 90},
    {
        "id": 2420,
        "name": "Northwestern University",
        "domain": "northwestern.edu",
        "weight": 88,
    },
    # 更多美国大学
    {"id": 3568, "name": "University of Michigan", "domain": "umich.edu", "weight": 95},
    {
        "id": 3686,
        "name": "University of Texas at Austin",
        "domain": "utexas.edu",
        "weight": 94,
    },
    {
        "id": 1217,
        "name": "Georgia Institute of Technology",
        "domain": "gatech.edu",
        "weight": 93,
    },
    {
        "id": 602,
        "name": "Carnegie Mellon University",
        "domain": "cmu.edu",
        "weight": 92,
    },
    {
        "id": 3477,
        "name": "University of California, San Diego",
        "domain": "ucsd.edu",
        "weight": 93,
    },
    {
        "id": 3600,
        "name": "University of North Carolina at Chapel Hill",
        "domain": "unc.edu",
        "weight": 90,
    },
    {
        "id": 3645,
        "name": "University of Southern California",
        "domain": "usc.edu",
        "weight": 91,
    },
    {
        "id": 3629,
        "name": "University of Pennsylvania",
        "domain": "upenn.edu",
        "weight": 90,
    },
    {
        "id": 1603,
        "name": "Indiana University Bloomington",
        "domain": "iu.edu",
        "weight": 88,
    },
    {"id": 2506, "name": "Ohio State University", "domain": "osu.edu", "weight": 90},
    {"id": 2700, "name": "Purdue University", "domain": "purdue.edu", "weight": 89},
    {"id": 3761, "name": "University of Washington", "domain": "uw.edu", "weight": 90},
    {
        "id": 3770,
        "name": "University of Wisconsin-Madison",
        "domain": "wisc.edu",
        "weight": 88,
    },
    {"id": 3562, "name": "University of Maryland", "domain": "umd.edu", "weight": 87},
    {"id": 519, "name": "Boston University", "domain": "bu.edu", "weight": 86},
    {"id": 378, "name": "Arizona State University", "domain": "asu.edu", "weight": 92},
    {"id": 3521, "name": "University of Florida", "domain": "ufl.edu", "weight": 90},
    {
        "id": 3535,
        "name": "University of Illinois at Urbana-Champaign",
        "domain": "illinois.edu",
        "weight": 91,
    },
    {
        "id": 3557,
        "name": "University of Minnesota Twin Cities",
        "domain": "umn.edu",
        "weight": 88,
    },
    {
        "id": 3483,
        "name": "University of California, Davis",
        "domain": "ucdavis.edu",
        "weight": 89,
    },
    {
        "id": 3487,
        "name": "University of California, Irvine",
        "domain": "uci.edu",
        "weight": 88,
    },
    {
        "id": 3502,
        "name": "University of California, Santa Barbara",
        "domain": "ucsb.edu",
        "weight": 87,
    },
    # 社区学院 (可能成功率更高)
    {"id": 2874, "name": "Santa Monica College", "domain": "smc.edu", "weight": 85},
    {
        "id": 2350,
        "name": "Northern Virginia Community College",
        "domain": "nvcc.edu",
        "weight": 84,
    },
    # =========== 其他国家 (低优先级 - 新注册可能无效) ===========
    # 加拿大
    {
        "id": 328355,
        "name": "University of Toronto",
        "domain": "utoronto.ca",
        "weight": 40,
    },
    {
        "id": 328315,
        "name": "University of British Columbia",
        "domain": "ubc.ca",
        "weight": 38,
    },
    # 英国
    {"id": 273409, "name": "University of Oxford", "domain": "ox.ac.uk", "weight": 35},
    {
        "id": 273378,
        "name": "University of Cambridge",
        "domain": "cam.ac.uk",
        "weight": 35,
    },
    # 印度 (新注册可能被封禁)
    {
        "id": 10007277,
        "name": "Indian Institute of Technology Delhi",
        "domain": "iitd.ac.in",
        "weight": 20,
    },
    {"id": 3819983, "name": "University of Mumbai", "domain": "mu.ac.in", "weight": 15},
    # 澳大利亚
    {
        "id": 345301,
        "name": "The University of Melbourne",
        "domain": "unimelb.edu.au",
        "weight": 30,
    },
    {
        "id": 345303,
        "name": "The University of Sydney",
        "domain": "sydney.edu.au",
        "weight": 28,
    },
]


def select_university() -> Dict:
    """基于成功率的加权随机选择"""
    weights = []
    for uni in UNIVERSITIES:
        weight = uni["weight"] * (stats.get_rate(uni["name"]) / 50)
        weights.append(max(1, weight))

    total = sum(weights)
    r = random.uniform(0, total)

    cumulative = 0
    for uni, weight in zip(UNIVERSITIES, weights):
        cumulative += weight
        if r <= cumulative:
            return {**uni, "idExtended": str(uni["id"])}
    return {**UNIVERSITIES[0], "idExtended": str(UNIVERSITIES[0]["id"])}


# ============ 工具函数 ============
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


# ============ 文档生成器 ============
def generate_transcript(first: str, last: str, school: str, dob: str) -> bytes:
    """生成学术成绩单 (成功率更高)"""
    w, h = 850, 1100
    img = Image.new("RGB", (w, h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_header = ImageFont.truetype("arial.ttf", 32)
        font_title = ImageFont.truetype("arial.ttf", 24)
        font_text = ImageFont.truetype("arial.ttf", 16)
        font_bold = ImageFont.truetype("arialbd.ttf", 16)
    except Exception:
        font_header = font_title = font_text = font_bold = ImageFont.load_default()

    # 1. 标题
    draw.text(
        (w // 2, 50), school.upper(), fill=(0, 0, 0), font=font_header, anchor="mm"
    )
    draw.text(
        (w // 2, 90),
        "OFFICIAL ACADEMIC TRANSCRIPT",
        fill=(50, 50, 50),
        font=font_title,
        anchor="mm",
    )
    draw.line([(50, 110), (w - 50, 110)], fill=(0, 0, 0), width=2)

    # 2. 学生信息
    y = 150
    draw.text((50, y), f"Student Name: {first} {last}", fill=(0, 0, 0), font=font_bold)
    draw.text(
        (w - 300, y),
        f"Student ID: {random.randint(10000000, 99999999)}",
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

    # 3. 当前注册状态
    draw.rectangle([(50, y), (w - 50, y + 40)], fill=(240, 240, 240))
    draw.text(
        (w // 2, y + 20),
        "CURRENT STATUS: ENROLLED (SPRING 2025)",
        fill=(0, 100, 0),
        font=font_bold,
        anchor="mm",
    )
    y += 70

    # 4. 课程列表
    courses = [
        ("CS 101", "Intro to Computer Science", "4.0", "A"),
        ("MATH 201", "Calculus I", "3.0", "A-"),
        ("ENG 102", "Academic Writing", "3.0", "B+"),
        ("PHYS 150", "Physics for Engineers", "4.0", "A"),
        ("HIST 110", "World History", "3.0", "A"),
    ]

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

    # 5. 汇总
    draw.text((50, y), "Cumulative GPA: 3.85", font=font_bold, fill=(0, 0, 0))
    draw.text((w - 300, y), "Academic Standing: Good", font=font_bold, fill=(0, 0, 0))

    # 6. 水印/页脚
    draw.text(
        (w // 2, h - 50),
        "This document is electronically generated and valid without signature.",
        fill=(100, 100, 100),
        font=font_text,
        anchor="mm",
    )

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_student_id(first: str, last: str, school: str) -> bytes:
    """生成学生证卡片"""
    w, h = 650, 400
    # 随机微调背景色
    bg_color = (
        random.randint(240, 255),
        random.randint(240, 255),
        random.randint(240, 255),
    )
    img = Image.new("RGB", (w, h), bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font_lg = ImageFont.truetype("arial.ttf", 26)
        font_md = ImageFont.truetype("arial.ttf", 18)
        font_sm = ImageFont.truetype("arial.ttf", 14)
        font_bold = ImageFont.truetype("arialbd.ttf", 20)
    except Exception:
        font_lg = font_md = font_sm = font_bold = ImageFont.load_default()

    # 根据校名哈希生成一致但有变化的头部颜色
    header_color = (
        random.randint(0, 50),
        random.randint(0, 50),
        random.randint(50, 150),
    )

    draw.rectangle([(0, 0), (w, 80)], fill=header_color)
    draw.text(
        (w // 2, 40), school.upper(), fill=(255, 255, 255), font=font_lg, anchor="mm"
    )

    # 照片占位
    draw.rectangle(
        [(30, 100), (160, 280)], outline=(100, 100, 100), width=2, fill=(220, 220, 220)
    )
    draw.text((95, 190), "PHOTO", fill=(150, 150, 150), font=font_md, anchor="mm")

    # 信息
    x_info = 190
    y = 110
    draw.text((x_info, y), f"{first} {last}", fill=(0, 0, 0), font=font_bold)
    y += 40
    draw.text((x_info, y), "Student ID:", fill=(100, 100, 100), font=font_sm)
    draw.text(
        (x_info + 80, y),
        str(random.randint(10000000, 99999999)),
        fill=(0, 0, 0),
        font=font_md,
    )
    y += 30
    draw.text((x_info, y), "Role:", fill=(100, 100, 100), font=font_sm)
    draw.text((x_info + 80, y), "Student", fill=(0, 0, 0), font=font_md)
    y += 30
    draw.text((x_info, y), "Valid Thru:", fill=(100, 100, 100), font=font_sm)
    draw.text(
        (x_info + 80, y),
        f"05/{int(time.strftime('%Y')) + 1}",
        fill=(0, 0, 0),
        font=font_md,
    )

    # 条形码
    draw.rectangle([(0, 320), (w, 380)], fill=(255, 255, 255))
    for i in range(40):
        x = 50 + i * 14
        if random.random() > 0.3:
            draw.rectangle([(x, 330), (x + 8, 370)], fill=(0, 0, 0))

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ============ 验证器 ============
class GeminiVerifier:
    """增强版 Gemini 学生验证器"""

    def __init__(self, url: str, proxy: str = None):
        self.url = url
        self.vid = self._parse_id(url)
        self.fingerprint = generate_fingerprint()

        # 使用增强版反检测会话
        if HAS_ANTI_DETECT:
            self.client, self.lib_name, self.impersonate_target = create_session(proxy)
            print(
                f"[信息] 会话已创建，使用 {self.lib_name} (模拟: {self.impersonate_target})"
            )
        else:
            proxy_url = None
            if proxy:
                if not proxy.startswith("http"):
                    proxy = f"http://{proxy}"
                proxy_url = proxy
            self.client = httpx.Client(timeout=30, proxy=proxy_url)
            self.lib_name = "httpx"

        self.org = None

    def __del__(self):
        if hasattr(self, "client"):
            self.client.close()

    @staticmethod
    def _parse_id(url: str) -> Optional[str]:
        match = re.search(r"verificationId=([a-f0-9]+)", url, re.IGNORECASE)
        return match.group(1) if match else None

    def _request(
        self, method: str, endpoint: str, body: Dict = None
    ) -> Tuple[Dict, int]:
        random_delay()
        try:
            # 可用时使用反检测请求头
            headers = (
                get_headers(for_sheerid=True)
                if HAS_ANTI_DETECT
                else {"Content-Type": "application/json"}
            )
            resp = self.client.request(
                method, f"{SHEERID_API_URL}{endpoint}", json=body, headers=headers
            )
            try:
                parsed = resp.json() if resp.text else {}
            except Exception:
                parsed = {"_text": resp.text}
            return parsed, resp.status_code
        except Exception as e:
            raise Exception(f"请求失败: {e}")

    def _upload_s3(self, url: str, data: bytes) -> bool:
        # 不同 HTTP 库接受不同的参数名，尝试多种方式以最大化兼容性 (curl_cffi, httpx, requests)
        attempts = []
        # 第一种: httpx 签名
        attempts.append(
            lambda: self.client.put(
                url, content=data, headers={"Content-Type": "image/png"}, timeout=60
            )
        )
        # 第二种: requests 签名
        attempts.append(
            lambda: self.client.put(
                url, data=data, headers={"Content-Type": "image/png"}, timeout=60
            )
        )
        # 第三种: 通用 request 方法
        attempts.append(
            lambda: self.client.request(
                "PUT", url, data=data, headers={"Content-Type": "image/png"}, timeout=60
            )
        )

        last_exc = None
        for fn in attempts:
            try:
                resp = fn()
                if hasattr(resp, "status_code"):
                    if 200 <= resp.status_code < 300:
                        return True
                    try:
                        body = resp.json()
                    except Exception:
                        body = getattr(resp, "text", str(resp))
                    print(f"     ❗ S3 上传失败: HTTP {resp.status_code} | {body}")
                    return False
                else:
                    # 响应非标准对象，有值则视为成功
                    if resp:
                        return True
                    return False
            except TypeError as e:
                last_exc = e
                continue
            except Exception as e:
                last_exc = e
                continue

        print(f"     ❗ S3 上传失败，最后错误: {last_exc}")
        return False

    def check_link(self) -> Dict:
        """检查验证链接是否有效"""
        if not self.vid:
            return {"valid": False, "error": "无效的 URL"}

        data, status = self._request("GET", f"/verification/{self.vid}")
        if status != 200:
            return {"valid": False, "error": f"HTTP {status}"}

        step = data.get("currentStep", "")
        # 接受多个有效步骤 - 处理拒绝后重新上传
        valid_steps = ["collectStudentPersonalInfo", "docUpload", "sso"]
        if step in valid_steps:
            return {"valid": True, "step": step}
        elif step == "success":
            return {"valid": False, "error": "已验证通过"}
        elif step == "pending":
            return {"valid": False, "error": "已在审核中"}
        return {"valid": False, "error": f"无效步骤: {step}"}

    def verify(self) -> Dict:
        """运行完整验证流程"""
        if not self.vid:
            return {"success": False, "error": "无效的验证 URL"}

        try:
            # 先检查当前步骤
            check_data, check_status = self._request("GET", f"/verification/{self.vid}")
            current_step = (
                check_data.get("currentStep", "") if check_status == 200 else ""
            )

            # 生成信息
            first, last = generate_name()
            self.org = select_university()
            email = generate_email(first, last, self.org["domain"])
            dob = generate_birth_date()

            print(f"\n   🎓 学生: {first} {last}")
            print(f"   📧 邮箱: {email}")
            print(f"   🏫 学校: {self.org['name']}")
            print(f"   🎂 出生日期: {dob}")
            print(f"   🔑 ID: {self.vid[:20]}...")
            print(f"   📍 当前步骤: {current_step}")

            # 步骤1: 生成文档
            doc_type = "transcript" if random.random() < 0.7 else "id_card"
            if doc_type == "transcript":
                print("\n   ▶ 步骤 1/3: 生成学术成绩单...")
                doc = generate_transcript(first, last, self.org["name"], dob)
                filename = "transcript.png"
            else:
                print("\n   ▶ 步骤 1/3: 生成学生证...")
                doc = generate_student_id(first, last, self.org["name"])
                filename = "student_card.png"
            print(f"     📄 大小: {len(doc) / 1024:.1f} KB")

            # 步骤2: 提交信息 (已过此步骤则跳过)
            if current_step == "collectStudentPersonalInfo":
                print("   ▶ 步骤 2/3: 提交学生信息...")
                body = {
                    "firstName": first,
                    "lastName": last,
                    "birthDate": dob,
                    "email": email,
                    "phoneNumber": "",
                    "organization": {
                        "id": self.org["id"],
                        "idExtended": self.org["idExtended"],
                        "name": self.org["name"],
                    },
                    "deviceFingerprintHash": self.fingerprint,
                    "locale": "en-US",
                    "metadata": {
                        "marketConsentValue": False,
                        "verificationId": self.vid,
                        "refererUrl": f"https://services.sheerid.com/verify/{PROGRAM_ID}/?verificationId={self.vid}",
                        "flags": '{"collect-info-step-email-first":"default","doc-upload-considerations":"default","doc-upload-may24":"default","doc-upload-redesign-use-legacy-message-keys":false,"docUpload-assertion-checklist":"default","font-size":"default","include-cvec-field-france-student":"not-labeled-optional"}',
                        "submissionOptIn": "By submitting the personal information above, I acknowledge that my personal information is being collected under the privacy policy of the business from which I am seeking a discount",
                    },
                }

                data, status = self._request(
                    "POST",
                    f"/verification/{self.vid}/step/collectStudentPersonalInfo",
                    body,
                )

                if status != 200:
                    stats.record(self.org["name"], False)
                    print(f"     ❗ 提交失败: HTTP {status}")
                    print(f"     ❗ 响应内容: {data}")
                    return {
                        "success": False,
                        "error": f"提交失败: {status} - {data}",
                    }

                if data.get("currentStep") == "error":
                    error_ids = data.get("errorIds", [])
                    # 检查欺诈拒绝
                    if "fraudRulesReject" in str(error_ids):
                        if HAS_ANTI_DETECT:
                            handle_fraud_rejection(
                                retry_count=0,
                                error_payload=data,
                                message=f"University: {self.org['name']}",
                            )
                    stats.record(self.org["name"], False)
                    return {
                        "success": False,
                        "error": f"Error: {error_ids}",
                        "is_fraud_reject": "fraudRulesReject" in str(error_ids),
                    }

                print(f"     📍 当前步骤: {data.get('currentStep')}")
                current_step = data.get("currentStep", "")
            elif current_step in ["docUpload", "sso"]:
                print("   ▶ 步骤 2/3: 跳过 (已过信息提交)...")
            else:
                print(
                    f"   ▶ 步骤 2/3: 未知步骤 '{current_step}'，尝试继续..."
                )

            # 步骤3: 跳过 SSO (如需要)
            if current_step in ["sso", "collectStudentPersonalInfo"]:
                print("   ▶ 步骤 3/4: 跳过 SSO...")
                self._request("DELETE", f"/verification/{self.vid}/step/sso")

            # 步骤4: 上传文档
            print("   ▶ 步骤 4/5: 上传文档...")
            upload_body = {
                "files": [
                    {
                        "fileName": filename,
                        "mimeType": "image/png",
                        "fileSize": len(doc),
                    }
                ]
            }
            data, status = self._request(
                "POST", f"/verification/{self.vid}/step/docUpload", upload_body
            )

            if not data.get("documents"):
                stats.record(self.org["name"], False)
                return {"success": False, "error": "没有上传 URL"}

            upload_url = data["documents"][0].get("uploadUrl")
            if not self._upload_s3(upload_url, doc):
                stats.record(self.org["name"], False)
                return {"success": False, "error": "上传失败"}

            print("     ✅ 文档已上传!")

            # 步骤5: 完成文档上传
            print("   ▶ 步骤 5/5: 完成上传...")
            data, status = self._request(
                "POST", f"/verification/{self.vid}/step/completeDocUpload"
            )
            final_step = data.get("currentStep", "unknown")
            print(f"     📍 最终步骤: {final_step}")

            if final_step == "success":
                stats.record(self.org["name"], True)
                return {
                    "success": True,
                    "message": "已立即验证! 无需审核。",
                    "student": f"{first} {last}",
                    "email": email,
                    "school": self.org["name"],
                    "redirectUrl": data.get("redirectUrl"),
                }
            elif final_step == "pending":
                return {
                    "success": False,
                    "pending": True,
                    "message": "文档已提交审核，等待 24-48 小时结果。",
                    "student": f"{first} {last}",
                    "email": email,
                    "school": self.org["name"],
                }
            elif final_step in ["rejected", "error"]:
                stats.record(self.org["name"], False)
                error_ids = data.get("errorIds", [])
                return {
                    "success": False,
                    "error": f"被拒绝: {error_ids}"
                    if error_ids
                    else "文档被拒绝",
                }
            else:
                return {
                    "success": False,
                    "pending": True,
                    "message": f"未知状态: {final_step}，请手动检查。",
                    "student": f"{first} {last}",
                    "email": email,
                    "school": self.org["name"],
                }

        except Exception as e:
            if self.org:
                stats.record(self.org["name"], False)
            return {"success": False, "error": str(e)}


# ============ 主程序 ============
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Google One (Gemini) 学生验证工具"
    )
    parser.add_argument("url", nargs="?", help="验证 URL")
    parser.add_argument(
        "--proxy", help="代理服务器 (host:port 或 http://user:pass@host:port)"
    )
    parser.add_argument(
        "--force", action="store_true", help="强制运行，跳过警告"
    )
    args = parser.parse_args()

    print()
    print("╔" + "═" * 56 + "╗")
    print("║" + " 🤖 Google One (Gemini) 验证工具".center(56) + "║")
    print("║" + " SheerID 学生优惠".center(56) + "║")
    print("╚" + "═" * 56 + "╝")
    print()

    # ⚠️ 仅限美国警告
    print("   " + "⚠" * 20)
    print("   ⚠️  重要警告 (2026年1月):")
    print("   ⚠️  Gemini 学生验证现已限制为仅限美国!")
    print("   ⚠️  ")
    print("   ⚠️  成功要求:")
    print("   ⚠️  1. 美国住宅代理 (数据中心 IP 被封禁)")
    print("   ⚠️  2. 已安装 curl_cffi (pip install curl_cffi)")
    print("   ⚠️  3. 美国大学选择")
    print("   ⚠️  ")
    print("   ⚠️  非美国用户: 建议使用 perplexity-verify-tool")
    print("   ⚠️  或 spotify-verify-tool 替代")
    print("   " + "⚠" * 20)
    print()

    if not args.force:
        confirm = input("   是否继续? (y/N): ").strip().lower()
        if confirm != "y":
            print("\n   已中止。使用 --force 跳过此警告")
            return

    # 获取 URL
    if args.url:
        url = args.url
    else:
        url = input("\n   请输入验证 URL: ").strip()

    if not url or "sheerid.com" not in url:
        print("\n   ❌ 无效 URL，必须包含 sheerid.com")
        return

    # 显示代理信息
    if args.proxy:
        print(f"   🔒 使用代理: {args.proxy}")
    else:
        print("   ⚠️  未指定代理! 使用直连")
        print("   ⚠️  可能导致验证失败")

    print("\n   ⏳ 处理中...")

    verifier = GeminiVerifier(url, proxy=args.proxy)

    # 先检查链接
    check = verifier.check_link()
    if not check.get("valid"):
        print(f"\n   ❌ 链接错误: {check.get('error')}")
        return

    result = verifier.verify()

    print()
    print("─" * 58)
    if result.get("success"):
        print("   🎉 立即验证成功!")
        print(f"   👤 {result.get('student')}")
        print(f"   📧 {result.get('email')}")
        print(f"   🏫 {result.get('school')}")
        print()
        print("   ✅ 无需审核 - 已通过权威数据库验证!")
    elif result.get("pending"):
        print("   ⏳ 已提交审核")
        print(f"   👤 {result.get('student')}")
        print(f"   📧 {result.get('email')}")
        print(f"   🏫 {result.get('school')}")
        print()
        print("   ⚠️  文档已上传，等待审核 (24-48小时)")
        print("   ⚠️  这不保证一定成功!")
    else:
        print(f"   ❌ 失败: {result.get('error')}")
    print("─" * 58)

    stats.print_stats()


if __name__ == "__main__":
    main()
