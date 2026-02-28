"""
conftest.py — pytest 共享 fixtures

环境配置:
    pythonpath 在 pyproject.toml 中设置为 ["common"]，
    common/ 下的包可以直接 import，无需 sys.path hack。

使用方法:
    # ── 安装依赖 ──
    pip install -e ".[dev]"              # 推荐
    pip install -r requirements.txt      # 或使用 requirements.txt

    # ── 运行全部测试 ──
    pytest                               # 全部测试（简洁输出）
    pytest -v                            # 全部测试（详细输出）
    pytest -v -s                         # 全部测试（含 print 输出）

    # ── 按模块运行 ──
    pytest tests/common/device_fingerprint_factory/ -v -s    # 设备指纹工厂
    pytest tests/common/student_document_factory/ -v -s      # 学生文档工厂
    pytest tests/common/proxy_checker/ -v -s                 # 代理检测器

    # ── 运行单个测试文件 ──
    pytest tests/common/device_fingerprint_factory/test_verbose_output.py -v -s
    pytest tests/common/student_document_factory/test_verbose_output.py -v -s
    pytest tests/common/proxy_checker/test_verbose_output.py -v -s

    # ── 运行单个测试类 / 方法 ──
    pytest tests/.../test_factory.py::TestDeterministicGeneration -v
    pytest tests/.../test_factory.py::TestDeterministicGeneration::test_same_vid_produces_identical_hash -v

    # ── 自定义参数 ──
    --vid=<verification_id>              # 指定测试用的 verificationId
                                         # 未指定时使用默认值
    --proxy=<proxy_url>                  # 指定实时代理（用于 test_live_proxy.py）
                                         # 未指定时跳过实时测试

    # 示例:
    pytest tests/common/device_fingerprint_factory/ -v -s --vid=67890abcdef1234567890123
    pytest tests/common/student_document_factory/test_verbose_output.py -v -s --vid=my-vid-001
    pytest tests/common/proxy_checker/test_live_proxy.py -v -s --proxy="http://user:pass@host:port"

    # ── 覆盖率报告 ──
    pytest --cov=common --cov-report=term-missing
"""

import pytest


def pytest_addoption(parser):
    """注册自定义命令行参数"""
    parser.addoption(
        "--vid",
        action="store",
        default=None,
        help="指定测试用的 verificationId（默认使用内置固定值）",
    )
    parser.addoption(
        "--proxy",
        action="store",
        default=None,
        help="指定实时代理地址，用于 test_live_proxy.py（如 http://user:pass@host:port）",
    )


@pytest.fixture
def factory():
    """返回 DeviceIdentityFactory 实例"""
    from device_fingerprint_factory import DeviceIdentityFactory
    return DeviceIdentityFactory()


@pytest.fixture
def sample_vid(request):
    """返回测试 verificationId（优先使用 --vid 命令行参数）"""
    vid = request.config.getoption("--vid")
    return vid if vid else "abc123def456789012345678"


@pytest.fixture
def sample_identity(factory, sample_vid):
    """返回一个固定的 DeviceIdentity 实例"""
    return factory.create(sample_vid)

