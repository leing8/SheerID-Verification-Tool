"""
调试日志模块 - 保存验证过程中的所有数据用于问题排查

功能:
- 保存生成的学生信息
- 保存生成的文档图片
- 保存请求/响应数据
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class DebugLogger:
    """
    调试日志记录器
    
    保存验证过程中的所有数据到 logs/ 目录
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.session_id = None
        self.session_dir = None
        
        if enabled:
            self._init_session()
    
    def _init_session(self):
        """初始化调试会话"""
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建日志目录
        base_dir = Path(__file__).parent / "logs"
        self.session_dir = base_dir / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[调试日志] 会话目录: {self.session_dir}")
    
    def log_student_info(self, student_info: Dict):
        """保存学生信息"""
        if not self.enabled:
            return
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "first": student_info.get("first"),
            "last": student_info.get("last"),
            "email": student_info.get("email"),
            "dob": student_info.get("dob"),
            "org": {
                "name": student_info.get("org", {}).get("name"),
                "domain": student_info.get("org", {}).get("domain"),
                "id": student_info.get("org", {}).get("id"),
                "country": student_info.get("org", {}).get("country"),
            },
        }
        
        path = self.session_dir / "student_info.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[调试日志] 学生信息已保存: {path}")
    
    def log_document(self, doc_bytes: bytes, filename: str):
        """保存生成的文档"""
        if not self.enabled:
            return
        
        path = self.session_dir / f"document_{filename}"
        with open(path, "wb") as f:
            f.write(doc_bytes)
        
        print(f"[调试日志] 文档已保存: {path} ({len(doc_bytes):,} bytes)")
    
    def log_request(self, method: str, endpoint: str, body: Optional[Dict] = None):
        """记录请求"""
        if not self.enabled:
            return
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "request",
            "method": method,
            "endpoint": endpoint,
            "body": body,
        }
        
        self._append_to_log("requests.jsonl", log_entry)
    
    def log_response(self, endpoint: str, status: int, data: Any):
        """记录响应"""
        if not self.enabled:
            return
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "response",
            "endpoint": endpoint,
            "status": status,
            "data": data if isinstance(data, dict) else str(data),
        }
        
        self._append_to_log("requests.jsonl", log_entry)
    
    def log_error(self, error_type: str, message: str, details: Optional[Dict] = None):
        """记录错误"""
        if not self.enabled:
            return
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "error",
            "error_type": error_type,
            "message": message,
            "details": details,
        }
        
        self._append_to_log("errors.jsonl", log_entry)
        
        # 同时写入人类可读的错误文件
        error_file = self.session_dir / "last_error.txt"
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(f"Error Type: {error_type}\n")
            f.write(f"Message: {message}\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            if details:
                f.write(f"\nDetails:\n{json.dumps(details, indent=2, ensure_ascii=False)}\n")
    
    def log_result(self, result: Dict):
        """记录最终结果"""
        if not self.enabled:
            return
        
        result_with_time = {
            "timestamp": datetime.now().isoformat(),
            **result,
        }
        
        path = self.session_dir / "result.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result_with_time, f, indent=2, ensure_ascii=False)
        
        print(f"[调试日志] 结果已保存: {path}")
    
    def _append_to_log(self, filename: str, entry: Dict):
        """追加日志条目"""
        path = self.session_dir / filename
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def get_session_path(self) -> Optional[Path]:
        """获取当前会话路径"""
        return self.session_dir


# 全局调试日志实例
debug_logger = DebugLogger(enabled=True)
