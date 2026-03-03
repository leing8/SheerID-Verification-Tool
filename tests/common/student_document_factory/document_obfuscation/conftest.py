"""
tests/common/student_document_factory/document_obfuscation/conftest.py

document_obfuscation 子目录专属 fixtures。
上层 conftest.py（student_document_factory/conftest.py）中定义的
sample_vid、make_rng、white_canvas、colored_canvas 均在此自动继承可用。
"""

import pytest

# 共享工具函数（供视觉测试使用；定义在业务模块，测试按需导入）
from student_document_factory.document_obfuscation.effects.utils import (
    to_uint8,   # float32 数组 → uint8（clip + astype）
)


# ── document_obfuscation 专属 fixtures ──────────────────────────────────────

@pytest.fixture
def paper_canvas():
    """模拟纸质文档底板（象牙色，640×400 RGB）——更贴近真实文档颜色"""
    from PIL import Image
    return Image.new("RGB", (640, 400), color=(250, 248, 240))


@pytest.fixture
def transcript_canvas():
    """模拟成绩单底板（浅灰白，640×400 RGB）"""
    from PIL import Image
    return Image.new("RGB", (640, 400), color=(245, 245, 242))
