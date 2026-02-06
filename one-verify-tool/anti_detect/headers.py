"""
请求头生成模块
生成类浏览器请求头和 NewRelic 追踪头

优化内容：
- 根据 User-Agent 确定性选择匹配的 platform
- 确保 sec-ch-ua、sec-ch-ua-platform 与 User-Agent 完全一致
- 根据 Chrome 版本动态生成正确的 sec-ch-ua 头
"""

import base64
import json
import random
import re
import time
import uuid

from .config import (
    LANGUAGES,
    USER_AGENTS_CHROME,
    DEFAULT_IMPERSONATE,
    UA_PLATFORM_MAP,
    CHROME_VERSION_SEC_CH_UA,
)


def generate_newrelic_headers() -> dict:
    """
    生成 SheerID API 所需的 NewRelic 追踪请求头
    这些请求头有助于使请求看起来像来自真实浏览器
    """
    trace_id = uuid.uuid4().hex + uuid.uuid4().hex[:8]
    trace_id = trace_id[:32]
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


def _extract_chrome_version(ua: str) -> str:
    """从 User-Agent 中提取 Chrome 版本号"""
    match = re.search(r"Chrome/(\d+)\.", ua)
    return match.group(1) if match else "131"


def _get_platform_for_ua(ua: str) -> tuple:
    """
    根据 User-Agent 确定性地返回匹配的平台信息
    
    返回: (platform_name, sec_ch_ua_platform, sec_ch_ua)
    """
    # 提取 Chrome 版本以生成正确的 sec-ch-ua
    chrome_version = _extract_chrome_version(ua)
    sec_ch_ua = CHROME_VERSION_SEC_CH_UA.get(
        chrome_version,
        CHROME_VERSION_SEC_CH_UA["131"]  # 默认使用 131
    )

    # 根据 UA 内容匹配平台
    for ua_pattern, platform_info in UA_PLATFORM_MAP.items():
        if ua_pattern in ua:
            platform_name, sec_ch_ua_platform, _ = platform_info
            return (platform_name, sec_ch_ua_platform, sec_ch_ua)

    # 默认返回 Windows 平台
    return ("Windows", '"Windows"', sec_ch_ua)


def get_headers() -> dict:
    """
    生成 SheerID 专用请求头（确保一致性）
    
    关键改进：
    - User-Agent 与 sec-ch-ua-platform 保持一致
    - sec-ch-ua 版本与 User-Agent 中的 Chrome 版本匹配
    """
    # 使用与 TLS 指纹版本匹配的 User-Agent
    ua = get_matched_ua_for_impersonate()

    # 根据 UA 确定性选择匹配的平台（而非随机）
    platform_name, sec_ch_ua_platform, sec_ch_ua = _get_platform_for_ua(ua)

    language = random.choice(LANGUAGES)
    nr_headers = generate_newrelic_headers()

    # 请求头（像真实浏览器一样正确排序）
    return {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": language,
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "sec-ch-ua": sec_ch_ua,
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": sec_ch_ua_platform,
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": ua,
        "content-type": "application/json",
        "clientversion": "2.158.0",
        "clientname": "jslib",
        "origin": "https://services.sheerid.com",
        "referer": "https://services.sheerid.com/",
        **nr_headers,
    }


def get_matched_ua_for_impersonate(impersonate: str = None) -> str:
    """
    获取与我们模拟的 Chrome 版本匹配的 User-Agent

    重要: User-Agent 必须与 TLS 指纹版本匹配，
    否则 SheerID 可以检测到不匹配。
    """
    imp = impersonate or DEFAULT_IMPERSONATE

    # 提取版本号
    version = imp.replace("chrome", "").replace("edge", "").replace("safari", "")

    # 查找匹配的 UA
    for ua in USER_AGENTS_CHROME:
        if f"Chrome/{version}." in ua:
            return ua

    # 回退到第一个 Chrome UA
    return USER_AGENTS_CHROME[0]
