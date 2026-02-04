"""
指纹生成模块 - 浏览器指纹生成

包含:
- BrowserProfile: 一致性浏览器配置文件
- get_fingerprint: 基础指纹 hash
- get_canvas_fingerprint: Canvas 指纹
- get_webgl_fingerprint: WebGL 指纹
- get_audio_fingerprint: Audio 指纹
- get_full_fingerprint: 完整指纹
"""

import random
import hashlib
import time
import uuid
from typing import Dict, Optional, Tuple

from .constants import (
    RESOLUTIONS, SCREEN_CONFIGS, US_TIMEZONES, US_TIMEZONE_NAMES, LANGUAGES,
    WEBGL_CONFIGS, WEBGL_EXTENSIONS, NAVIGATOR_PROPS, NAVIGATOR_PLUGINS,
    AUDIO_CONTEXT_CONFIG, PLATFORMS, SEC_CH_UA_TEMPLATES,
    USER_AGENTS_CHROME, DEFAULT_IMPERSONATE,
)


class BrowserProfile:
    """
    一致性浏览器配置文件
    
    确保会话中所有浏览器参数相互匹配，避免指纹不一致导致的检测。
    """
    
    def __init__(self, platform: str = None, chrome_version: str = None):
        """
        初始化浏览器配置文件
        
        Args:
            platform: 平台类型 ("windows", "macos", "linux")
            chrome_version: Chrome 版本 (如 "133", "132")
        """
        # 确定平台
        self._platform = platform or random.choice(["windows", "windows", "windows", "macos", "linux"])
        
        # 确定 Chrome 版本
        self._chrome_version = chrome_version or DEFAULT_IMPERSONATE.replace("chrome", "")
        
        # 生成会话 ID
        self._session_id = str(uuid.uuid4())
        self._created_at = time.time()
        
        # 生成一致的参数
        self._generate_consistent_params()
    
    def _generate_consistent_params(self):
        """生成相互一致的浏览器参数"""
        
        # 1. 屏幕配置
        self._resolution = random.choice(RESOLUTIONS)
        width, height = self._resolution.split("x")
        self._screen_width = int(width)
        self._screen_height = int(height)
        
        screen_config = SCREEN_CONFIGS.get(self._resolution, {
            "availWidth": self._screen_width,
            "availHeight": self._screen_height - 40,
            "colorDepth": 24,
            "pixelRatio": 1,
        })
        self._avail_width = screen_config["availWidth"]
        self._avail_height = screen_config["availHeight"]
        self._color_depth = screen_config["colorDepth"]
        self._pixel_ratio = screen_config["pixelRatio"]
        
        # 2. 平台配置
        platform_config = PLATFORMS.get(self._platform, PLATFORMS["windows"])
        self._navigator_platform = platform_config["platform"]
        self._sec_ch_ua_platform = platform_config["sec_ch_ua_platform"]
        self._os_version = random.choice(platform_config["os_version"])
        self._arch = platform_config["arch"]
        self._bitness = platform_config["bitness"]
        
        # 3. sec-ch-ua
        self._sec_ch_ua = SEC_CH_UA_TEMPLATES.get(
            self._chrome_version,
            SEC_CH_UA_TEMPLATES["133"]
        )
        
        # 4. User-Agent
        ua_list = USER_AGENTS_CHROME.get(self._chrome_version, USER_AGENTS_CHROME["133"])
        # 根据平台选择匹配的 UA
        platform_ua_keywords = {
            "windows": "Windows NT",
            "macos": "Macintosh",
            "linux": "X11; Linux",
        }
        keyword = platform_ua_keywords.get(self._platform, "Windows NT")
        matching_uas = [ua for ua in ua_list if keyword in ua]
        self._user_agent = random.choice(matching_uas) if matching_uas else ua_list[0]
        
        # 5. 时区
        self._timezone_offset = random.choice(US_TIMEZONES)
        self._timezone_name = US_TIMEZONE_NAMES.get(self._timezone_offset, "America/New_York")
        
        # 6. 语言
        self._language = random.choice(LANGUAGES)
        self._language_primary = self._language.split(",")[0]
        
        # 7. WebGL 配置
        webgl_config = WEBGL_CONFIGS.get(self._platform, WEBGL_CONFIGS["windows"])
        self._webgl_vendor = random.choice(webgl_config["vendors"])
        
        # 从 vendor 提取 GPU 品牌
        gpu_brand = "NVIDIA"
        for brand in ["NVIDIA", "Intel", "AMD", "Apple"]:
            if brand in self._webgl_vendor:
                gpu_brand = brand
                break
        
        renderers = webgl_config["renderers"].get(gpu_brand, list(webgl_config["renderers"].values())[0])
        self._webgl_renderer = random.choice(renderers)
        
        # WebGL extensions (随机选择部分)
        num_extensions = random.randint(20, len(WEBGL_EXTENSIONS))
        self._webgl_extensions = random.sample(WEBGL_EXTENSIONS, num_extensions)
        
        # 8. Navigator 属性
        self._hardware_concurrency = random.choice(NAVIGATOR_PROPS["hardwareConcurrency"])
        self._device_memory = random.choice(NAVIGATOR_PROPS["deviceMemory"])
        self._max_touch_points = random.choice(NAVIGATOR_PROPS["maxTouchPoints"])
        
        # 9. Audio 配置
        self._audio_sample_rate = random.choice(AUDIO_CONTEXT_CONFIG["sampleRate"])
        self._audio_base_latency = random.choice(AUDIO_CONTEXT_CONFIG["baseLatency"])
        
        # 10. 生成指纹 hash
        self._generate_fingerprint_hashes()
    
    def _generate_fingerprint_hashes(self):
        """生成各类指纹 hash"""
        # 基于配置生成一致的 hash
        base_seed = f"{self._session_id}:{self._platform}:{self._resolution}"
        
        # Canvas 指纹
        canvas_seed = f"{base_seed}:canvas:{self._webgl_renderer}"
        self._canvas_hash = hashlib.sha256(canvas_seed.encode()).hexdigest()[:32]
        
        # WebGL 指纹
        webgl_seed = f"{base_seed}:webgl:{self._webgl_vendor}:{self._webgl_renderer}"
        self._webgl_hash = hashlib.md5(webgl_seed.encode()).hexdigest()
        
        # Audio 指纹 (模拟 AudioContext fingerprint)
        audio_seed = f"{base_seed}:audio:{self._audio_sample_rate}"
        audio_random = random.Random(hash(audio_seed))
        self._audio_fingerprint = str(audio_random.uniform(124.04344968475198, 124.04344968475499))[:18]
        
        # 主指纹 hash
        components = [
            self._resolution,
            str(self._timezone_offset),
            self._language_primary,
            self._navigator_platform,
            self._webgl_vendor,
            str(self._hardware_concurrency),
            str(self._device_memory),
            self._canvas_hash[:8],
            self._webgl_hash[:8],
            self._session_id,
        ]
        self._main_hash = hashlib.md5("|".join(components).encode()).hexdigest()
    
    @property
    def user_agent(self) -> str:
        return self._user_agent
    
    @property
    def platform(self) -> str:
        return self._platform
    
    @property
    def chrome_version(self) -> str:
        return self._chrome_version
    
    @property
    def fingerprint_hash(self) -> str:
        return self._main_hash
    
    @property
    def session_id(self) -> str:
        return self._session_id
    
    def get_screen_info(self) -> Dict:
        """获取屏幕信息"""
        return {
            "width": self._screen_width,
            "height": self._screen_height,
            "availWidth": self._avail_width,
            "availHeight": self._avail_height,
            "colorDepth": self._color_depth,
            "pixelDepth": self._color_depth,
            "pixelRatio": self._pixel_ratio,
        }
    
    def get_navigator_info(self) -> Dict:
        """获取 Navigator 信息"""
        return {
            "platform": self._navigator_platform,
            "userAgent": self._user_agent,
            "language": self._language_primary,
            "languages": self._language.replace(";q=", ",").split(","),
            "hardwareConcurrency": self._hardware_concurrency,
            "deviceMemory": self._device_memory,
            "maxTouchPoints": self._max_touch_points,
            "cookieEnabled": True,
            "pdfViewerEnabled": True,
            "webdriver": False,
            "plugins": NAVIGATOR_PLUGINS[:5],
        }
    
    def get_webgl_info(self) -> Dict:
        """获取 WebGL 信息"""
        return {
            "vendor": self._webgl_vendor,
            "renderer": self._webgl_renderer,
            "hash": self._webgl_hash,
            "extensions": self._webgl_extensions,
        }
    
    def get_audio_info(self) -> Dict:
        """获取 Audio 信息"""
        return {
            "sampleRate": self._audio_sample_rate,
            "baseLatency": self._audio_base_latency,
            "fingerprint": self._audio_fingerprint,
        }
    
    def get_timezone_info(self) -> Dict:
        """获取时区信息"""
        return {
            "offset": self._timezone_offset,
            "name": self._timezone_name,
        }
    
    def get_client_hints(self) -> Dict:
        """获取 Client Hints headers"""
        return {
            "sec-ch-ua": self._sec_ch_ua,
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": self._sec_ch_ua_platform,
            "sec-ch-ua-platform-version": f'"{self._os_version}"',
            "sec-ch-ua-arch": f'"{self._arch}"',
            "sec-ch-ua-bitness": f'"{self._bitness}"',
            "sec-ch-ua-full-version-list": self._sec_ch_ua,
        }
    
    def to_full_fingerprint(self) -> Dict:
        """导出完整指纹数据"""
        return {
            "hash": self._main_hash,
            "canvas": self._canvas_hash,
            "webgl": self.get_webgl_info(),
            "audio": self._audio_fingerprint,
            "screen": self.get_screen_info(),
            "timezone": self._timezone_offset,
            "timezoneName": self._timezone_name,
            "language": self._language_primary,
            "languages": self._language.replace(";q=", ",").split(","),
            "platform": self._navigator_platform,
            "cpuCores": self._hardware_concurrency,
            "memory": self._device_memory,
            "maxTouchPoints": self._max_touch_points,
            "sessionId": self._session_id,
            "clientHints": self.get_client_hints(),
        }


