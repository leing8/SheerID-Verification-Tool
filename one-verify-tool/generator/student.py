"""
学生信息生成模块 - 生成虚拟学生信息

包含:
- generate_name: 生成随机姓名
- generate_email: 生成学校邮箱
- generate_birth_date: 生成出生日期
"""

import random
import time
from typing import Tuple, Optional

from data import FIRST_NAMES, LAST_NAMES


def generate_name(include_middle: bool = False) -> Tuple[str, str]:
    """
    生成随机英文姓名
    
    Args:
        include_middle: 是否包含中间名（可选）
    
    Returns:
        Tuple[str, str]: (名, 姓) 或包含中间名的格式
    """
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    
    # 偶尔添加中间名
    if include_middle and random.random() < 0.3:
        middle = random.choice(FIRST_NAMES)
        # 有时只用首字母
        if random.random() < 0.5:
            middle = middle[0] + "."
        return f"{first} {middle}", last
    
    return first, last


def generate_email(first: str, last: str, domain: str) -> str:
    """
    生成学校邮箱地址
    
    使用多种常见格式（模拟真实学校邮箱的多样性）:
    - 首字母+姓+数字: jsmith123@xxx.edu
    - 名.姓+数字: john.smith12@xxx.edu
    - 姓+首字母+数字: smithj456@xxx.edu
    - 姓名无空格+数字: johnsmith@xxx.edu
    - 首字母+姓: jsmith@xxx.edu
    - 完整格式: john.a.smith@xxx.edu
    
    Args:
        first: 名（可能包含中间名）
        last: 姓
        domain: 学校邮箱域名
    
    Returns:
        str: 生成的邮箱地址
    """
    # 处理可能的中间名
    first_parts = first.split()
    first_name = first_parts[0].lower()
    middle_initial = first_parts[1][0].lower() if len(first_parts) > 1 else ""
    last_lower = last.lower()
    
    # 生成数字后缀
    num_2 = random.randint(10, 99)
    num_3 = random.randint(100, 999)
    year_2 = random.randint(22, 28)  # 2022-2028
    
    patterns = [
        # 格式: 权重（概率选择）
        (f"{first_name[0]}{last_lower}{num_3}", 20),
        (f"{first_name}.{last_lower}{num_2}", 20),
        (f"{last_lower}{first_name[0]}{num_3}", 15),
        (f"{first_name}{last_lower}", 10),
        (f"{first_name[0]}{last_lower}", 10),
        (f"{first_name}{last_lower}{num_2}", 8),
        (f"{last_lower}.{first_name}", 5),
        (f"{first_name}_{last_lower}", 5),
        (f"{first_name[0]}{last_lower}{year_2}", 5),
    ]
    
    # 如果有中间名，添加额外格式
    if middle_initial:
        patterns.extend([
            (f"{first_name}.{middle_initial}.{last_lower}", 5),
            (f"{first_name[0]}{middle_initial}{last_lower}", 3),
        ])
    
    # 加权随机选择
    total_weight = sum(w for _, w in patterns)
    r = random.uniform(0, total_weight)
    cumulative = 0
    
    for pattern, weight in patterns:
        cumulative += weight
        if r <= cumulative:
            return f"{pattern}@{domain}"
    
    # 默认格式
    return f"{first_name[0]}{last_lower}{num_3}@{domain}"


def generate_birth_date(min_age: int = 18, max_age: int = 26) -> str:
    """
    生成合理的学生出生日期
    
    生成年龄在指定范围内的日期（适合大学生）
    
    Args:
        min_age: 最小年龄，默认 18
        max_age: 最大年龄，默认 26
    
    Returns:
        str: 日期字符串 (YYYY-MM-DD)
    """
    current_year = int(time.strftime('%Y'))
    
    # 计算出生年份范围
    max_birth_year = current_year - min_age
    min_birth_year = current_year - max_age
    
    year = random.randint(min_birth_year, max_birth_year)
    month = random.randint(1, 12)
    
    # 根据月份确定最大天数
    if month in [1, 3, 5, 7, 8, 10, 12]:
        max_day = 31
    elif month in [4, 6, 9, 11]:
        max_day = 30
    else:  # 2月
        # 简化处理：假设最多28天
        max_day = 28
    
    day = random.randint(1, max_day)
    
    return f"{year}-{month:02d}-{day:02d}"


def generate_phone_number(area_code: str = None) -> str:
    """
    生成美国电话号码
    
    Args:
        area_code: 可选的区号（3位数）
    
    Returns:
        str: 电话号码 (xxx-xxx-xxxx 格式)
    """
    if not area_code:
        # 常见的美国区号
        area_codes = [
            "212", "213", "310", "312", "404", "415", "512", "617", 
            "702", "713", "818", "917", "949", "206", "303", "469",
        ]
        area_code = random.choice(area_codes)
    
    # 生成中间三位和后四位
    middle = random.randint(200, 999)
    last = random.randint(1000, 9999)
    
    return f"{area_code}-{middle}-{last}"


def generate_address(state: str = None) -> dict:
    """
    生成美国地址
    
    Args:
        state: 可选的州代码
    
    Returns:
        dict: 地址信息
    """
    street_types = ["St", "Ave", "Blvd", "Dr", "Ln", "Way", "Ct", "Pl"]
    street_names = [
        "Main", "Oak", "Park", "Cedar", "Elm", "Washington", "Lake",
        "Hill", "Maple", "Pine", "University", "College", "Campus",
    ]
    
    states_cities = {
        "CA": ["Los Angeles", "San Francisco", "San Diego", "Berkeley", "Palo Alto"],
        "NY": ["New York", "Buffalo", "Albany", "Syracuse", "Rochester"],
        "TX": ["Austin", "Houston", "Dallas", "San Antonio", "College Station"],
        "MA": ["Boston", "Cambridge", "Worcester", "Springfield"],
        "WA": ["Seattle", "Bellevue", "Tacoma", "Spokane"],
        "IL": ["Chicago", "Evanston", "Urbana", "Springfield"],
        "PA": ["Philadelphia", "Pittsburgh", "State College"],
        "FL": ["Miami", "Orlando", "Tampa", "Gainesville"],
    }
    
    if not state:
        state = random.choice(list(states_cities.keys()))
    
    city = random.choice(states_cities.get(state, ["Unknown City"]))
    
    return {
        "street": f"{random.randint(100, 9999)} {random.choice(street_names)} {random.choice(street_types)}",
        "city": city,
        "state": state,
        "zip": f"{random.randint(10000, 99999)}",
    }
