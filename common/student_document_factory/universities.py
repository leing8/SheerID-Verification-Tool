"""
大学数据定义

仅保留5所顶尖美国大学的CS相关专业，每所学校含：
- 基本信息 (id, name, domain)
- 可用状态 (enabled)
- 专业列表 (programs)
- 4种文档类型的可用状态 (doc_availability)
"""

from enum import Enum
from typing import Dict, List


class DocumentType(str, Enum):
    """支持的文档类型"""
    TRANSCRIPT = "transcript"   # 学术成绩单
    INVOICE    = "invoice"      # 学费发票
    SCHEDULE   = "schedule"     # 课程表
    STUDENT_ID = "student_id"   # 学生证


UNIVERSITIES: List[Dict] = [
    {
        "id": 3113,
        "name": "Stanford University",
        "domain": "stanford.edu",
        "enabled": False,
        "programs": [
            "Computer Science (B.S.)",
            "Computer Science (M.S.)",
            "Computer Science (Ph.D.)",
        ],
        "doc_availability": {
            DocumentType.TRANSCRIPT: True,
            DocumentType.INVOICE:    True,
            DocumentType.SCHEDULE:   True,
            DocumentType.STUDENT_ID: True,
        },
    },
    {
        "id": 3491,
        "name": "University of California, Berkeley",
        "domain": "berkeley.edu",
        "enabled": False,
        "programs": [
            "Electrical Engineering and Computer Sciences (B.S.)",
            "Computer Science (B.A.)",
            "Computer Science (M.S.)",
            "Computer Science (Ph.D.)",
        ],
        "doc_availability": {
            DocumentType.TRANSCRIPT: True,
            DocumentType.INVOICE:    True,
            DocumentType.SCHEDULE:   True,
            DocumentType.STUDENT_ID: True,
        },
    },
    {
        "id": 1953,
        "name": "Massachusetts Institute of Technology",
        "domain": "mit.edu",
        "enabled": False,
        "programs": [
            "Artificial Intelligence and Decision Making (B.S., Course 6-4 / VI-4)",
            "Computer Science and Engineering (B.S., Course 6-3 / VI-3)",
            "Electrical Engineering and Computer Science (M.Eng.)",
            "Electrical Engineering and Computer Science (S.M.)",
            "Electrical Engineering and Computer Science (Ph.D.)",
        ],
        "doc_availability": {
            DocumentType.TRANSCRIPT: True,
            DocumentType.INVOICE:    True,
            DocumentType.SCHEDULE:   True,
            DocumentType.STUDENT_ID: True,
        },
    },
    {
        "id": 3761,
        "name": "University of Washington",
        "domain": "uw.edu",
        "enabled": False,
        "programs": [
            "Computer Science (B.S.)",
            "Computer Engineering (B.S.)",
            "Computer Science & Engineering (M.S.)",
            "Computer Science & Engineering (Ph.D.)",
        ],
        "doc_availability": {
            DocumentType.TRANSCRIPT: True,
            DocumentType.INVOICE:    True,
            DocumentType.SCHEDULE:   True,
            DocumentType.STUDENT_ID: True,
        },
    },
    {
        "id": 1426,
        "name": "Harvard University",
        "domain": "harvard.edu",
        "enabled": True,
        "programs": [
            "Computer Science (A.B.)",
            "Computer Science (S.M.)",
            "Computer Science (Ph.D.)",
            "Data Science (S.M.)",
        ],
        "doc_availability": {
            DocumentType.TRANSCRIPT: True,
            DocumentType.INVOICE:    True,
            DocumentType.SCHEDULE:   False,   # 哈佛仅开放3种文档
            DocumentType.STUDENT_ID: True,
        },
    },
]

# 仅包含 enabled=True 且至少有一种可用文档的大学
ENABLED_UNIVERSITIES = [
    u for u in UNIVERSITIES
    if u["enabled"] and any(u["doc_availability"].values())
]


def get_available_doc_types(university: Dict) -> List[DocumentType]:
    """返回指定大学的可用文档类型列表"""
    return [
        doc_type
        for doc_type, available in university["doc_availability"].items()
        if available
    ]
