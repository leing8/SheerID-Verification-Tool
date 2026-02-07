"""
反检测模块
提供 EXIF 清理、噪声添加、纸张纹理等功能
防止 AI 检测伪造或篡改的文档
"""

import random
from io import BytesIO
from typing import Tuple

from PIL import Image, ImageFilter, ImageFont

# 字体缓存，避免重复加载
_font_cache = {}
_courier_cache = {}


def load_fonts(sizes: Tuple[int, ...] = (32, 24, 18, 16, 14)) -> dict:
    """
    加载 Arial 字体族（带缓存）
    
    参数:
        sizes: 需要的字体大小元组
    
    返回:
        字体字典，包含 "header", "title", "lg", "md", "sm", "text", "bold" 等键
    
    异常:
        RuntimeError: 字体文件不存在
    """
    cache_key = sizes
    if cache_key in _font_cache:
        return _font_cache[cache_key]
    
    try:
        fonts = {}
        # 常用尺寸映射
        if 32 in sizes:
            fonts["header"] = ImageFont.truetype("arial.ttf", 32)
        if 26 in sizes:
            fonts["lg"] = ImageFont.truetype("arial.ttf", 26)
        if 24 in sizes:
            fonts["title"] = ImageFont.truetype("arial.ttf", 24)
        if 20 in sizes:
            fonts["bold_lg"] = ImageFont.truetype("arialbd.ttf", 20)
        if 18 in sizes:
            fonts["md"] = ImageFont.truetype("arial.ttf", 18)
        if 16 in sizes:
            fonts["text"] = ImageFont.truetype("arial.ttf", 16)
            fonts["bold"] = ImageFont.truetype("arialbd.ttf", 16)
        if 14 in sizes:
            fonts["sm"] = ImageFont.truetype("arial.ttf", 14)
            fonts["bold_sm"] = ImageFont.truetype("arialbd.ttf", 14)
        
        _font_cache[cache_key] = fonts
        return fonts
    except Exception as e:
        raise RuntimeError(f"无法加载字体文件，请确保系统已安装 Arial 字体: {e}")


def clean_exif_metadata(img: Image.Image, rng: random.Random) -> Image.Image:
    """
    清理/伪造 EXIF 元数据
    
    SheerID 可能检测：
    - 创建软件标识（PIL/Pillow vs 真实相机/扫描仪）
    - 时间戳异常
    - 缺少真实设备信息
    """
    # 创建一个干净的副本，去除所有元数据
    clean_img = Image.new(img.mode, img.size)
    clean_img.putdata(list(img.getdata()))
    return clean_img


def add_realistic_noise(img: Image.Image, rng: random.Random, intensity: float = 0.02) -> Image.Image:
    """
    添加真实感噪声（模拟扫描/拍摄效果）
    
    防止 AI 检测"过于完美"的数字生成文档
    """
    pixels = img.load()
    width, height = img.size
    
    # 添加随机噪点
    for _ in range(int(width * height * intensity)):
        x = rng.randint(0, width - 1)
        y = rng.randint(0, height - 1)
        r, g, b = pixels[x, y]
        # 微小的颜色变化
        delta = rng.randint(-8, 8)
        pixels[x, y] = (
            max(0, min(255, r + delta)),
            max(0, min(255, g + delta)),
            max(0, min(255, b + delta)),
        )
    
    return img


def add_paper_texture(img: Image.Image, rng: random.Random) -> Image.Image:
    """
    添加纸张纹理效果（模拟真实打印/扫描文档）
    """
    # 轻微模糊模拟扫描效果
    if rng.random() < 0.3:
        img = img.filter(ImageFilter.GaussianBlur(radius=0.3))
    
    # 随机轻微旋转（模拟扫描偏斜）
    if rng.random() < 0.4:
        angle = rng.uniform(-0.5, 0.5)
        img = img.rotate(angle, fillcolor=(255, 255, 255), expand=False)
    
    return img


def apply_anti_detection(img: Image.Image, rng: random.Random, noise_intensity: float = 0.015) -> Image.Image:
    """
    应用所有反检测效果
    
    参数:
        img: 原始图像
        rng: 种子随机数生成器
        noise_intensity: 噪声强度（默认0.015）
    
    返回:
        处理后的图像
    """
    img = add_realistic_noise(img, rng, intensity=noise_intensity)
    img = add_paper_texture(img, rng)
    img = clean_exif_metadata(img, rng)
    return img


