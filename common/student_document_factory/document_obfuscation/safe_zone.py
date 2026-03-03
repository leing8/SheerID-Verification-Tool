"""
document_obfuscation.safe_zone — 通用核心数据保护区

SafeZone 是与文档类型完全解耦的纯数据结构。
每种文档（哈佛 / 未来其它学校）只需提供 list[SafeZone]，
stains.py 根据该列表做 Rejection Sampling，无需知道文档细节。

使用方式：
    from .safe_zone import SafeZone

    # 各文档在自己的模块内定义保护区
    def get_safe_zones(img_w: int, img_h: int) -> list[SafeZone]:
        return [
            SafeZone(x1=70, y1=185, x2=img_w - 30, y2=270, label="address"),
            SafeZone(x1=30, y1=440, x2=img_w - 30, y2=img_h - 10, label="courses"),
        ]

    # 传入流水线
    pipeline = ObfuscationPipeline(rng, safe_zones=get_safe_zones(w, h))
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SafeZone:
    """
    矩形核心数据保护区（像素坐标，含 padding 扩展）。

    Attributes:
        x1, y1:  左上角坐标（图像像素）。
        x2, y2:  右下角坐标（图像像素）。
        padding: 在原始矩形四周额外扩展的像素数，防止污渍边缘擦过字段。
        label:   仅用于调试 / 可视化，不影响冲突判断逻辑。
    """

    x1: int
    y1: int
    x2: int
    y2: int
    padding: int = 30
    label: str = ""

    def expanded_bounds(self) -> tuple[int, int, int, int]:
        """返回含 padding 的扩展矩形 (ex1, ey1, ex2, ey2)"""
        return (
            self.x1 - self.padding,
            self.y1 - self.padding,
            self.x2 + self.padding,
            self.y2 + self.padding,
        )

    def conflicts(self, cx: float, cy: float, rx: int, ry: int) -> bool:
        """
        判断以 (cx, cy) 为中心、rx×ry 为半轴的椭圆是否与本保护区（含 padding）重叠。

        使用椭圆包围盒与矩形的 AABB 相交检测（保守估计，略大于实际椭圆）。
        对于安全性来说，宁可多排除一些区域也不要漏掉遮挡。
        """
        ex1, ey1, ex2, ey2 = self.expanded_bounds()
        # 椭圆与矩形无交集的条件（取反即为有交集）
        return not (cx + rx < ex1 or cx - rx > ex2 or cy + ry < ey1 or cy - ry > ey2)
