"""
DeviceIdentity — 不可变的设备身份

绑定到特定 verificationId 的完整设备身份，包含全部指纹信号。
"""

import base64
import json
import time
import uuid
from dataclasses import dataclass, field

from .catalog import DeviceProfile

# ============================================================
# SheerID 配置常量 (定期检查更新)
# ============================================================

# jslib 版本号，来源: https://cdn.jsdelivr.net/npm/@sheerid/jslib@2/sheerid-install.js
# SheerID 服务端可能检查此值与 jslib 实际版本是否匹配
# 最后验证: 2026-02-28, 建议每月检查一次
SHEERID_CLIENT_VERSION = "2.190.0"
SHEERID_CLIENT_NAME = "jslib"

# NewRelic 追踪配置 (从 SheerID 页面的 NREUM 配置中提取)
# 这些值对应 SheerID 的 NewRelic 账户，不匹配可能导致追踪异常
# 最后验证: 2026-02-28
NEWRELIC_ACCOUNT_ID = "364029"
NEWRELIC_APP_ID = "134291347"

# SheerID 服务端点
SHEERID_ORIGIN = "https://services.sheerid.com"



@dataclass(frozen=True)
class DeviceIdentity:
    """不可变的设备身份，绑定到特定 verificationId"""

    # 来源标识
    verification_id: str
    device: DeviceProfile

    # Chrome 版本
    chrome_version: str        # 完整版本号 (如 "131.0.6778.140")
    impersonate_key: str       # curl_cffi impersonate 键 (如 "chrome131")

    # 时区
    timezone_name: str
    timezone_offset: int

    # === 指纹信号 ===
    canvas_hash: str
    webgl_vendor: str
    webgl_renderer: str
    audio_fingerprint: str
    screen_width: int
    screen_height: int
    color_depth: int
    pixel_ratio: float
    language: str
    platform: str
    cpu_cores: int
    device_memory: int
    max_touch_points: int
    session_id: str

    # === 衍生值 ===
    webgl_hash: str
    font_hash: str
    fingerprint_hash: str  # 最终的 deviceFingerprintHash

    # 生成的 User-Agent
    user_agent: str
    sec_ch_ua: str
    sec_ch_ua_platform: str

    # === NewRelic 追踪 (同一身份复用 trace_id) ===
    _trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:32], repr=False)
    _span_counter: int = field(default=0, repr=False)

    def get_headers(self, for_sheerid: bool = True) -> dict:
        """
        生成与此设备身份完全一致的 HTTP 请求头。

        所有请求头与指纹中的设备信号自洽：
        - User-Agent ↔ platform ↔ sec-ch-ua-platform
        - Chrome 版本 ↔ sec-ch-ua
        """
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": f"{self.language},en;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "sec-ch-ua": self.sec_ch_ua,
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": self.sec_ch_ua_platform,
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": self.user_agent,
        }

        if for_sheerid:
            nr_headers = self._generate_newrelic_headers()
            headers.update({
                "content-type": "application/json",
                "clientversion": SHEERID_CLIENT_VERSION,
                "clientname": SHEERID_CLIENT_NAME,
                "origin": SHEERID_ORIGIN,
                "referer": f"{SHEERID_ORIGIN}/",
                **nr_headers,
            })

        return headers

    def _generate_newrelic_headers(self) -> dict:
        """
        生成 NewRelic 追踪头。

        同一 DeviceIdentity 复用 trace_id (模拟同一页面加载),
        span_id 每次递增 (模拟同一 trace 下的不同 span)。
        """
        # 使用 object.__setattr__ 绕过 frozen dataclass 限制更新计数器
        current = self._span_counter
        object.__setattr__(self, '_span_counter', current + 1)

        span_id = uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f"{self._trace_id}:{current}"
        ).hex[:16]
        timestamp = int(time.time() * 1000)

        payload = {
            "v": [0, 1],
            "d": {
                "ty": "Browser",
                "ac": NEWRELIC_ACCOUNT_ID,
                "ap": NEWRELIC_APP_ID,
                "id": span_id,
                "tr": self._trace_id,
                "ti": timestamp,
            },
        }

        return {
            "newrelic": base64.b64encode(json.dumps(payload).encode()).decode(),
            "traceparent": f"00-{self._trace_id}-{span_id}-01",
            "tracestate": f"{NEWRELIC_ACCOUNT_ID}@nr=0-1-{NEWRELIC_ACCOUNT_ID}-{NEWRELIC_APP_ID}-{span_id}----{timestamp}",
        }

    def __str__(self) -> str:
        return (
            f"DeviceIdentity(\n"
            f"  vid={self.verification_id[:16]}...\n"
            f"  device={self.device.brand} {self.device.model} [{self.device.config_label}]\n"
            f"  platform={self.platform}\n"
            f"  screen={self.screen_width}x{self.screen_height}@{self.pixel_ratio}x\n"
            f"  cores={self.cpu_cores}, mem={self.device_memory}GB\n"
            f"  tz={self.timezone_name} (UTC{self.timezone_offset:+d})\n"
            f"  chrome={self.chrome_version} (impersonate={self.impersonate_key})\n"
            f"  fingerprint={self.fingerprint_hash}\n"
            f")"
        )
