"""
Google One (Gemini) 学生验证工具
SheerID 学生验证 - 获取 Google One AI Premium

⚠️  重要提示 (2026年1月):
Google 已将 Gemini 学生验证限制为仅限美国新注册用户。
其他国家的用户可能会遇到较高的失败率。

增强功能:
- 按学校追踪成功率
- 加权大学选择（美国学校优先）
- 指数退避重试
- 限速规避
- 反检测（Chrome TLS 模拟）

依赖:
- curl_cffi: pip install curl_cffi（关键，用于 TLS 欺骗）
- 美国住宅代理（强烈推荐）

作者: ThanhNguyxn
"""

import argparse

from verifier import GeminiVerifier
from stats import stats


def main():
    """程序主入口 - 解析命令行参数并执行验证"""
    parser = argparse.ArgumentParser(
        description="Google One (Gemini) 学生验证工具"
    )
    parser.add_argument("url", nargs="?", help="验证链接 URL")
    parser.add_argument(
        "--proxy", help="代理服务器 (host:port 或 http://user:pass@host:port)"
    )
    parser.add_argument(
        "--force", action="store_true", help="强制运行，跳过警告"
    )
    args = parser.parse_args()

    # 打印程序横幅
    print()
    print("╔" + "═" * 56 + "╗")
    print("║" + " 🤖 Google One (Gemini) 验证工具".center(50) + "║")
    print("║" + " SheerID 学生优惠".center(52) + "║")
    print("╚" + "═" * 56 + "╝")
    print()

    # ⚠️ 仅限美国警告
    print("   " + "⚠" * 20)
    print("   ⚠️  重要警告 (2026年1月):")
    print("   ⚠️  Gemini 学生验证现在仅限美国！")
    print("   ⚠️  ")
    print("   ⚠️  成功的要求:")
    print("   ⚠️  1. 美国住宅代理（数据中心 IP 被阻止）")
    print("   ⚠️  2. 已安装 curl_cffi (pip install curl_cffi)")
    print("   ⚠️  3. 选择美国大学")
    print("   ⚠️  ")
    print("   ⚠️  非美国用户: 请考虑使用 perplexity-verify-tool")
    print("   ⚠️  或 spotify-verify-tool 代替。")
    print("   " + "⚠" * 20)
    print()

    # 确认继续
    if not args.force:
        confirm = input("   是否继续？(y/N): ").strip().lower()
        if confirm != "y":
            print("\n   已取消。使用 --force 跳过此警告。")
            return

    # 获取验证 URL
    if args.url:
        url = args.url
    else:
        url = input("\n   请输入验证链接 URL: ").strip()

    if not url or "sheerid.com" not in url:
        print("\n   ❌ URL 无效。必须包含 sheerid.com")
        return

    # 显示代理信息
    if args.proxy:
        print(f"   🔒 使用代理: {args.proxy}")
    else:
        print("   ⚠️  未指定代理！使用直接连接。")
        print("   ⚠️  这可能导致验证失败。")

    print("\n   ⏳ 处理中...")

    # 创建验证器并执行验证
    verifier = GeminiVerifier(url, proxy=args.proxy)

    # 首先检查链接有效性
    check = verifier.check_link()
    if not check.get("valid"):
        print(f"\n   ❌ 链接错误: {check.get('error')}")
        return

    # 执行验证
    result = verifier.verify()

    # 打印结果
    print()
    print("─" * 58)
    if result.get("success"):
        print("   🎉 验证成功！")
        print(f"   👤 {result.get('student')}")
        print(f"   📧 {result.get('email')}")
        print(f"   🏫 {result.get('school')}")
        print()
        print("   ✅ 无需审核 - 通过权威数据库验证！")
    elif result.get("pending"):
        print("   ⏳ 已提交审核")
        print(f"   👤 {result.get('student')}")
        print(f"   📧 {result.get('email')}")
        print(f"   🏫 {result.get('school')}")
        print()
        print("   ⚠️  文档已上传，等待审核 (24-48小时)")
        print("   ⚠️  这不保证一定成功！")
    else:
        print(f"   ❌ 失败: {result.get('error')}")
    print("─" * 58)

    # 打印统计信息
    stats.print_stats()


if __name__ == "__main__":
    main()
