"""
DeviceIdentity — 不可变的设备身份

绑定到特定 verificationId 的完整设备身份，包含全部 15 项自洽指纹信号。
"""

import base64
import json
import time
import uuid
from dataclasses import dataclass

from .catalog import DeviceProfile


@dataclass(frozen=True)
class DeviceIdentity:
    """不可变的设备身份，绑定到特定 verificationId"""

    # 来源标识
    verification_id: str
    device: DeviceProfile

    # Chrome 版本
    chrome_version: str

    # 时区
    timezone_name: str
    timezone_offset: int

    # === 15 项信号 ===
    # 1. Canvas 指纹
    canvas_hash: str
    # 2. WebGL vendor
    webgl_vendor: str
    # 3. WebGL renderer
    webgl_renderer: str
    # 4. AudioContext 指纹
    audio_fingerprint: str
    # 5. 屏幕宽度
    screen_width: int
    # 6. 屏幕高度
    screen_height: int
    # 7. 色深
    color_depth: int
    # 8. 设备像素比
    pixel_ratio: float
    # 9. 时区偏移
    # (已包含在 timezone_offset)
    # 10. 语言
    language: str
    # 11. 平台
    platform: str
    # 12. CPU 核心数
    cpu_cores: int
    # 13. 设备内存
    device_memory: int
    # 14. 触屏支持
    max_touch_points: int
    # 15. 会话 ID
    session_id: str

    # === 衍生值 ===
    webgl_hash: str
    font_hash: str
    fingerprint_hash: str  # 最终的 deviceFingerprintHash

    # 生成的 User-Agent
    user_agent: str
    sec_ch_ua: str
    sec_ch_ua_platform: str

    def get_headers(self, for_sheerid: bool = True) -> dict:
        """
        生成与此设备身份完全一致的 HTTP 请求头。

        所有请求头与指纹中的设备信号自洽：
        - User-Agent ↔ platform ↔ sec-ch-ua-platform
        - Chrome 版本 ↔ sec-ch-ua
        """
        is_mobile = self.device.device_type == "mobile"

        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": f"{self.language},en;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "sec-ch-ua": self.sec_ch_ua,
            "sec-ch-ua-mobile": "?1" if is_mobile else "?0",
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
                "clientversion": "2.190.0",
                "clientname": "jslib",
                "origin": "https://services.sheerid.com",
                "referer": "https://services.sheerid.com/",
                **nr_headers,
            })

        return headers

    def _generate_newrelic_headers(self) -> dict:
        """生成 NewRelic 追踪头"""
        trace_id = uuid.uuid4().hex[:32]
        span_id = uuid.uuid4().hex[:16]
        timestamp = int(time.time() * 1000)

        payload = {
            "v": [0, 1],
            "d": {
                "ty": "Browser",
                "ac": "364029",
                "ap": "134291347",
                "id": span_id,
                "tr": trace_id,
                "ti": timestamp,
            },
        }

        return {
            "newrelic": base64.b64encode(json.dumps(payload).encode()).decode(),
            "traceparent": f"00-{trace_id}-{span_id}-01",
            "tracestate": f"364029@nr=0-1-364029-134291347-{span_id}----{timestamp}",
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
            f"  fingerprint={self.fingerprint_hash}\n"
            f")"
        )
