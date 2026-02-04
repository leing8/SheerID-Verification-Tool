"""
统计模块 - 验证成功率追踪

包含:
- Stats 类: 按学校追踪验证成功率
- stats 全局实例: 供其他模块使用
"""

import json
from pathlib import Path
from typing import Dict


class Stats:
    """
    统计追踪类 - 按学校记录验证成功率
    
    数据存储在 stats.json 文件中，包含:
    - 总计数、成功数、失败数
    - 每个学校的成功/失败统计
    """

    def __init__(self):
        """初始化统计追踪器，从文件加载已有数据"""
        self.file = Path(__file__).parent / "stats.json"
        self.data = self._load()

    def _load(self) -> Dict:
        """
        从文件加载统计数据
        
        Returns:
            Dict: 统计数据字典，包含 total, success, failed, orgs
        """
        if self.file.exists():
            try:
                return json.loads(self.file.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        return {"total": 0, "success": 0, "failed": 0, "orgs": {}}

    def _save(self):
        """保存统计数据到文件"""
        self.file.write_text(json.dumps(self.data, indent=2))

    def record(self, org: str, success: bool):
        """
        记录一次验证结果
        
        Args:
            org: 学校名称
            success: 是否验证成功
        """
        self.data["total"] += 1
        self.data["success" if success else "failed"] += 1

        if org not in self.data["orgs"]:
            self.data["orgs"][org] = {"success": 0, "failed": 0}
        self.data["orgs"][org]["success" if success else "failed"] += 1
        self._save()

    def get_rate(self, org: str = None) -> float:
        """
        获取成功率百分比
        
        Args:
            org: 学校名称，为 None 时返回总体成功率
            
        Returns:
            float: 成功率百分比 (0-100)，无数据时返回 50（中性值）或 0
        """
        if org:
            o = self.data["orgs"].get(org, {})
            total = o.get("success", 0) + o.get("failed", 0)
            # 无数据时返回 50%（中性值），避免新学校权重过低
            return o.get("success", 0) / total * 100 if total else 50
        return (
            self.data["success"] / self.data["total"] * 100 if self.data["total"] else 0
        )

    def print_stats(self):
        """打印统计摘要到控制台"""
        print(f"\n📊 统计信息:")
        print(
            f"   总计: {self.data['total']} | ✅ 成功: {self.data['success']} | ❌ 失败: {self.data['failed']}"
        )
        if self.data["total"]:
            print(f"   成功率: {self.get_rate():.1f}%")


# 全局单例实例，供其他模块使用
stats = Stats()
