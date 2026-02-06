"""
WebGL 指纹生成模块
模拟真实 GPU 渲染参数
"""

from .base import get_seeded_random, generate_deterministic_hash
from ..config import WEBGL_VENDORS, WEBGL_RENDERERS


def get_webgl_fingerprint(seed: str) -> dict:
    """
    生成 WebGL 指纹（模拟真实 GPU 渲染参数）
    
    真实浏览器中，WebGL 指纹包含：
    1. GPU 厂商和渲染器信息
    2. 支持的扩展列表
    3. 各种参数的最大值（受 GPU 限制）
    4. 着色器精度信息
    
    参数:
        seed: verificationId（必须）
    
    返回:
        包含完整 WebGL 参数的字典
    """
    rng = get_seeded_random(seed)

    # GPU 信息（WEBGL_debug_renderer_info 扩展）
    vendor = rng.choice(WEBGL_VENDORS)
    renderer = rng.choice(WEBGL_RENDERERS)

    # 根据 GPU 类型选择合适的参数范围
    is_nvidia = "NVIDIA" in renderer
    is_intel = "Intel" in renderer
    is_apple = "Apple" in renderer

    # 模拟 GPU 能力参数（不同 GPU 有不同的硬件限制）
    if is_nvidia:
        max_texture_size = rng.choice([16384, 32768])
        max_viewport_dims = [32768, 32768]
        max_renderbuffer_size = 16384
    elif is_intel:
        max_texture_size = rng.choice([8192, 16384])
        max_viewport_dims = [16384, 16384]
        max_renderbuffer_size = 8192
    elif is_apple:
        max_texture_size = 16384
        max_viewport_dims = [16384, 16384]
        max_renderbuffer_size = 16384
    else:  # AMD 或其他
        max_texture_size = rng.choice([8192, 16384])
        max_viewport_dims = [16384, 16384]
        max_renderbuffer_size = rng.choice([8192, 16384])

    # 常见 WebGL 扩展
    all_extensions = [
        "ANGLE_instanced_arrays",
        "EXT_blend_minmax",
        "EXT_color_buffer_half_float",
        "EXT_disjoint_timer_query",
        "EXT_float_blend",
        "EXT_frag_depth",
        "EXT_shader_texture_lod",
        "EXT_texture_compression_bptc",
        "EXT_texture_compression_rgtc",
        "EXT_texture_filter_anisotropic",
        "EXT_sRGB",
        "OES_element_index_uint",
        "OES_fbo_render_mipmap",
        "OES_standard_derivatives",
        "OES_texture_float",
        "OES_texture_float_linear",
        "OES_texture_half_float",
        "OES_texture_half_float_linear",
        "OES_vertex_array_object",
        "WEBGL_color_buffer_float",
        "WEBGL_compressed_texture_s3tc",
        "WEBGL_compressed_texture_s3tc_srgb",
        "WEBGL_debug_renderer_info",
        "WEBGL_debug_shaders",
        "WEBGL_depth_texture",
        "WEBGL_draw_buffers",
        "WEBGL_lose_context",
    ]
    # 随机选择 15-25 个扩展
    num_extensions = rng.randint(15, min(25, len(all_extensions)))
    extensions = rng.sample(all_extensions, num_extensions)

    # 着色器精度（不同 GPU 精度不同）
    shader_precision = {
        "highFloatPrecision": rng.choice([23, 24, 127]),
        "highIntPrecision": rng.choice([16, 24, 127]),
        "mediumFloatPrecision": rng.choice([23, 24]),
        "lowFloatPrecision": rng.choice([8, 23, 24]),
    }

    return {
        # GPU 信息
        "vendor": vendor,
        "renderer": renderer,
        "unmaskedVendor": vendor,
        "unmaskedRenderer": renderer,

        # 版本信息
        "version": "WebGL 1.0 (OpenGL ES 2.0 Chromium)",
        "shadingLanguageVersion": "WebGL GLSL ES 1.0 (OpenGL ES GLSL ES 1.0 Chromium)",

        # GPU 能力参数
        "maxTextureSize": max_texture_size,
        "maxViewportDims": max_viewport_dims,
        "maxRenderbufferSize": max_renderbuffer_size,
        "maxCubeMapTextureSize": max_texture_size // 2,
        "maxTextureImageUnits": rng.choice([16, 32]),
        "maxVertexTextureImageUnits": rng.choice([4, 8, 16]),
        "maxCombinedTextureImageUnits": rng.choice([32, 48, 80]),
        "maxVertexAttribs": rng.choice([16, 32]),
        "maxVertexUniformVectors": rng.choice([256, 1024, 4096]),
        "maxFragmentUniformVectors": rng.choice([256, 1024, 4096]),
        "maxVaryingVectors": rng.choice([15, 16, 30, 31]),

        # 抗锯齿
        "antialias": rng.choice([True, False]),
        "maxSamples": rng.choice([4, 8, 16]),

        # 扩展
        "extensions": extensions,

        # 着色器精度
        "shaderPrecision": shader_precision,

        # 最终哈希
        "hash": generate_deterministic_hash(seed, "_webgl"),
    }