def image_to_bytes(img: Image.Image, rng: random.Random, noise_intensity: float = 0.015) -> bytes:
    """
    将图像转换为 PNG 字节（含反检测处理）
    
    参数:
        img: PIL Image 对象
        rng: 种子随机数生成器
        noise_intensity: 噪声强度
    
    返回:
        PNG 格式的字节数据
    """
    img = apply_anti_detection(img, rng, noise_intensity)
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def load_courier_fonts(sizes: Tuple[int, ...] = (14, 12, 11, 10)) -> dict:
    """
    加载 Letter Gothic Std 等宽字体（Harvard 成绩单专用）
    
    Letter Gothic 是打字机风格的等宽字体，Harvard 成绩单使用此风格
    
    参数:
        sizes: 需要的字体大小元组
    
    返回:
        字体字典，包含 "lg", "md", "sm", "xs" 等键
    
    异常:
        RuntimeError: 字体文件不存在
    """
    cache_key = ("letter_gothic", sizes)
    if cache_key in _courier_cache:
        return _courier_cache[cache_key]
    
    try:
        from pathlib import Path
        
        fonts = {}
        
        # Letter Gothic Std 字体路径（按优先级排序）
        font_paths = [
            # 用户字体目录
            Path.home() / "AppData/Local/Microsoft/Windows/Fonts/LetterGothicStd.otf",
            Path.home() / "AppData/Local/Microsoft/Windows/Fonts/LetterGothicStd-Bold.otf",
            # 系统字体目录
            Path("C:/Windows/Fonts/LetterGothicStd.otf"),
            Path("C:/Windows/Fonts/LetterGothicStd-Bold.otf"),
            # 项目本地字体目录
            Path(__file__).parent.parent / "fonts/LetterGothicStd.otf",
        ]
        
        # 查找可用的字体文件
        regular_font = None
        bold_font = None
        for p in font_paths:
            if p.exists():
                if "Bold" in p.name or "bold" in p.name:
                    bold_font = bold_font or str(p)
                else:
                    regular_font = regular_font or str(p)
        
        if not regular_font:
            raise FileNotFoundError("未找到 LetterGothicStd 字体文件")
        
        # 如果没有粗体，使用常规字体代替
        bold_font = bold_font or regular_font
        
        if 14 in sizes:
            fonts["lg"] = ImageFont.truetype(regular_font, 14)
            fonts["lg_bold"] = ImageFont.truetype(bold_font, 14)
        if 12 in sizes:
            fonts["md"] = ImageFont.truetype(regular_font, 12)
            fonts["md_bold"] = ImageFont.truetype(bold_font, 12)
        if 11 in sizes:
            fonts["sm"] = ImageFont.truetype(regular_font, 11)
            fonts["sm_bold"] = ImageFont.truetype(bold_font, 11)
        if 10 in sizes:
            fonts["xs"] = ImageFont.truetype(regular_font, 10)
        
        _courier_cache[cache_key] = fonts
        return fonts
    except Exception as e:
        raise RuntimeError(f"无法加载 Letter Gothic 字体文件: {e}")


def image_to_format(
    img: Image.Image, 
    rng: random.Random, 
    output_format: str = "png",
    noise_intensity: float = 0.008
) -> bytes:
    """
    将图像转换为指定格式的字节（含反检测处理）
    
    支持 PNG、JPG、PDF 三种格式输出。
    对于模板叠加类型的图片，使用较低的噪声强度以保持质量。
    
    参数:
        img: PIL Image 对象
        rng: 种子随机数生成器
        output_format: 输出格式 ("png", "jpg", "pdf")
        noise_intensity: 噪声强度（模板叠加建议 0.008）
    
    返回:
        指定格式的字节数据
    """
    # 应用反检测效果
    img = apply_anti_detection(img, rng, noise_intensity)
    
    buf = BytesIO()
    output_format = output_format.lower()
    
    if output_format == "png":
        img.save(buf, format="PNG", optimize=True)
    elif output_format in ("jpg", "jpeg"):
        # JPEG 需要 RGB 模式
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        # 使用较高质量避免压缩伪影
        img.save(buf, format="JPEG", quality=92, optimize=True)
    elif output_format == "pdf":
        # PDF 需要 RGB 模式
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf, format="PDF", resolution=150.0)
    else:
        raise ValueError(f"不支持的输出格式: {output_format}，支持: png, jpg, pdf")
    
    return buf.getvalue()
