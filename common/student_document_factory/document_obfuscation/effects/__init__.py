"""
document_obfuscation.effects — 各类文档损坏效果

子模块：
  utils             — 共享工具函数（to_uint8 / to_float32 / make_rs）
  stains            — 污渍（mud / wear / fading）
  creases           — 折痕（纯光照方案，支持 SafeZone）
  crop              — 边缘裁剪（未实现）
  transform_3d      — 3D 透视变换（未实现）
  background_scene  — 背景场景叠加（桌面拍照模拟，含真实透视变换）
"""
