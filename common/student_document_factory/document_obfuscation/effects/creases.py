"""
document_obfuscation.effects.creases — 折痕效果（待实现）

占位模块，接口已定义，实现留空。
后续实现时在此模块内完成，pipeline.py 无需修改。
"""

import random

from PIL import Image


def apply_creases(
    img: Image.Image,
    rng: random.Random,
    doc_type: str = "",
) -> Image.Image:
    """
    折痕效果主入口（当前未实现）。

    Args:
        img:      输入 PIL 图像（RGB）。
        rng:      确定性随机数生成器。
        doc_type: 文档类型字符串。

    Returns:
        原图（未做任何改动）。
    """
    # TODO: 实现折痕效果
    # 设计思路：
    #   - 在图像边缘区域（距边 ≤ 15%）绘制1~2条半透明直线阴影
    #   - 水平折痕（near top/bottom）/ 垂直折痕（near left/right）
    #   - 线宽 3~8px，不透明度 0.05~0.15
    #   - 折痕两侧略有亮度差（模拟纸张折叠后光泽变化）
    return img
