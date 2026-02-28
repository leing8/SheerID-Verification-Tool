"""
tests/common/device_fingerprint_factory/conftest.py

device_fingerprint_factory 专属 fixtures。
顶层 conftest.py 的 factory / sample_vid / sample_identity fixtures 在此继承可用。
"""

import pytest


@pytest.fixture
def all_devices():
    """返回完整设备列表"""
    from device_fingerprint_factory.catalog import ALL_DEVICES
    return ALL_DEVICES


@pytest.fixture
def devices_by_brand():
    """返回按品牌分组的设备字典"""
    from device_fingerprint_factory.catalog import DEVICES_BY_BRAND
    return DEVICES_BY_BRAND
