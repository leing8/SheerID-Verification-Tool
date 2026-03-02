"""
document_obfuscation.effects.transform_3d — 3D 透视变换效果（待实现）

占位模块，接口已定义，实现留空。
后续实现时在此模块内完成，pipeline.py 无需修改。
"""

import random

from PIL import Image


def apply_transform_3d(
    img: Image.Image,
    rng: random.Random,
    doc_type: str = "",
) -> Image.Image:
    """
    3D 透视变换效果主入口（当前未实现）。

    Args:
        img:      输入 PIL 图像（RGB）。
        rng:      确定性随机数生成器。
        doc_type: 文档类型字符串。

    Returns:
        原图（未做任何改动）。
    """
    # TODO: 实现 3D 透视变换效果
    # 设计思路：
    #   - 四角独立微偏移（±6px）模拟纸张不平整 / 拍摄角度
    #   - 加上轻微旋转（±1.5°）模拟手机未完全对齐
    #   - PIL PERSPECTIVE 变换 + BICUBIC 插值
    #   - 边缘填充白色（255, 255, 255）
    return img
