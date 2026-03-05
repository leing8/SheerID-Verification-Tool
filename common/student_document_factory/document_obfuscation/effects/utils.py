"""
document_obfuscation.effects.utils — 效果模块共享工具函数

供 stains.py、creases.py 等效果模块复用的底层工具。
所有函数均为纯计算，无副作用，不依赖全局状态。
"""

import functools
import random
from typing import TYPE_CHECKING

from PIL import Image

if TYPE_CHECKING:
    import numpy


def to_float32(arr: "numpy.ndarray") -> "numpy.ndarray":
    """将 numpy 数组转换为 float32（像素运算统一精度）"""
    return arr.astype("float32")


def to_uint8(arr: "numpy.ndarray") -> "numpy.ndarray":
    """将 float32 数组截断至 [0, 255] 并转换为 uint8"""
    import numpy as np
    return np.clip(arr, 0, 255).astype(np.uint8)


def make_rs(rng: random.Random) -> "numpy.random.RandomState":
    """
    从 Python random.Random 实例创建 numpy RandomState，保证确定性。

    用于需要 numpy 随机操作（如 normal 噪声）的效果模块；
    通过 rng.randint 将 Python RNG 的状态传递给 numpy，确保
    相同 seed 下产生相同的 numpy 随机序列。
    """
    import numpy as np
    return np.random.RandomState(rng.randint(0, 2 ** 31 - 1))


def preserve_alpha(fn):
    """
    Alpha 通道保留装饰器（Alpha Preservation Pattern）。

    用于仅修改 RGB 颜色/亮度、不应影响透明度的效果函数。
    装饰器自动完成：
      1. 保存 RGBA 图像的 alpha 通道
      2. 将图像转为 RGB 传给被装饰函数
      3. 从返回的 RGB 结果恢复 alpha 通道

    被装饰函数签名要求：第一个参数为 img: Image.Image，返回 Image.Image。

    物理依据：污渍/折痕只改变纸面颜色，不会让纸变透明——
    类似 Photoshop 的"锁定透明像素"功能。
    """
    @functools.wraps(fn)
    def wrapper(img: Image.Image, *args, **kwargs) -> Image.Image:
        original_alpha = None
        if img.mode == "RGBA":
            original_alpha = img.split()[3]
            img = img.convert("RGB")

        result = fn(img, *args, **kwargs)

        if original_alpha is not None:
            # 若效果改变了尺寸（如 crop），用原始 alpha 时需匹配尺寸
            if result.size == original_alpha.size:
                result = result.convert("RGBA")
                result.putalpha(original_alpha)
            else:
                # 尺寸不匹配，保持 RGB（如 crop 后不还原）
                pass
        return result
    return wrapper

