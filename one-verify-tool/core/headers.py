"""
请求头模块 - HTTP 请求头生成

包含:
- generate_newrelic_headers: NewRelic 跟踪头
- get_headers: 完整的 Chrome 请求头
- get_headers_with_profile: 使用 BrowserProfile 生成请求头
"""

import random
import uuid
import time
import base64
import json
from typing import Dict, Optional
from collections import OrderedDict

from .constants import LANGUAGES
from .fingerprint import get_or_create_profile, BrowserProfile


def generate_newrelic_headers() -> dict:
    """
    生成 SheerID 需要的 NewRelic 跟踪头
    
    NewRelic 用于分布式追踪，这些头部对于模拟真实浏览器请求很重要。
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


def get_headers_with_profile(
    profile: BrowserProfile,
    for_sheerid: bool = True,
    with_auth: str = None,
    referer: str = None,
    include_client_hints: bool = True,
) -> Dict:
    """
    使用 BrowserProfile 生成完整的 Chrome 请求头
    
    按照真实 Chrome 浏览器的 header 顺序排列，这对于避免检测很重要。
    
    Args:
        profile: 浏览器配置文件
        for_sheerid: 是否为 SheerID API 生成专用头
        with_auth: 可选的 Bearer token
        referer: 可选的 Referer URL
        include_client_hints: 是否包含 Client Hints
    
    Returns:
        OrderedDict: 按正确顺序排列的请求头
    """
    # 使用 OrderedDict 保持 header 顺序（Chrome 的实际顺序）
    headers = OrderedDict()
    
    # 1. Host (由 HTTP 库自动添加)
    
    # 2. Connection headers
    headers["Connection"] = "keep-alive"
    
    # 3. Cache headers
    headers["Cache-Control"] = "no-cache"
    headers["Pragma"] = "no-cache"
    
    # 4. Client Hints (Chrome 优先发送)
    if include_client_hints:
        client_hints = profile.get_client_hints()
        headers["sec-ch-ua"] = client_hints["sec-ch-ua"]
        headers["sec-ch-ua-mobile"] = client_hints["sec-ch-ua-mobile"]
        headers["sec-ch-ua-platform"] = client_hints["sec-ch-ua-platform"]
    
    # 5. Upgrade-Insecure-Requests (仅页面请求)
    
    # 6. User-Agent
    headers["User-Agent"] = profile.user_agent
    
    # 7. Accept headers
    headers["Accept"] = "application/json, text/plain, */*"
    headers["Accept-Encoding"] = "gzip, deflate, br, zstd"
    headers["Accept-Language"] = profile._language
    
    # 8. Sec-Fetch headers
    headers["Sec-Fetch-Dest"] = "empty"
    headers["Sec-Fetch-Mode"] = "cors"
    headers["Sec-Fetch-Site"] = "same-origin"
    
    # 9. Origin and Referer
    if for_sheerid:
        headers["Origin"] = "https://services.sheerid.com"
        headers["Referer"] = referer or "https://services.sheerid.com/"
    elif referer:
        headers["Referer"] = referer
    
    # 10. SheerID specific headers
    if for_sheerid:
        headers["Content-Type"] = "application/json"
        headers["clientversion"] = "2.180.0"  # 更新版本号
        headers["clientname"] = "jslib"
        
        # NewRelic headers
        nr_headers = generate_newrelic_headers()
        headers["newrelic"] = nr_headers["newrelic"]
        headers["traceparent"] = nr_headers["traceparent"]
        headers["tracestate"] = nr_headers["tracestate"]
    
    # 11. Extended Client Hints (按需)
    if include_client_hints and for_sheerid:
        client_hints = profile.get_client_hints()
        if "sec-ch-ua-platform-version" in client_hints:
            headers["sec-ch-ua-platform-version"] = client_hints["sec-ch-ua-platform-version"]
    
    # 12. Authorization
    if with_auth:
        headers["Authorization"] = f"Bearer {with_auth}"
    
    return dict(headers)


def get_headers(for_sheerid: bool = True, with_auth: str = None) -> dict:
    """
    生成 Chrome 浏览器请求头（兼容旧 API）
    
    Args:
        for_sheerid: 是否为 SheerID API 生成专用头
        with_auth: 可选的 Bearer token
    
    Returns:
        dict: HTTP 请求头
    """
    profile = get_or_create_profile()
    return get_headers_with_profile(profile, for_sheerid, with_auth)


def get_resource_headers(profile: BrowserProfile, resource_type: str = "script") -> Dict:
    """
    生成资源请求头（模拟加载 JS/CSS/图片）
    
    Args:
        profile: 浏览器配置文件
        resource_type: 资源类型 (script, style, image, font)
    
    Returns:
        dict: HTTP 请求头
    """
    headers = OrderedDict()
    
    headers["sec-ch-ua"] = profile.get_client_hints()["sec-ch-ua"]
    headers["sec-ch-ua-mobile"] = "?0"
    headers["sec-ch-ua-platform"] = profile.get_client_hints()["sec-ch-ua-platform"]
    headers["User-Agent"] = profile.user_agent
    
    # Accept header 根据资源类型变化
    accept_map = {
        "script": "*/*",
        "style": "text/css,*/*;q=0.1",
        "image": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "font": "*/*",
        "document": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
    headers["Accept"] = accept_map.get(resource_type, "*/*")
    
    headers["Accept-Encoding"] = "gzip, deflate, br, zstd"
    headers["Accept-Language"] = profile._language
    
    # Sec-Fetch headers
    headers["Sec-Fetch-Dest"] = resource_type if resource_type in ["script", "style", "image", "font"] else "empty"
    headers["Sec-Fetch-Mode"] = "no-cors"
    headers["Sec-Fetch-Site"] = "same-origin"
    
    headers["Referer"] = "https://services.sheerid.com/"
    
    return dict(headers)


def get_navigation_headers(profile: BrowserProfile, from_url: str = None) -> Dict:
    """
    生成页面导航请求头
    
    Args:
        profile: 浏览器配置文件
        from_url: 来源页面 URL
    
    Returns:
        dict: HTTP 请求头
    """
    headers = OrderedDict()
    
    headers["Cache-Control"] = "no-cache"
    headers["Pragma"] = "no-cache"
    
    client_hints = profile.get_client_hints()
    headers["sec-ch-ua"] = client_hints["sec-ch-ua"]
    headers["sec-ch-ua-mobile"] = "?0"
    headers["sec-ch-ua-platform"] = client_hints["sec-ch-ua-platform"]
    
    headers["Upgrade-Insecure-Requests"] = "1"
    headers["User-Agent"] = profile.user_agent
    
    headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    headers["Accept-Encoding"] = "gzip, deflate, br, zstd"
    headers["Accept-Language"] = profile._language
    
    headers["Sec-Fetch-Dest"] = "document"
    headers["Sec-Fetch-Mode"] = "navigate"
    headers["Sec-Fetch-Site"] = "same-origin" if from_url else "none"
    headers["Sec-Fetch-User"] = "?1"
    
    if from_url:
        headers["Referer"] = from_url
    
    return dict(headers)
