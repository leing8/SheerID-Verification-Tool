"""
Harvard 模板测试脚本
运行方式: python test_harvard_template.py
"""

import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from doc_generator.templates import harvard_template


def test_generate_transcript():
    """测试成绩单生成"""
    print("=" * 50)
    print("Harvard 成绩单模板测试")
    print("=" * 50)
    
    # 测试输出目录
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # 测试数据
    test_cases = [
        {"first": "Alice", "last": "Johnson", "dob": "2001-03-15", "seed": "test_seed_001"},
        {"first": "Bob", "last": "Smith", "dob": "2002-07-22", "seed": "test_seed_002"},
    ]
    
    for i, tc in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i}: {tc['first']} {tc['last']} ---")
        
        for fmt in ["png", "jpg", "pdf"]:
            try:
                data = harvard_template.generate_transcript(
                    first=tc["first"],
                    last=tc["last"],
                    school="Harvard University",
                    dob=tc["dob"],
                    seed=tc["seed"],
                    output_format=fmt
                )
                
                filename = output_dir / f"transcript_{tc['first'].lower()}_{tc['last'].lower()}.{fmt}"
                filename.write_bytes(data)
                print(f"  [OK] {fmt.upper()}: {len(data):,} bytes -> {filename.name}")
                
            except Exception as e:
                print(f"  [FAIL] {fmt.upper()}: {e}")
    
    print("\n" + "=" * 50)
    print(f"成绩单测试完成! 输出目录: {output_dir}")
    print("=" * 50)


def test_generate_student_id():
    """测试学生证生成"""
    print("=" * 50)
    print("Harvard 学生证模板测试")
    print("=" * 50)
    
    # 测试输出目录
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # 测试数据
    test_cases = [
        {"first": "Alice", "last": "Johnson", "seed": "test_seed_001"},
        {"first": "Bob", "last": "Smith", "seed": "test_seed_002"},
        {"first": "Charlie", "last": "Brown", "seed": "test_seed_003"},
    ]
    
    for i, tc in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i}: {tc['first']} {tc['last']} ---")
        
        for fmt in ["png", "jpg", "pdf"]:
            try:
                data = harvard_template.generate_student_id(
                    first=tc["first"],
                    last=tc["last"],
                    school="Harvard University",
                    seed=tc["seed"],
                    output_format=fmt
                )
                
                filename = output_dir / f"student_id_{tc['first'].lower()}_{tc['last'].lower()}.{fmt}"
                filename.write_bytes(data)
                print(f"  [OK] {fmt.upper()}: {len(data):,} bytes -> {filename.name}")
                
            except Exception as e:
                print(f"  [FAIL] {fmt.upper()}: {e}")
    
    print("\n" + "=" * 50)
    print(f"学生证测试完成! 输出目录: {output_dir}")
    print("=" * 50)


if __name__ == "__main__":
    test_generate_transcript()
    print("\n")
    test_generate_student_id()

