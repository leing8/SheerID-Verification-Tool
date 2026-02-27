"""
大学列表与加权选择
"""

import random
from typing import Dict

from stats import stats

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
