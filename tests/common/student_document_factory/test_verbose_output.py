"""
test_verbose_output.py — 学生文档工厂完整信息输出测试

运行时使用 -s 参数查看完整输出:
    pytest tests/common/student_document_factory/test_verbose_output.py -v -s

生成的文档保存在 tests/output/student_documents/ 目录中，可直接打开查看。
"""

from pathlib import Path

import pytest

# 输出目录：tests/output/student_documents/
_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output" / "student_documents"


class TestStudentDataVerboseOutput:
    """输出完整学生数据信息，便于人工检查"""

    def test_full_student_data_output(self, sample_harvard_data):
        """输出完整的哈佛学生数据"""
        s = sample_harvard_data

        print("\n" + "=" * 72)
        print("  哈佛学生数据完整信息")
        print("=" * 72)

        # 基本信息
        print(f"\n── 基本信息 ──")
        print(f"  First Name          : {s.first_name}")
        print(f"  Last Name           : {s.last_name}")
        print(f"  Email               : {s.email}")
        print(f"  Birth Date          : {s.birth_date}")

        # 学校信息
        print(f"\n── 学校信息 ──")
        print(f"  Program             : {s.program}")
        print(f"  School Code         : {s.school_code}")
        print(f"  Student ID          : {s.student_id}")
        print(f"  Enrollment Year     : {s.enrollment_year}")
        print(f"  GPA                 : {s.gpa}")
        print(f"  Term                : {s.term}")

        # 课程信息
        print(f"\n── 课程列表 ({len(s.courses)} 门) ──")
        print(f"  {'Code':<15} {'Title':<42} {'Cr':>3} {'Grade':>5} {'Lv':>3}")
        print(f"  {'-'*15} {'-'*42} {'-'*3} {'-'*5} {'-'*3}")
        for code, title, credits, grade, level in s.courses:
            print(f"  {code:<15} {title:<42} {credits:>3} {grade:>5} {level:>3}")

        # 学费信息
        total = s.tuition_amount + s.fee_health + s.fee_activity + s.fee_gsc
        print(f"\n── 学费明细 ──")
        print(f"  Tuition             : ${s.tuition_amount:,}.00")
        print(f"  Health Insurance    : ${s.fee_health:,}.00")
        print(f"  Activities Fee      : ${s.fee_activity:,}.00")
        print(f"  GSC Fee             : ${s.fee_gsc:,}.00")
        print(f"  ─────────────────────────────")
        print(f"  Total               : ${total:,}.00")

        # 发票信息
        print(f"\n── 发票信息 ──")
        print(f"  Invoice Number      : {s.invoice_number}")

        # 地址信息
        print(f"\n── 地址信息 ──")
        for i, line in enumerate(s.address, 1):
            print(f"  Line {i}              : {line}")

        print("\n" + "=" * 72)


class TestDocumentGenerationVerboseOutput:
    """生成文档并保存到磁盘，可直接打开查看"""

    def test_full_document_output(self, sample_harvard_data):
        """生成所有文档，保存到 tests/output/student_documents/ 并输出文件路径"""
        from student_document_factory.schools.harvard.documents import (
            generate_invoice,
            generate_student_id_card,
            generate_transcript,
        )

        s = sample_harvard_data

        # 创建输出目录
        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        print("\n" + "=" * 72)
        print("  文档生成 — 保存到磁盘")
        print("=" * 72)
        print(f"  Student: {s.first_name} {s.last_name} (ID: {s.student_id})")
        print(f"  Output:  {_OUTPUT_DIR}")
        print()

        docs = [
            ("transcript.png", "成绩单", generate_transcript),
            ("invoice.png", "学费发票", generate_invoice),
            ("student_id.png", "学生证", generate_student_id_card),
        ]

        print(f"  {'Filename':<20} {'Type':<10} {'Size':>12} {'Format':>8}")
        print(f"  {'-'*20} {'-'*10} {'-'*12} {'-'*8}")

        saved_paths = []
        for filename, doc_type, generator in docs:
            data = generator(s)
            size = len(data)
            fmt = "PNG" if data[:4] == b'\x89PNG' else "JPEG" if data[:2] == b'\xff\xd8' else "?"

            # 保存文件
            filepath = _OUTPUT_DIR / filename
            filepath.write_bytes(data)
            saved_paths.append(filepath)

            print(f"  {filename:<20} {doc_type:<10} {size:>10,} B {fmt:>8}")

        print(f"\n  ✅ {len(saved_paths)} 个文档已保存，可直接打开查看：")
        for p in saved_paths:
            print(f"     file:///{p.as_posix()}")
        print()


class TestStudentInfoFactoryVerboseOutput:
    """输出 StudentInfoFactory 集成信息"""

    def test_factory_full_output(self, student_factory):
        """输出工厂完整输出信息"""
        print("\n" + "=" * 72)
        print("  StudentInfoFactory 多 VID 输出对比")
        print("=" * 72)

        print(
            f"\n  {'VID':<28} {'Name':<22} {'Program':<26} "
            f"{'Docs':>4} {'Total Size':>12}"
        )
        print(
            f"  {'-'*28} {'-'*22} {'-'*26} "
            f"{'-'*4} {'-'*12}"
        )

        for i in range(8):
            vid = f"verbose-factory-test-{i:04d}"
            info = student_factory.create(vid)
            name = f"{info.first_name} {info.last_name}"
            total_size = sum(len(d) for _, d in info.documents)
            doc_names = ", ".join(f for f, _ in info.documents)

            print(
                f"  {vid:<28} {name:<22} {info.program:<26} "
                f"{len(info.documents):>4} {total_size:>10,} B"
            )

        print()

    def test_single_student_complete_output(self, student_factory, sample_vid):
        """输出单个学生的完整信息（数据 + 文档）"""
        info = student_factory.create(sample_vid)

        print("\n" + "=" * 72)
        print("  StudentInfoFactory 完整输出")
        print("=" * 72)

        print(f"\n── 学生信息 ──")
        print(f"  Verification ID     : {sample_vid}")
        print(f"  Name                : {info.first_name} {info.last_name}")
        print(f"  Email               : {info.email}")
        print(f"  Birth Date          : {info.birth_date}")
        print(f"  Program             : {info.program}")

        print(f"\n── 大学信息 ──")
        for key, value in info.university.items():
            print(f"  {key:<20} : {value}")

        print(f"\n── 文档信息 ({len(info.documents)} 个) ──")
        for filename, data in info.documents:
            fmt = "PNG" if data[:4] == b'\x89PNG' else "JPEG" if data[:2] == b'\xff\xd8' else "?"
            print(f"  {filename:<20} : {len(data):>10,} bytes ({fmt})")

        print("\n" + "=" * 72)
