"""共享 fixtures for device_fingerprint_factory 测试

修改或使用默认SAMPLE_VID后运行以下命令进行测试
pytest tests/common/device_fingerprint_factory/test_verifier_integration.py::TestVerifierFingerprintFlow::test_full_flow -v --log-cli-level=DEBUG

"""

import pytest

from device_fingerprint_factory import DeviceIdentityFactory, DeviceIdentity


SAMPLE_VID = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
SAMPLE_VID_ALT = "f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3"


@pytest.fixture
def factory() -> DeviceIdentityFactory:
    """DeviceIdentityFactory 实例"""
    return DeviceIdentityFactory()


@pytest.fixture
def sample_identity(factory: DeviceIdentityFactory) -> DeviceIdentity:
    """预生成的 DeviceIdentity 实例"""
    return factory.create(SAMPLE_VID)
