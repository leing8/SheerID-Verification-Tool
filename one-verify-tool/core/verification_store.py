"""
验证信息持久化模块 - 保存验证ID与学生信息的映射

解决问题:
当验证已经提交了个人信息（docUpload 步骤），但需要重新上传文档时，
需要使用之前提交的相同学生信息，否则会导致姓名不匹配。

使用方式:
- 首次提交时调用 save_verification_info() 保存信息
- 重试时调用 get_verification_info() 获取之前的信息
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class VerificationInfoStore:
    """
    验证信息存储器
    
    将验证 ID 与学生信息的映射持久化到本地文件
    """
    
    def __init__(self):
        # 存储路径
        self.store_dir = Path(__file__).parent / "verification_store"
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.store_file = self.store_dir / "verifications.json"
        
        # 加载现有数据
        self.data = self._load()
    
    def _load(self) -> Dict:
        """加载存储的数据"""
        if self.store_file.exists():
            try:
                with open(self.store_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save(self):
        """保存数据到文件"""
        with open(self.store_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def save_verification_info(self, verification_id: str, student_info: Dict):
        """
        保存验证信息
        
        Args:
            verification_id: SheerID 验证 ID
            student_info: 学生信息字典
        """
        self.data[verification_id] = {
            "timestamp": datetime.now().isoformat(),
            "first": student_info.get("first"),
            "last": student_info.get("last"),
            "email": student_info.get("email"),
            "dob": student_info.get("dob"),
            "org": {
                "id": student_info.get("org", {}).get("id"),
                "name": student_info.get("org", {}).get("name"),
                "domain": student_info.get("org", {}).get("domain"),
                "country": student_info.get("org", {}).get("country"),
            },
        }
        self._save()
        print(f"[持久化] 已保存验证信息: {verification_id[:20]}...")
    
    def get_verification_info(self, verification_id: str) -> Optional[Dict]:
        """
        获取之前保存的验证信息
        
        Args:
            verification_id: SheerID 验证 ID
            
        Returns:
            之前保存的学生信息，如果不存在则返回 None
        """
        stored = self.data.get(verification_id)
        if stored:
            print(f"[持久化] 找到已保存的验证信息: {stored['first']} {stored['last']}")
            return {
                "first": stored["first"],
                "last": stored["last"],
                "email": stored["email"],
                "dob": stored["dob"],
                "org": {
                    "id": stored["org"]["id"],
                    "name": stored["org"]["name"],
                    "domain": stored["org"]["domain"],
                    "country": stored["org"]["country"],
                    "idExtended": str(stored["org"]["id"]),
                },
            }
        return None
    
    def has_verification(self, verification_id: str) -> bool:
        """检查是否有该验证的保存信息"""
        return verification_id in self.data
    
    def delete_verification(self, verification_id: str):
        """删除验证信息"""
        if verification_id in self.data:
            del self.data[verification_id]
            self._save()
            print(f"[持久化] 已删除验证信息: {verification_id[:20]}...")
    
    def cleanup_old(self, days: int = 7):
        """清理过期的验证信息"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)
        
        to_delete = []
        for vid, info in self.data.items():
            try:
                ts = datetime.fromisoformat(info["timestamp"])
                if ts < cutoff:
                    to_delete.append(vid)
            except Exception:
                pass
        
        for vid in to_delete:
            del self.data[vid]
        
        if to_delete:
            self._save()
            print(f"[持久化] 清理了 {len(to_delete)} 条过期记录")


# 全局单例
verification_store = VerificationInfoStore()
