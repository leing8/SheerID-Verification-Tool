"""
document_obfuscation.effects.crop — 边缘裁剪效果（待实现）

占位模块，接口已定义，实现留空。
后续实现时在此模块内完成，pipeline.py 无需修改。
"""

import random

from PIL import Image


def apply_crop(
    img: Image.Image,
    rng: random.Random,
    doc_type: str = "",
) -> Image.Image:
    """
    边缘裁剪效果主入口（当前未实现）。

    Args:
        img:      输入 PIL 图像（RGB）。
        rng:      确定性随机数生成器。
        doc_type: 文档类型字符串。

    Returns:
        原图（未做任何改动）。
    """
    # TODO: 实现边缘裁剪效果
    # 设计思路：
    #   - 四边独立随机裁剪 0~15px（模拟手机未完全对准纸张）
    #   - 裁剪后 resize 回原尺寸（LANCZOS）
    #   - 安全约束：裁剪总量不超过图像宽/高的 10%
    return img
