"""
反检测模块 - 请求头生成

生成浏览器级请求头和 NewRelic 追踪头。
"""

import base64
import json
import random
import time
import uuid

from .constants import (
    DEFAULT_IMPERSONATE,
    LANGUAGES,
    PLATFORMS,
    USER_AGENTS,
    USER_AGENTS_CHROME,
)


def get_random_user_agent() -> str:
    """随机获取一个 User-Agent 字符串"""
    return random.choice(USER_AGENTS)


def generate_newrelic_headers() -> dict:
    """生成 SheerID API 所需的 NewRelic 追踪头，模拟真实浏览器请求"""
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


def get_headers(for_sheerid: bool = True, with_auth: str = None) -> dict:
    """
    生成浏览器级请求头（按真实浏览器顺序排列）

    Args:
        for_sheerid: 是否使用 SheerID 专用请求头
        with_auth: Bearer 授权令牌
    """
    ua = get_random_user_agent()
    platform = random.choice(PLATFORMS)
    language = random.choice(LANGUAGES)

    # 基础请求头（按真实浏览器顺序排列）
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": language,
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "sec-ch-ua": platform[2],
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": platform[1],
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": ua,
    }

    if for_sheerid:
        nr_headers = generate_newrelic_headers()
        headers.update(
            {
                "content-type": "application/json",
                "clientversion": "2.158.0",
                "clientname": "jslib",
                "origin": "https://services.sheerid.com",
                "referer": "https://services.sheerid.com/",
                **nr_headers,  # NewRelic 追踪头
            }
        )

    if with_auth:
        headers["authorization"] = f"Bearer {with_auth}"
        headers["origin"] = "https://chatgpt.com"
        headers["referer"] = "https://chatgpt.com/"
        headers["oai-device-id"] = str(uuid.uuid4())
        headers["oai-language"] = "en-US"

    return headers


def get_matched_ua_for_impersonate(impersonate: str = None) -> str:
    """
    获取与模拟版本匹配的 User-Agent

    重要: User-Agent 必须与 TLS 指纹版本匹配，否则 SheerID 可检测到不一致
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
