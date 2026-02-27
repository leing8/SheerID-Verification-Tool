"""
proxy_checker.models — 数据模型

定义代理检测相关的所有结构化数据类型。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ProxyType(str, Enum):
    """代理类型"""
    RESIDENTIAL = "residential"
    DATACENTER = "datacenter"
    MOBILE = "mobile"
    ISP = "isp"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class ProxyInfo:
    """代理基本信息"""
    url: str
    protocol: str = "http"
    host: str = ""
    port: int = 0
    username: Optional[str] = None
    password: Optional[str] = None


@dataclass
class GeoResult:
    """地理位置检测结果"""
    ip: str = "unknown"
    country: str = "unknown"
    city: str = "unknown"
    region: str = ""
    org: str = ""
    timezone: str = ""


@dataclass
class ReputationResult:
    """代理纯净度 / 属性评估"""
    proxy_type: ProxyType = ProxyType.UNKNOWN
    is_datacenter: bool = False
    risk_level: RiskLevel = RiskLevel.MEDIUM
    provider: str = ""


@dataclass
class ProxyCheckResult:
    """完整的代理检测结果"""
    geo: GeoResult = field(default_factory=GeoResult)
    reputation: ReputationResult = field(default_factory=ReputationResult)
    is_country_match: bool = False
    expected_country: str = ""
    latency_ms: float = 0.0
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        """代理是否通过基本检测（国家匹配 + 非数据中心）"""
        return self.is_country_match and not self.reputation.is_datacenter
