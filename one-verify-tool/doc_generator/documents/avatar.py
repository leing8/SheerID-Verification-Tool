"""
头像获取模块
通过 pravatar.cc API 获取真人头像
"""

import hashlib
from io import BytesIO
from typing import Optional

from PIL import Image

# 尝试导入 curl_cffi，作为反检测 HTTP 客户端
try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    import requests
    HAS_CURL_CFFI = False

# 头像缓存（基于seed）
_avatar_cache: dict = {}


def _http_get(url: str, headers: dict = None, timeout: int = 10):
    """统一的 HTTP GET 请求"""
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    }
    if headers:
        default_headers.update(headers)
    
    if HAS_CURL_CFFI:
        return cffi_requests.get(url, headers=default_headers, timeout=timeout, impersonate="chrome120")
    return requests.get(url, headers=default_headers, timeout=timeout)


def fetch_random_avatar(
    seed: str,
    size: tuple = (139, 169),
    use_cache: bool = True
) -> Optional[Image.Image]:
    """
    获取随机头像
    
    优先使用 pravatar.cc（稳定可复现），失败时使用 thispersondoesnotexist
    
    参数:
        seed: 随机种子（用于生成唯一头像ID和缓存键）
        size: 目标尺寸 (宽, 高)
        use_cache: 是否使用缓存
    
    返回:
        PIL Image 对象，失败返回 None
    """
    cache_key = hashlib.md5(f"{seed}_{size}".encode()).hexdigest()
    
    if use_cache and cache_key in _avatar_cache:
        return _avatar_cache[cache_key].copy()
    
    # 优先使用 pravatar.cc（稳定可复现）
    avatar_img = _fetch_from_pravatar(seed, max(size))
    
    # 备用：thispersondoesnotexist
    if avatar_img is None:
        avatar_img = _fetch_from_thispersondoesnotexist()
    
    if avatar_img is None:
        return None
    
    # 裁剪和缩放到目标尺寸
    avatar_img = _crop_to_id_photo(avatar_img, size)
    
    if use_cache:
        _avatar_cache[cache_key] = avatar_img.copy()
    
    return avatar_img


def _fetch_from_pravatar(seed: str, size: int = 300) -> Optional[Image.Image]:
    """
    从 pravatar.cc 获取头像
    
    使用 seed 作为唯一标识，确保相同 seed 返回相同头像
    """
    try:
        # 使用 seed 的 hash 作为唯一 ID
        unique_id = hashlib.md5(seed.encode()).hexdigest()[:16]
        url = f"https://i.pravatar.cc/{size}?u={unique_id}"
        
        resp = _http_get(url)
        if resp.status_code == 200 and len(resp.content) > 1000:
            return Image.open(BytesIO(resp.content)).convert("RGB")
    except Exception:
        pass
    
    return None


def _fetch_from_thispersondoesnotexist() -> Optional[Image.Image]:
    """从 thispersondoesnotexist.com 获取头像（备用）"""
    try:
        url = "https://thispersondoesnotexist.com"
        resp = _http_get(url)
        if resp.status_code == 200 and len(resp.content) > 1000:
            return Image.open(BytesIO(resp.content)).convert("RGB")
    except Exception:
        pass
    
    return None


def _crop_to_id_photo(img: Image.Image, size: tuple) -> Image.Image:
    """
    裁剪图像为证件照比例
    
    取中心偏上区域（人脸通常在上半部分）
    """
    w, h = img.size
    target_ratio = size[0] / size[1]  # 宽高比
    current_ratio = w / h
    
    if current_ratio > target_ratio:
        # 太宽，裁剪两侧
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        # 太高，裁剪下方（保留头部）
        new_h = int(w / target_ratio)
        img = img.crop((0, 0, w, new_h))
    
    return img.resize(size, Image.Resampling.LANCZOS)


def create_placeholder_avatar(size: tuple = (139, 169)) -> Image.Image:
    """
    创建占位头像（无法获取头像时使用）
    
    生成灰色渐变背景的占位图
    """
    img = Image.new("RGB", size, (180, 180, 180))
    pixels = img.load()
    for y in range(size[1]):
        for x in range(size[0]):
            gray = 160 + int(40 * y / size[1])
            pixels[x, y] = (gray, gray, gray)
    
    return img

