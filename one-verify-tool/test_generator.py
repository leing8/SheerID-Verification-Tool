#!/usr/bin/env python
"""
Harvard 成绩单生成测试入口

运行: python test_generator.py

用于测试和调整 Harvard 成绩单的生成位置
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generator import generate_harvard_transcript
from generator.student import generate_name, generate_birth_date


def main():
    print("\n" + "=" * 60)
    print("📄 Harvard 成绩单生成测试")
    print("=" * 60)
    
    # 生成测试用学生信息
    first, last = generate_name(include_middle=True)
    dob = generate_birth_date()
    
    print(f"\n👤 学生姓名: {first} {last}")
    print(f"🎂 出生日期: {dob}")
    
    # 生成 Harvard 成绩单
    # add_effects=False 关闭扫描效果便于检查位置
    data = generate_harvard_transcript(
        first=first,
        last=last,
        school="Harvard University",
        dob=dob,
        add_effects=False
    )
    
    # 保存文件
    output_path = "test_harvard_transcript.png"
    with open(output_path, 'wb') as f:
        f.write(data)
    
    abs_path = os.path.abspath(output_path)
    print(f"\n✅ 已生成: {abs_path}")
    print(f"   文件大小: {len(data):,} 字节")
    print(f"\n💡 提示: 打开文件检查内容位置是否正确")
    print(f"   位置调整: 编辑 generator/document.py 中的坐标注释")
    print()


if __name__ == "__main__":
    main()
