"""
大学数据模块
包含支持的大学列表和选择逻辑
支持按地区筛选大学
"""

import random
from typing import Dict, List, Optional

from stats import stats

# ============ 地区枚举 ============
REGIONS = {
    "us": "美国",
    "ca": "加拿大",
    "uk": "英国",
    "au": "澳大利亚",
    "in": "印度",
}

# ============ 大学列表（带权重、地区、启用状态和支持文档） ============
# 注意: 截至2026年1月，新的 Gemini 学生注册仅限美国
# 其他国家可能适用于现有用户，但新注册受限
#
# 字段说明:
#   enabled: 是否启用（False 的大学不会被选中）
#   docs: 该大学支持的文档类型列表（会全部生成并上传）
#         可选值: "transcript"（成绩单）, "student_id"（学生证）, "receipt"（收据）
#   template: 文档模板（默认 "generic"，Harvard 使用 "harvard"）

UNIVERSITIES = [
    # =========== 美国 - 高优先级 ===========
    # 这些学校对新注册用户成功率最高
    {"id": 2565, "name": "Pennsylvania State University-Main Campus", "domain": "psu.edu", "weight": 100, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3499, "name": "University of California, Los Angeles", "domain": "ucla.edu", "weight": 98, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3491, "name": "University of California, Berkeley", "domain": "berkeley.edu", "weight": 97, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 1953, "name": "Massachusetts Institute of Technology", "domain": "mit.edu", "weight": 95, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3113, "name": "Stanford University", "domain": "stanford.edu", "weight": 95, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 2285, "name": "New York University", "domain": "nyu.edu", "weight": 96, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 1426, "name": "Harvard University", "domain": "harvard.edu", "weight": 92, "region": "us", "enabled": True, "docs": ["transcript", "student_id"], "template": "harvard"},
    {"id": 590759, "name": "Yale University", "domain": "yale.edu", "weight": 90, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 2626, "name": "Princeton University", "domain": "princeton.edu", "weight": 90, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 698, "name": "Columbia University", "domain": "columbia.edu", "weight": 92, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3508, "name": "University of Chicago", "domain": "uchicago.edu", "weight": 88, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 943, "name": "Duke University", "domain": "duke.edu", "weight": 88, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 751, "name": "Cornell University", "domain": "cornell.edu", "weight": 90, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 2420, "name": "Northwestern University", "domain": "northwestern.edu", "weight": 88, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    # 更多美国大学
    {"id": 3568, "name": "University of Michigan", "domain": "umich.edu", "weight": 95, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3686, "name": "University of Texas at Austin", "domain": "utexas.edu", "weight": 94, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 1217, "name": "Georgia Institute of Technology", "domain": "gatech.edu", "weight": 93, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 602, "name": "Carnegie Mellon University", "domain": "cmu.edu", "weight": 92, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3477, "name": "University of California, San Diego", "domain": "ucsd.edu", "weight": 93, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3600, "name": "University of North Carolina at Chapel Hill", "domain": "unc.edu", "weight": 90, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3645, "name": "University of Southern California", "domain": "usc.edu", "weight": 91, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3629, "name": "University of Pennsylvania", "domain": "upenn.edu", "weight": 90, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 1603, "name": "Indiana University Bloomington", "domain": "iu.edu", "weight": 88, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 2506, "name": "Ohio State University", "domain": "osu.edu", "weight": 90, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 2700, "name": "Purdue University", "domain": "purdue.edu", "weight": 89, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3761, "name": "University of Washington", "domain": "uw.edu", "weight": 90, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3770, "name": "University of Wisconsin-Madison", "domain": "wisc.edu", "weight": 88, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3562, "name": "University of Maryland", "domain": "umd.edu", "weight": 87, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 519, "name": "Boston University", "domain": "bu.edu", "weight": 86, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 378, "name": "Arizona State University", "domain": "asu.edu", "weight": 92, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3521, "name": "University of Florida", "domain": "ufl.edu", "weight": 90, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3535, "name": "University of Illinois at Urbana-Champaign", "domain": "illinois.edu", "weight": 91, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3557, "name": "University of Minnesota Twin Cities", "domain": "umn.edu", "weight": 88, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3483, "name": "University of California, Davis", "domain": "ucdavis.edu", "weight": 89, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3487, "name": "University of California, Irvine", "domain": "uci.edu", "weight": 88, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 3502, "name": "University of California, Santa Barbara", "domain": "ucsb.edu", "weight": 87, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    # 社区学院（可能成功率更高）
    {"id": 2874, "name": "Santa Monica College", "domain": "smc.edu", "weight": 85, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    {"id": 2350, "name": "Northern Virginia Community College", "domain": "nvcc.edu", "weight": 84, "region": "us", "enabled": True, "docs": ["transcript", "student_id"]},
    # =========== 加拿大（低优先级 - 新注册可能无法使用） ===========
    {"id": 328355, "name": "University of Toronto", "domain": "utoronto.ca", "weight": 40, "region": "ca", "enabled": False, "docs": ["transcript", "student_id"]},
    {"id": 328315, "name": "University of British Columbia", "domain": "ubc.ca", "weight": 38, "region": "ca", "enabled": False, "docs": ["transcript", "student_id"]},
    # =========== 英国 ===========
    {"id": 273409, "name": "University of Oxford", "domain": "ox.ac.uk", "weight": 35, "region": "uk", "enabled": False, "docs": ["transcript", "student_id"]},
    {"id": 273378, "name": "University of Cambridge", "domain": "cam.ac.uk", "weight": 35, "region": "uk", "enabled": False, "docs": ["transcript", "student_id"]},
    # =========== 印度（新注册可能被阻止） ===========
    {"id": 10007277, "name": "Indian Institute of Technology Delhi", "domain": "iitd.ac.in", "weight": 20, "region": "in", "enabled": False, "docs": ["transcript"]},
    {"id": 3819983, "name": "University of Mumbai", "domain": "mu.ac.in", "weight": 15, "region": "in", "enabled": False, "docs": ["transcript"]},
    # =========== 澳大利亚 ===========
    {"id": 345301, "name": "The University of Melbourne", "domain": "unimelb.edu.au", "weight": 30, "region": "au", "enabled": False, "docs": ["transcript", "student_id"]},
    {"id": 345303, "name": "The University of Sydney", "domain": "sydney.edu.au", "weight": 28, "region": "au", "enabled": False, "docs": ["transcript", "student_id"]},
]


def get_available_regions() -> Dict[str, str]:
    """
    获取所有可用的地区
    
    返回:
        地区代码到名称的映射字典
    """
    return REGIONS.copy()


def get_universities_by_region(region: Optional[str] = None, include_disabled: bool = False) -> List[Dict]:
    """
    按地区获取大学列表（默认只返回已启用的大学）
    
    参数:
        region: 地区代码 ("us", "ca", "uk", "au", "in")，为 None 时返回所有大学
        include_disabled: 是否包含未启用的大学
    
    返回:
        大学列表（包含 idExtended 字段）
    """
    # 过滤启用状态
    candidates = UNIVERSITIES if include_disabled else [u for u in UNIVERSITIES if u.get("enabled", True)]
    
    if region is not None:
        region = region.lower()
        candidates = [u for u in candidates if u.get("region") == region]
    
    # 添加 idExtended 字段
    return [{**u, "idExtended": str(u["id"])} for u in candidates]


def select_university(region: Optional[str] = None, rng: Optional[random.Random] = None) -> Dict:
    """
    基于成功率的加权随机选择（只从已启用的大学中选择）
    
    参数:
        region: 可选，限制选择范围到指定地区
        rng: 可选，随机数生成器（用于确定性选择）
    
    返回:
        选中的大学字典（包含 idExtended 字段）
    """
    # 只从已启用的大学中选择
    enabled = [u for u in UNIVERSITIES if u.get("enabled", True)]
    
    # 按地区过滤
    if region:
        candidates = [u for u in enabled if u.get("region") == region.lower()]
        if not candidates:
            candidates = enabled  # 如果指定地区无结果，回退到全部已启用大学
    else:
        candidates = enabled
    
    if not candidates:
        raise RuntimeError("没有已启用的大学可供选择，请在 UNIVERSITIES 中至少启用一所大学")
    
    # 计算权重
    weights = []
    for uni in candidates:
        weight = uni["weight"] * (stats.get_rate(uni["name"]) / 50)
        weights.append(max(1, weight))

    total = sum(weights)
    r = rng.uniform(0, total) if rng else random.uniform(0, total)

    cumulative = 0
    for uni, weight in zip(candidates, weights):
        cumulative += weight
        if r <= cumulative:
            return {**uni, "idExtended": str(uni["id"])}
    
    return {**candidates[0], "idExtended": str(candidates[0]["id"])}


def get_university_by_id(university_id: int) -> Optional[Dict]:
    """
    根据大学ID获取大学信息
    
    参数:
        university_id: 大学ID
    
    返回:
        大学字典，未找到则返回 None
    """
    for uni in UNIVERSITIES:
        if uni["id"] == university_id:
            return {**uni, "idExtended": str(uni["id"])}
    return None
