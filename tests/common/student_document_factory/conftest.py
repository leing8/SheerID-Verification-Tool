"""共享 fixtures for student_document_factory 测试

运行以下命令进行测试（含文档输出到 tests/output/student_docs/）

修改或使用默认SAMPLE_VID后运行以下命令进行测试

全部测试：
  pytest tests/common/student_document_factory/ -v --log-cli-level=DEBUG

单个测试（查看完整调用链日志）：
  pytest tests/common/student_document_factory/test_verifier_integration.py::TestVerifierStudentFlow::test_full_flow -v --log-cli-level=DEBUG
  pytest tests/common/student_document_factory/test_verifier_integration.py::TestVerifierStudentFlow::test_save_all_verifier_documents -v --log-cli-level=DEBUG

  pytest tests/common/student_document_factory/test_factory.py::TestDocuments::test_save_all_documents -v --log-cli-level=DEBUG
  pytest tests/common/student_document_factory/test_documents.py::TestTranscript::test_save_to_output -v --log-cli-level=DEBUG
  pytest tests/common/student_document_factory/test_documents.py::TestInvoice::test_save_to_output -v --log-cli-level=DEBUG
  pytest tests/common/student_document_factory/test_documents.py::TestStudentId::test_save_to_output -v --log-cli-level=DEBUG
"""

import logging
from pathlib import Path

import pytest
from student_document_factory import StudentInfoFactory
from student_document_factory.document_obfuscation import ObfuscationConfig

logger = logging.getLogger(__name__)

# 输出目录（测试生成的文档保存于此，便于查看效果）
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output" / "student_docs"

# ============ 可配置区域（修改后直接运行测试即可查看效果）============

# 固定 vid 确保确定性（修改此值可生成不同学生）
SAMPLE_VID = "test-verification-id-12345678-abcdef2026-3-5 12:30:28"

# 混淆配置（默认全部关闭，仅查看原始文档内容）
# 如需查看某个混淆效果，将 enabled 设为 True 并开启对应效果：
#   enabled=True           总开关（必须为 True 才会应用下面的效果）
#   stains=True            污渍（mud / wear / fading）
#   creases=True           折痕
#   crop=True              边缘裁剪
#   transform_3d=True      3D 透视变换
#   background_scene=True  背景场景叠加（桌面 / 地毯等）

# OBFUSCATION_CONFIG = ObfuscationConfig(
#     enabled=False,
#     stains=False,
#     creases=False,
#     crop=False,
#     transform_3d=False,
#     background_scene=False,
# )

OBFUSCATION_CONFIG = ObfuscationConfig(
    enabled=True,
    stains=True,
    creases=True,
    crop=True,
    transform_3d=True,
    background_scene=True,
)


@pytest.fixture(scope="session", autouse=True)
def output_dir() -> Path:
    """创建输出目录"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


@pytest.fixture(autouse=True)
def disable_obfuscation():
    """
    测试时关闭文档混淆（利用 ObfuscationConfig.enabled=False）。

    由于 pythonpath=["common"]，模块可能以两个路径被加载到 sys.modules，
    导致 monkeypatch/patch 只修改其中一个副本。
    此处遍历 sys.modules 找到所有 common 模块副本，全部 patch。
    """
    import sys

    # 找到所有 common 模块副本并 patch
    originals = {}
    target_suffix = "student_document_factory.schools.harvard.documents.common"
    for name, mod in sys.modules.items():
        if name.endswith(target_suffix) and hasattr(mod, "DEFAULT_CONFIG"):
            originals[name] = mod.DEFAULT_CONFIG
            mod.DEFAULT_CONFIG = OBFUSCATION_CONFIG

    logger.debug("disable_obfuscation: patched %d module copies", len(originals))

    yield

    # 恢复
    for name, original in originals.items():
        if name in sys.modules:
            sys.modules[name].DEFAULT_CONFIG = original


@pytest.fixture
def factory() -> StudentInfoFactory:
    """StudentInfoFactory 实例"""
    return StudentInfoFactory()


@pytest.fixture
def sample_vid() -> str:
    """固定验证 ID"""
    return SAMPLE_VID


def save_document(doc_bytes: bytes, filename: str, label: str = "") -> Path:
    """
    保存生成的文档到输出目录，并记录日志。

    Args:
        doc_bytes: 文档字节数据
        filename:  文件名
        label:     附加标签（如 step_1, verifier_flow）
    Returns:
        保存路径
    """
    if label:
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        filename = f"{stem}_{label}{suffix}"

    path = OUTPUT_DIR / filename
    path.write_bytes(doc_bytes)

    logger.info(
        "📄 文档已保存: %s (%.1f KB) → %s",
        filename, len(doc_bytes) / 1024, path,
    )
    return path