# ============ 全局 Profile 实例 (用于单次验证) ============
_current_profile: Optional[BrowserProfile] = None


def get_or_create_profile(platform: str = None, chrome_version: str = None) -> BrowserProfile:
    """获取或创建浏览器配置文件"""
    global _current_profile
    if _current_profile is None:
        _current_profile = BrowserProfile(platform, chrome_version)
    return _current_profile


def reset_profile():
    """重置浏览器配置文件（新会话时调用）"""
    global _current_profile
    _current_profile = None


def create_new_profile(platform: str = None, chrome_version: str = None) -> BrowserProfile:
    """创建新的浏览器配置文件并设为当前"""
    global _current_profile
    _current_profile = BrowserProfile(platform, chrome_version)
    return _current_profile


# ============ 兼容旧 API ============

def get_random_user_agent() -> str:
    """获取随机 User-Agent"""
    profile = get_or_create_profile()
    return profile.user_agent


def get_fingerprint() -> str:
    """生成浏览器指纹 hash"""
    profile = get_or_create_profile()
    return profile.fingerprint_hash


def get_canvas_fingerprint() -> str:
    """生成 Canvas 指纹 hash"""
    profile = get_or_create_profile()
    return profile._canvas_hash


def get_webgl_fingerprint() -> dict:
    """生成 WebGL 指纹"""
    profile = get_or_create_profile()
    return profile.get_webgl_info()


def get_audio_fingerprint() -> str:
    """生成 AudioContext 指纹"""
    profile = get_or_create_profile()
    return profile._audio_fingerprint


def get_full_fingerprint() -> dict:
    """生成完整浏览器指纹（会话内保持一致）"""
    profile = get_or_create_profile()
    return profile.to_full_fingerprint()


def get_matched_ua_for_impersonate(impersonate: str = None) -> str:
    """获取与 TLS 伪装版本匹配的 User-Agent"""
    if impersonate:
        version = impersonate.replace("chrome", "").replace("edge", "").replace("safari", "")
        if version in USER_AGENTS_CHROME:
            return random.choice(USER_AGENTS_CHROME[version])
    
    profile = get_or_create_profile()
    return profile.user_agent
