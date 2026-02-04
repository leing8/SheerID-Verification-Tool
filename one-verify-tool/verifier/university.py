"""
大学选择模块 - 加权随机选择大学

包含:
- select_university: 根据权重和代理位置选择大学
- FraudTracker: 欺诈记录追踪
"""

import random
import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field

from data import UNIVERSITIES
from stats import stats


@dataclass
class FraudRecord:
    """欺诈记录"""
    university_name: str
    timestamp: float
    error_type: str = "fraudRulesReject"


class FraudTracker:
    """
    欺诈记录追踪器
    
    追踪触发欺诈检测的大学，降低高风险大学的选择权重。
    """
    
    def __init__(self):
        self.records: List[FraudRecord] = []
        self.cooldown_hours = 24
    
    def record_fraud(self, university_name: str, error_type: str = "fraudRulesReject"):
        """记录欺诈触发"""
        self.records.append(FraudRecord(
            university_name=university_name,
            timestamp=time.time(),
            error_type=error_type,
        ))
        print(f"[欺诈追踪] 记录: {university_name} ({error_type})")
    
    def get_fraud_count(self, university_name: str, hours: int = 24) -> int:
        """获取指定时间段内的欺诈次数"""
        cutoff = time.time() - (hours * 3600)
        return sum(
            1 for r in self.records
            if r.university_name == university_name and r.timestamp > cutoff
        )
    
    def get_weight_modifier(self, university_name: str) -> float:
        """
        获取权重修正系数
        
        欺诈次数越多，权重越低
        """
        fraud_count = self.get_fraud_count(university_name)
        
        if fraud_count == 0:
            return 1.0
        elif fraud_count == 1:
            return 0.5
        elif fraud_count == 2:
            return 0.2
        else:
            return 0.05  # 几乎不选择
    
    def get_high_risk_universities(self) -> List[str]:
        """获取高风险大学列表"""
        return [
            r.university_name for r in self.records
            if self.get_fraud_count(r.university_name) >= 2
        ]
    
    def cleanup_old_records(self, hours: int = 72):
        """清理旧记录"""
        cutoff = time.time() - (hours * 3600)
        self.records = [r for r in self.records if r.timestamp > cutoff]


# 全局欺诈追踪器
fraud_tracker = FraudTracker()


def select_university(
    proxy_country: str = None,
    proxy_state: str = None,
    exclude_names: List[str] = None,
) -> Dict:
    """
    加权随机选择大学，支持代理位置匹配
    
    根据以下因素计算权重:
    1. 大学预设权重（美国学校更高）
    2. 历史成功率（成功率越高权重越大）
    3. 代理位置匹配（优先选择匹配国家/州的大学）
    4. 欺诈记录（触发欺诈的大学权重降低）
    
    Args:
        proxy_country: 代理所在国家代码（如 "US", "CA"）
        proxy_state: 代理所在州代码（如 "CA", "NY"）
        exclude_names: 排除的大学名称列表
    
    Returns:
        Dict: 选中的大学信息
    """
    exclude_names = exclude_names or []
    
    # 筛选大学列表
    available_unis = [u for u in UNIVERSITIES if u["name"] not in exclude_names]
    
    if not available_unis:
        available_unis = UNIVERSITIES
    
    # 按代理位置筛选
    if proxy_country and proxy_country != "unknown":
        matching_unis = [u for u in available_unis if u.get("country") == proxy_country]
        
        if matching_unis:
            print(f"[信息] 根据代理位置 {proxy_country} 筛选到 {len(matching_unis)} 所匹配的大学")
            
            # 如果有州信息，进一步筛选
            if proxy_state:
                state_unis = [u for u in matching_unis if u.get("state") == proxy_state]
                if state_unis:
                    print(f"[信息] 根据州 {proxy_state} 进一步筛选到 {len(state_unis)} 所大学")
                    available_unis = state_unis
                else:
                    available_unis = matching_unis
            else:
                available_unis = matching_unis
        else:
            print(f"[警告] 未找到 {proxy_country} 的大学，使用全部列表")
    
    # 计算权重
    weights = []
    for uni in available_unis:
        # 基础权重
        base_weight = uni.get("weight", 50)
        
        # 成功率修正
        success_rate = stats.get_rate(uni["name"])
        rate_modifier = success_rate / 50  # 标准化到 1.0 左右
        
        # 欺诈记录修正
        fraud_modifier = fraud_tracker.get_weight_modifier(uni["name"])
        
        # 最终权重
        final_weight = base_weight * rate_modifier * fraud_modifier
        weights.append(max(1, final_weight))
    
    # 加权随机选择
    total = sum(weights)
    r = random.uniform(0, total)
    
    cumulative = 0
    for uni, weight in zip(available_unis, weights):
        cumulative += weight
        if r <= cumulative:
            print(f"[信息] 选择大学: {uni['name']} (权重: {weight:.1f})")
            return {**uni, "idExtended": str(uni["id"])}
    
    # 默认返回第一个
    return {**available_unis[0], "idExtended": str(available_unis[0]["id"])}


def validate_university_ip_match(university: Dict, ip_country: str, ip_state: str = None) -> Dict:
    """
    验证大学与 IP 位置的匹配度
    
    Args:
        university: 大学信息
        ip_country: IP 所在国家
        ip_state: IP 所在州（可选）
    
    Returns:
        Dict: 匹配评估结果
    """
    result = {
        "country_match": False,
        "state_match": False,
        "risk_level": "high",
        "recommendation": None,
    }
    
    uni_country = university.get("country", "")
    uni_state = university.get("state", "")
    
    if uni_country == ip_country:
        result["country_match"] = True
        result["risk_level"] = "medium"
        
        if ip_state and uni_state == ip_state:
            result["state_match"] = True
            result["risk_level"] = "low"
    
    if result["risk_level"] == "high":
        result["recommendation"] = f"建议使用 {uni_country} 的代理 IP"
    elif result["risk_level"] == "medium" and uni_state:
        result["recommendation"] = f"建议使用 {uni_state} 州的代理 IP 以降低风险"
    
    return result


def get_university_by_name(name: str) -> Optional[Dict]:
    """根据名称获取大学信息"""
    for uni in UNIVERSITIES:
        if uni["name"].lower() == name.lower():
            return {**uni, "idExtended": str(uni["id"])}
    return None


def get_universities_by_country(country: str) -> List[Dict]:
    """根据国家获取大学列表"""
    return [
        {**u, "idExtended": str(u["id"])}
        for u in UNIVERSITIES
        if u.get("country") == country
    ]
