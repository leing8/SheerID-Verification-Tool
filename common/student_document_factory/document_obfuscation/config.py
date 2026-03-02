"""
ObfuscationConfig — 文档混淆配置

frozen dataclass，所有字段均为开关或参数。
enabled=False 时整条流水线跳过，直接返回原图。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ObfuscationConfig:
    """
    文档混淆总控配置。

    Attributes:
        enabled:           总开关。False → 所有效果跳过，原图原样返回。
        stains:            污渍效果（mud / wear / fading）。
        creases:           折痕效果（当前未实现）。
        crop:              边缘裁剪效果（当前未实现）。
        transform_3d:      3D 透视变换效果（当前未实现）。
        photo_simulation:  拍照模拟（光照 / 噪声 / 模糊 / JPEG 重编码）。
    """

    enabled: bool = True
    stains: bool = True
    creases: bool = True
    crop: bool = True
    transform_3d: bool = True
    photo_simulation: bool = True


# 默认配置：全部效果启用
DEFAULT_CONFIG = ObfuscationConfig()

# 仅启用拍照模拟（无污渍等物理损坏）
PHOTO_ONLY_CONFIG = ObfuscationConfig(
    stains=False,
    creases=False,
    crop=False,
    transform_3d=False,
)

# 完全禁用（调试 / 测试用）
DISABLED_CONFIG = ObfuscationConfig(enabled=False)
