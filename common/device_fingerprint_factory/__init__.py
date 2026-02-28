"""
device_fingerprint_factory — 设备指纹工厂

基于真实设备数据和 verificationId 确定性生成浏览器指纹。
可供多个项目复用。

用法:
    from device_fingerprint_factory import DeviceIdentityFactory

    factory = DeviceIdentityFactory()
    identity = factory.create("your-verification-id")

    # 获取指纹哈希 (用于 SheerID API 的 deviceFingerprintHash)
    print(identity.fingerprint_hash)

    # 获取一致的请求头
    headers = identity.get_headers(for_sheerid=True)

    # 同一 verificationId 始终返回相同结果
    identity2 = factory.create("your-verification-id")
    assert identity.fingerprint_hash == identity2.fingerprint_hash
"""

from .catalog import ALL_DESKTOP_DEVICES, ALL_DEVICES, ALL_MOBILE_DEVICES, DeviceProfile
from .factory import DeviceIdentityFactory
from .identity import DeviceIdentity

__all__ = [
    "DeviceIdentityFactory",
    "DeviceIdentity",
    "DeviceProfile",
    "ALL_DEVICES",
    "ALL_DESKTOP_DEVICES",
    "ALL_MOBILE_DEVICES",
]
