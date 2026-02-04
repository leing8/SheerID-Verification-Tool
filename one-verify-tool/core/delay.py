"""
延迟模块 - 人类化延迟函数

包含:
- random_delay: 人类化随机延迟（Gamma 分布）
- typing_delay: 打字延迟
- reading_delay: 阅读延迟
- interaction_delay: 交互延迟
- get_human_delay_pattern: 获取人类化延迟模式
"""

import time
import random
from typing import Tuple

from .constants import (
    MIN_DELAY, MAX_DELAY,
    TYPING_MIN_DELAY, TYPING_MAX_DELAY,
    PAGE_READ_DELAY,
)


def random_delay(min_ms: int = None, max_ms: int = None, use_gamma: bool = True) -> float:
    """
    人类化随机延迟（Gamma 分布）
    
    Gamma 分布比均匀随机更接近人类反应时间，
    大部分延迟集中在较短时间，偶尔有较长延迟。
    
    Args:
        min_ms: 最小延迟（毫秒），默认使用配置值
        max_ms: 最大延迟（毫秒），默认使用配置值
        use_gamma: 是否使用 Gamma 分布（更人类化）
    
    Returns:
        float: 实际延迟秒数
    """
    min_ms = min_ms or MIN_DELAY
    max_ms = max_ms or MAX_DELAY
    
    if use_gamma:
        try:
            import numpy as np
            # Gamma 分布参数：shape=2 产生右偏分布
            shape, scale = 2.0, (max_ms - min_ms) / 4000
            delay = min_ms / 1000 + np.random.gamma(shape, scale)
            delay = min(delay, max_ms / 1000)
        except ImportError:
            # 无 numpy 时使用模拟的右偏分布
            delay = _simulate_gamma_delay(min_ms, max_ms)
    else:
        delay = random.randint(min_ms, max_ms) / 1000
    
    # 添加微小随机波动（模拟真实人类行为）
    jitter = random.uniform(-0.02, 0.05)
    delay = max(min_ms / 1000, delay + jitter)
    
    time.sleep(delay)
    return delay


def _simulate_gamma_delay(min_ms: int, max_ms: int) -> float:
    """无 numpy 时模拟 Gamma 分布"""
    # 使用多个均匀随机数的和来近似 Gamma 分布
    samples = [random.random() for _ in range(3)]
    normalized = sum(samples) / 3
    # 偏向较小值
    skewed = normalized ** 1.5
    delay = min_ms / 1000 + skewed * (max_ms - min_ms) / 1000
    return delay


def typing_delay(char_count: int = 1) -> float:
    """
    模拟打字延迟
    
    人类打字速度大约 40-80 WPM (每分钟字数)，
    每个字符约 100-300ms，但会有自然的波动。
    
    Args:
        char_count: 字符数量
    
    Returns:
        float: 总延迟秒数
    """
    total_delay = 0
    
    for i in range(char_count):
        # 基础延迟
        base_delay = random.randint(TYPING_MIN_DELAY, TYPING_MAX_DELAY) / 1000
        
        # 偶尔暂停（模拟思考或按错键）
        if random.random() < 0.05:
            base_delay += random.uniform(0.2, 0.5)
        
        # 连续打字加速
        if i > 3:
            base_delay *= random.uniform(0.8, 1.0)
        
        total_delay += base_delay
    
    time.sleep(total_delay)
    return total_delay


def reading_delay(content_length: int = 100) -> float:
    """
    模拟阅读页面的延迟
    
    人类阅读速度约 200-300 WPM，
    但会因内容复杂度而变化。
    
    Args:
        content_length: 内容大致字符数
    
    Returns:
        float: 实际延迟秒数
    """
    # 估算阅读时间（每个单词约 250ms）
    word_count = content_length / 5
    base_time = word_count * 0.25
    
    # 最小/最大阅读时间
    min_read, max_read = PAGE_READ_DELAY
    delay = max(min_read / 1000, min(max_read / 1000, base_time))
    
    # 添加随机波动
    delay *= random.uniform(0.8, 1.2)
    
    time.sleep(delay)
    return delay


def interaction_delay(action_type: str = "click") -> float:
    """
    模拟用户交互延迟
    
    不同交互动作有不同的典型延迟：
    - click: 200-500ms
    - scroll: 300-800ms
    - focus: 100-300ms
    - submit: 500-1500ms (思考确认)
    
    Args:
        action_type: 交互类型
    
    Returns:
        float: 实际延迟秒数
    """
    delays = {
        "click": (200, 500),
        "scroll": (300, 800),
        "focus": (100, 300),
        "submit": (500, 1500),
        "navigation": (300, 700),
        "form_field": (150, 400),
    }
    
    min_ms, max_ms = delays.get(action_type, (200, 500))
    return random_delay(min_ms, max_ms)


def get_human_delay_pattern() -> dict:
    """
    获取人类化延迟模式配置
    
    根据一天中的时间返回不同的延迟配置，
    模拟真实用户行为模式。
    
    Returns:
        dict: 延迟配置
    """
    hour = time.localtime().tm_hour
    
    # 根据时间段调整延迟
    if 9 <= hour <= 17:
        # 工作时间：较快的操作
        return {
            "base_multiplier": 0.9,
            "typing_speed": "fast",
            "pause_probability": 0.03,
        }
    elif 18 <= hour <= 23:
        # 晚间：正常速度
        return {
            "base_multiplier": 1.0,
            "typing_speed": "normal",
            "pause_probability": 0.05,
        }
    else:
        # 深夜/早晨：较慢
        return {
            "base_multiplier": 1.2,
            "typing_speed": "slow",
            "pause_probability": 0.08,
        }


def wait_between_requests(request_count: int) -> float:
    """
    请求间等待，避免被检测为机器人
    
    第一个请求后延迟较短，随着请求增加延迟变长。
    
    Args:
        request_count: 当前请求数
    
    Returns:
        float: 实际延迟秒数
    """
    # 基础延迟随请求数增加
    base = MIN_DELAY + (request_count * 100)
    max_delay = min(MAX_DELAY, base + 500)
    
    return random_delay(base, max_delay)


def simulate_form_fill_timing(field_count: int) -> list:
    """
    模拟表单填写的时序
    
    返回每个字段的延迟列表，模拟真实用户填写表单的节奏。
    
    Args:
        field_count: 表单字段数
    
    Returns:
        list: 每个字段的延迟秒数列表
    """
    delays = []
    
    for i in range(field_count):
        # 第一个字段：较长延迟（阅读表单）
        if i == 0:
            delay = random.uniform(1.0, 2.5)
        # 最后一个字段：较长延迟（检查提交前）
        elif i == field_count - 1:
            delay = random.uniform(0.8, 1.5)
        else:
            # 中间字段：正常延迟
            delay = random.uniform(0.3, 0.8)
        
        delays.append(delay)
    
    return delays
