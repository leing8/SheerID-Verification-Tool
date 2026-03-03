"""
document_obfuscation — 文档混淆包

提供可插拔的文档混淆流水线，对调用方透明：
  - ObfuscationConfig   — 混淆开关与参数配置
  - ObfuscationPipeline — 流水线编排，应用各效果
  - DEFAULT_CONFIG      — 默认配置（全部效果启用）
  - SafeZone            — 通用核心数据保护区（任何文档类型均可使用）

使用方式：
    from .document_obfuscation import ObfuscationConfig, SafeZone, DEFAULT_CONFIG
    zones = [SafeZone(x1=70, y1=185, x2=700, y2=270, label="address")]
    pipeline = ObfuscationPipeline(rng, safe_zones=zones)
"""

from .config import DEFAULT_CONFIG, ObfuscationConfig
from .pipeline import ObfuscationPipeline
from .safe_zone import SafeZone

__all__ = ["ObfuscationConfig", "ObfuscationPipeline", "DEFAULT_CONFIG", "SafeZone"]
