"""
统计追踪模块
按学校追踪验证成功率
"""

import json
from pathlib import Path
from typing import Dict


class Stats:
    """按学校追踪成功率"""

    def __init__(self):
        self.file = Path(__file__).parent / "stats.json"
        self.data = self._load()

    def _load(self) -> Dict:
        if self.file.exists():
            try:
                return json.loads(self.file.read_text())
            except Exception:
                pass
        return {"total": 0, "success": 0, "failed": 0, "orgs": {}}

    def _save(self):
        self.file.write_text(json.dumps(self.data, indent=2))

    def record(self, org: str, success: bool):
        self.data["total"] += 1
        self.data["success" if success else "failed"] += 1

        if org not in self.data["orgs"]:
            self.data["orgs"][org] = {"success": 0, "failed": 0}
        self.data["orgs"][org]["success" if success else "failed"] += 1
        self._save()

    def get_rate(self, org: str = None) -> float:
        if org:
            o = self.data["orgs"].get(org, {})
            total = o.get("success", 0) + o.get("failed", 0)
            return o.get("success", 0) / total * 100 if total else 50
        return (
            self.data["success"] / self.data["total"] * 100 if self.data["total"] else 0
        )

    def print_stats(self):
        print(f"\n📊 统计信息:")
        print(
            f"   总计: {self.data['total']} | ✅ 成功: {self.data['success']} | ❌ 失败: {self.data['failed']}"
        )
        if self.data["total"]:
            print(f"   成功率: {self.get_rate():.1f}%")


# 全局统计实例
stats = Stats()
