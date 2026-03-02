"""
document_obfuscation — 文档混淆包

提供可插拔的文档混淆流水线，对调用方透明：
  - ObfuscationConfig  — 混淆开关与参数配置
  - ObfuscationPipeline — 流水线编排，应用各效果
  - DEFAULT_CONFIG     — 默认配置（全部效果启用）

使用方式：
    from .document_obfuscation import ObfuscationConfig, DEFAULT_CONFIG
    # 在 image_to_format() 内部通过 pipeline.apply(img) 透明应用
"""

from .config import DEFAULT_CONFIG, ObfuscationConfig
from .pipeline import ObfuscationPipeline

__all__ = ["ObfuscationConfig", "ObfuscationPipeline", "DEFAULT_CONFIG"]
