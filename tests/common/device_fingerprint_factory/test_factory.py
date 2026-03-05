"""DeviceIdentityFactory 核心测试

覆盖:
- 返回类型
- 确定性输出 (同一 vid → 相同结果)
- 不同 vid → 不同指纹
- 品牌过滤
- 空 vid 异常
- 关键日志输出验证
"""

import logging

import pytest
from device_fingerprint_factory import DeviceIdentityFactory, DeviceIdentity
from device_fingerprint_factory.catalog import DEVICES_BY_BRAND

SAMPLE_VID = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
SAMPLE_VID_ALT = "f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3"


class TestFactoryCreate:
    """factory.create() 基本行为"""

    def test_create_returns_device_identity(
        self, factory: DeviceIdentityFactory
    ) -> None:
        """返回类型为 DeviceIdentity"""
        identity = factory.create(SAMPLE_VID)
        assert isinstance(identity, DeviceIdentity)

    def test_deterministic_output(
        self, factory: DeviceIdentityFactory
    ) -> None:
        """同一 vid 两次调用产生完全相同的结果"""
        id1 = factory.create(SAMPLE_VID)
        id2 = factory.create(SAMPLE_VID)

        assert id1.fingerprint_hash == id2.fingerprint_hash
        assert id1.user_agent == id2.user_agent
        assert id1.canvas_hash == id2.canvas_hash
        assert id1.audio_fingerprint == id2.audio_fingerprint
        assert id1.session_id == id2.session_id
        assert id1.device.brand == id2.device.brand
        assert id1.device.model == id2.device.model
        assert id1.timezone_name == id2.timezone_name
        assert id1.impersonate_key == id2.impersonate_key

    def test_different_vid_different_result(
        self, factory: DeviceIdentityFactory
    ) -> None:
        """不同 vid 产生不同的指纹哈希"""
        id1 = factory.create(SAMPLE_VID)
        id2 = factory.create(SAMPLE_VID_ALT)
        assert id1.fingerprint_hash != id2.fingerprint_hash

    def test_empty_vid_raises_value_error(
        self, factory: DeviceIdentityFactory
    ) -> None:
        """空 vid 抛出 ValueError"""
        with pytest.raises(ValueError, match="不能为空"):
            factory.create("")

    def test_none_vid_raises_value_error(
        self, factory: DeviceIdentityFactory
    ) -> None:
        """None vid 也应被拒绝 (falsycheck)"""
        with pytest.raises((ValueError, TypeError)):
            factory.create(None)  # type: ignore[arg-type]


class TestFactoryBrandFilter:
    """品牌过滤功能"""

    @pytest.mark.parametrize("brand", ["dell", "Dell", "DELL"])
    def test_brand_filter_case_insensitive(
        self, factory: DeviceIdentityFactory, brand: str
    ) -> None:
        """品牌过滤不区分大小写"""
        identity = factory.create(SAMPLE_VID, brand=brand)
        assert identity.device.brand.lower() == "dell"

    def test_brand_filter_apple(
        self, factory: DeviceIdentityFactory
    ) -> None:
        """指定 apple 品牌只返回 Apple 设备"""
        identity = factory.create(SAMPLE_VID, brand="apple")
        assert identity.device.brand == "Apple"

    def test_unknown_brand_falls_back(
        self, factory: DeviceIdentityFactory
    ) -> None:
        """未知品牌回退到全部设备池"""
        identity = factory.create(SAMPLE_VID, brand="unknown_brand_xyz")
        assert isinstance(identity, DeviceIdentity)


class TestFactoryLogging:
    """验证关键日志消息"""

    def test_info_logs_on_create(
        self, factory: DeviceIdentityFactory, caplog: pytest.LogCaptureFixture
    ) -> None:
        """create() 产生 INFO 级别日志"""
        with caplog.at_level(logging.INFO, logger="device_fingerprint_factory.factory"):
            factory.create(SAMPLE_VID)

        messages = caplog.text
        # 入口日志
        assert "开始生成设备身份" in messages
        assert SAMPLE_VID[:16] in messages
        # 步骤1: 设备选择
        assert "[步骤1/8] 设备选择" in messages
        # 步骤7: 指纹哈希
        assert "[步骤7/8] 指纹哈希" in messages
        # 步骤8: 创建完成
        assert "[步骤8/8] DeviceIdentity 创建完成" in messages

    def test_debug_logs_detail(
        self, factory: DeviceIdentityFactory, caplog: pytest.LogCaptureFixture
    ) -> None:
        """DEBUG 级别包含详细信号信息"""
        with caplog.at_level(logging.DEBUG, logger="device_fingerprint_factory.factory"):
            factory.create(SAMPLE_VID)

        messages = caplog.text
        assert "[步骤2/8] 时区选择" in messages
        assert "[步骤3/8] Chrome 版本" in messages
        assert "[步骤4/8] 设备唯一键" in messages
        assert "[步骤5/8] 信号生成" in messages
        assert "[步骤6/8] User-Agent" in messages

    def test_signals_module_logging(
        self, factory: DeviceIdentityFactory, caplog: pytest.LogCaptureFixture
    ) -> None:
        """signals 模块产生 DEBUG 日志"""
        with caplog.at_level(logging.DEBUG, logger="device_fingerprint_factory.signals"):
            factory.create(SAMPLE_VID)

        messages = caplog.text
        assert "Chrome 版本选择" in messages
        assert "指纹哈希计算" in messages
        assert "指纹哈希结果" in messages

    def test_timezone_module_logging(
        self, factory: DeviceIdentityFactory, caplog: pytest.LogCaptureFixture
    ) -> None:
        """us_timezones 模块产生 DEBUG 日志"""
        with caplog.at_level(logging.DEBUG, logger="device_fingerprint_factory.us_timezones"):
            factory.create(SAMPLE_VID)

        messages = caplog.text
        assert "时区选择" in messages
        assert "DST 判定" in messages
