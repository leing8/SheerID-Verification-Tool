"""
成功率追踪
"""

import json
from pathlib import Path
from typing import Dict


class Stats:
    """按组织追踪成功率"""

    def __init__(self):
        self.file = Path(__file__).parent / "stats.json"
        self.data = self._load()

    def _load(self) -> Dict:
        if self.file.exists():
            try:
                return json.loads(self.file.read_text())
            except:
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
        print("\n📊 统计:")
        print(
            f"   Total: {self.data['total']} | ✅ {self.data['success']} | ❌ {self.data['failed']}"
        )
        if self.data["total"]:
            print(f"   成功率: {self.get_rate():.1f}%")


# 全局实例
stats = Stats()
