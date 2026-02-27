"""
Google One (Gemini) 学生验证工具
SheerID 学生验证 - Google One AI Premium

⚠️  重要提示 (2026年1月):
Google 已将 Gemini 学生验证限制为仅限美国新注册用户
其他国家用户可能遇到较高的失败率

增强功能:
- 按组织追踪成功率
- 加权大学选择 (美国院校优先)
- 指数退避重试
- 反速率限制
- Chrome TLS 模拟反检测

依赖:
- curl_cffi: pip install curl_cffi (TLS 伪装必需)
- 匹配美国位置的住宅代理 (强烈推荐)

Author: ThanhNguyxn
"""

import argparse

from stats import stats
from verifier import GeminiVerifier


def main():
    parser = argparse.ArgumentParser(
        description="Google One (Gemini) 学生验证工具"
    )
    parser.add_argument("url", nargs="?", help="验证 URL")
    parser.add_argument(
        "--proxy", help="代理服务器 (host:port 或 http://user:pass@host:port)"
    )
    parser.add_argument(
        "--force", action="store_true", help="强制运行，跳过警告"
    )
    args = parser.parse_args()

    print()
    print("╔" + "═" * 56 + "╗")
    print("║" + " 🤖 Google One (Gemini) 验证工具".center(56) + "║")
    print("║" + " SheerID 学生优惠".center(56) + "║")
    print("╚" + "═" * 56 + "╝")
    print()

    # ⚠️ 仅限美国警告
    print("   " + "⚠" * 20)
    print("   ⚠️  重要警告 (2026年1月):")
    print("   ⚠️  Gemini 学生验证现已限制为仅限美国!")
    print("   ⚠️  ")
    print("   ⚠️  成功要求:")
    print("   ⚠️  1. 美国住宅代理 (数据中心 IP 被封禁)")
    print("   ⚠️  2. 已安装 curl_cffi (pip install curl_cffi)")
    print("   ⚠️  3. 美国大学选择")
    print("   ⚠️  ")
    print("   ⚠️  非美国用户: 建议使用 perplexity-verify-tool")
    print("   ⚠️  或 spotify-verify-tool 替代")
    print("   " + "⚠" * 20)
    print()

    if not args.force:
        confirm = input("   是否继续? (y/N): ").strip().lower()
        if confirm != "y":
            print("\n   已中止。使用 --force 跳过此警告")
            return

    # 获取 URL
    if args.url:
        url = args.url
    else:
        url = input("\n   请输入验证 URL: ").strip()

    if not url or "sheerid.com" not in url:
        print("\n   ❌ 无效 URL，必须包含 sheerid.com")
        return

    # 显示代理信息
    if args.proxy:
        print(f"   🔒 使用代理: {args.proxy}")
    else:
        print("   ⚠️  未指定代理! 使用直连")
        print("   ⚠️  可能导致验证失败")

    print("\n   ⏳ 处理中...")

    verifier = GeminiVerifier(url, proxy=args.proxy)

    # 先检查链接
    check = verifier.check_link()
    if not check.get("valid"):
        print(f"\n   ❌ 链接错误: {check.get('error')}")
        return

    result = verifier.verify()

    print()
    print("─" * 58)
    if result.get("success"):
        print("   🎉 立即验证成功!")
        print(f"   👤 {result.get('student')}")
        print(f"   📧 {result.get('email')}")
        print(f"   🏫 {result.get('school')}")
        print()
        print("   ✅ 无需审核 - 已通过权威数据库验证!")
    elif result.get("pending"):
        print("   ⏳ 已提交审核")
        print(f"   👤 {result.get('student')}")
        print(f"   📧 {result.get('email')}")
        print(f"   🏫 {result.get('school')}")
        print()
        print("   ⚠️  文档已上传，等待审核 (24-48小时)")
        print("   ⚠️  这不保证一定成功!")
    else:
        print(f"   ❌ 失败: {result.get('error')}")
    print("─" * 58)

    stats.print_stats()


if __name__ == "__main__":
    main()
