"""
StudentInfoFactory — 学生信息工厂（学校模块化版本）

通过学校模块注册表调度各校专属实现：
  - 工厂从 ENABLED_UNIVERSITIES 中确定性选择已启用学校
  - 将学生数据生成和文档生成委托给对应的 SchoolModule
  - 对外接口保持不变（StudentInfo、StudentInfoFactory）
"""

import hashlib
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .interfaces import SchoolModule
# ── 学校模块注册表（仅注册已实现的学校）──
from .schools.harvard import HarvardModule
from .universities import ENABLED_UNIVERSITIES, get_available_doc_types

logger = logging.getLogger(__name__)

_SCHOOL_MODULES: Dict[int, SchoolModule] = {
    1426: HarvardModule(),   # Harvard University
    # 未来扩展：
    # 3113: StanfordModule(),
    # 3491: BerkeleyModule(),
    # 1953: MITModule(),
    # 3761: UWModule(),
}


@dataclass
class StudentInfo:
    """工厂返回的完整学生信息"""
    first_name: str
    last_name:  str
    email:      str
    birth_date: str
    university: Dict                              # id, idExtended, name, domain
    program:    str
    documents:  List[Tuple[str, bytes]] = field(default_factory=list)
    # [(文件名, PNG字节), ...]，长度满足 2 <= len <= 该校可用文档数


class StudentInfoFactory:
    """
    基于 verificationId 的学生信息工厂（模块化版本）。

    相同 verificationId → 相同学校、专业、学生数据（确定性）。
    学生数据生成 & 文档生成均由各校 SchoolModule 负责。
    """

    def _seeded_random(self, verification_id: str) -> random.Random:
        seed = int(hashlib.sha256(verification_id.encode()).hexdigest(), 16) % (2 ** 32)
        return random.Random(seed)

    def create(
        self,
        verification_id: str,
        *,
        fetch_avatar: bool = True,
    ) -> StudentInfo:
        """
        生成完整学生信息及文档。

        Args:
            verification_id: 验证 ID（确定性种子）
            fetch_avatar:    是否从网络获取头像（默认 True，测试可关闭）

        Steps:
          1. 基于 SHA-256(vid) 创建 seeded rng
          2. 从 ENABLED_UNIVERSITIES 确定性选择学校
          3. 从专业列表确定性选择专业
          4. 确定文档数量（2 <= count <= 可用文档数）
          5. 确定性选择文档类型组合
          6. 通过 SchoolModule 生成学生数据和各文档
          7. 返回 StudentInfo
        """
        start = time.monotonic()
        logger.info(
            "开始生成学生信息: vid=%s..., fetch_avatar=%s",
            verification_id[:16], fetch_avatar,
        )
        rng = self._seeded_random(verification_id)

        # 1. 选择学校（从已启用列表）
        university = rng.choice(ENABLED_UNIVERSITIES)
        logger.info(
            "[步骤1/7] 学校选择: id=%d, name=%s",
            university["id"], university["name"],
        )

        # 2. 获取该校的 SchoolModule
        module = _SCHOOL_MODULES.get(university["id"])
        if module is None:
            raise RuntimeError(
                f"No SchoolModule registered for university id={university['id']} "
                f"({university['name']}). Please implement and register a module."
            )

        # 3. 选择专业
        program = rng.choice(university["programs"])
        logger.debug("[步骤2/7] 专业选择: %s", program)

        # 4. 获取可用文档类型 & 确定数量
        available_types = get_available_doc_types(university)
        max_docs = max(len(available_types), 2)
        doc_count = rng.randint(2, max_docs)
        logger.debug(
            "[步骤3/7] 文档规划: 可用类型=%s, 生成数量=%d",
            [t.value for t in available_types], doc_count,
        )

        # 5. 确定性选择文档类型
        selected_types = rng.sample(available_types, doc_count)
        logger.info(
            "[步骤4/7] 选中文档类型: %s",
            [t.value for t in selected_types],
        )

        # 6. 通过 SchoolModule 生成学生数据（传入 program 以便哈佛选择对应课程）
        student_data = module.generate_student_data(verification_id, program=program)
        logger.info(
            "[步骤5/7] 学生数据: name=%s %s, email=%s, student_id=%s",
            student_data.first_name, student_data.last_name,
            student_data.email, student_data.student_id,
        )

        # 7. 生成文档
        documents: List[Tuple[str, bytes]] = []
        for i, doc_type in enumerate(selected_types):
            doc_start = time.monotonic()
            result = module.generate_document(
                doc_type, student_data, fetch_avatar=fetch_avatar,
            )
            doc_ms = (time.monotonic() - doc_start) * 1000
            documents.append((result.filename, result.data))
            logger.info(
                "[步骤6/7] 文档生成 %d/%d: type=%s, file=%s, size=%.1fKB, cost=%.0fms",
                i + 1, len(selected_types), doc_type.value,
                result.filename, len(result.data) / 1024, doc_ms,
            )

        total_ms = (time.monotonic() - start) * 1000
        logger.info(
            "[步骤7/7] 学生信息生成完成: 文档数=%d, 总耗时=%.0fms",
            len(documents), total_ms,
        )

        return StudentInfo(
            first_name=student_data.first_name,
            last_name=student_data.last_name,
            email=student_data.email,
            birth_date=student_data.birth_date,
            university={
                "id":         university["id"],
                "idExtended": str(university["id"]),
                "name":       university["name"],
                "domain":     university["domain"],
            },
            program=program,
            documents=documents,
        )
