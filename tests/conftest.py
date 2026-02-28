"""
conftest.py — pytest 共享 fixtures

pythonpath 配置在 pyproject.toml 中:
    [tool.pytest.ini_options]
    pythonpath = ["common"]

这使得 common/ 下的包可以直接 import，无需 sys.path hack。
"""

import pytest


@pytest.fixture
def factory():
    """返回 DeviceIdentityFactory 实例"""
    from device_fingerprint_factory import DeviceIdentityFactory
    return DeviceIdentityFactory()


@pytest.fixture
def sample_vid():
    """返回一个固定的测试 verificationId"""
    return "abc123def456789012345678"


@pytest.fixture
def sample_identity(factory, sample_vid):
    """返回一个固定的 DeviceIdentity 实例"""
    return factory.create(sample_vid)
