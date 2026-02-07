"""
WebGL 指纹生成模块
使用 DeviceProfile 确保 GPU 参数精确匹配
"""

from typing import Optional

from .base import get_seeded_random, generate_deterministic_hash
from .device_profile import DeviceProfile, GPU_PROFILES


def get_webgl_fingerprint(seed: str, device_profile: Optional[DeviceProfile] = None) -> dict:
    """
    生成 WebGL 指纹（使用真实 GPU 参数）
    
    参数:
        seed: verificationId（必须）
        device_profile: 统一设备档案，如果提供则使用其 GPU 配置
    
    返回:
        包含完整 WebGL 参数的字典
    """
    rng = get_seeded_random(seed)
    
    # 如果提供了设备档案，使用其 GPU 配置
    if device_profile is not None:
        gpu = device_profile.gpu
    else:
        # 向后兼容：没有设备档案时使用默认逻辑
        gpu_keys = list(GPU_PROFILES.keys())
        gpu = GPU_PROFILES[rng.choice(gpu_keys)]
    
    # GPU 信息（WEBGL_debug_renderer_info 扩展）
    vendor = gpu.vendor
    renderer = gpu.renderer
    
    # 常见 WebGL 扩展（根据 GPU 类型调整）
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
    
    # 根据 GPU 能力决定扩展数量
    if gpu.max_texture_size >= 32768:
        # 高端 GPU 支持更多扩展
        num_extensions = rng.randint(22, min(27, len(all_extensions)))
    elif gpu.max_texture_size >= 16384:
        # 中端 GPU
        num_extensions = rng.randint(18, 24)
    else:
        # 入门级 GPU
        num_extensions = rng.randint(15, 20)
    
    extensions = rng.sample(all_extensions, min(num_extensions, len(all_extensions)))
    
    # 着色器精度（使用 GPU 配置）
    shader_precision = {
        "highFloatPrecision": gpu.high_float_precision,
        "highIntPrecision": gpu.high_int_precision,
        "mediumFloatPrecision": rng.choice([23, 24]),
        "lowFloatPrecision": rng.choice([8, 23]),
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

        # GPU 能力参数（使用精确的 GPU 配置）
        "maxTextureSize": gpu.max_texture_size,
        "maxViewportDims": gpu.max_viewport_dims,
        "maxRenderbufferSize": gpu.max_renderbuffer_size,
        "maxCubeMapTextureSize": gpu.max_cube_map_texture_size,
        "maxTextureImageUnits": gpu.max_texture_image_units,
        "maxVertexTextureImageUnits": gpu.max_vertex_texture_image_units,
        "maxCombinedTextureImageUnits": gpu.max_combined_texture_image_units,
        "maxVertexAttribs": gpu.max_vertex_attribs,
        "maxVertexUniformVectors": gpu.max_vertex_uniform_vectors,
        "maxFragmentUniformVectors": gpu.max_fragment_uniform_vectors,
        "maxVaryingVectors": gpu.max_varying_vectors,

        # 抗锯齿
        "antialias": True,
        "maxSamples": gpu.max_samples,

        # 扩展
        "extensions": extensions,

        # 着色器精度
        "shaderPrecision": shader_precision,

        # 最终哈希
        "hash": generate_deterministic_hash(seed, "_webgl"),
    }
