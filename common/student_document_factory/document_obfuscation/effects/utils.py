"""
document_obfuscation.effects.utils — 效果模块共享工具函数

供 stains.py、creases.py 等效果模块复用的底层工具。
所有函数均为纯计算，无副作用，不依赖全局状态。
"""

import random
from typing import TYPE_CHECKING

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
