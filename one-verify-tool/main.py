"""
Google One (Gemini) 学生验证工具
SheerID 学生验证 - Google One AI Premium

⚠️  重要提示 (2026年1月):
Google 已将 Gemini 学生验证限制为仅限美国新注册用户
其他国家用户可能遇到较高的失败率

增强功能:
- 加权大学选择 (美国院校优先)
- 反速率限制
- Chrome TLS 模拟反检测
- 文档审查自动轮询

依赖:
- curl_cffi: pip install curl_cffi (TLS 伪装必需)
- 匹配美国位置的住宅代理 (强烈推荐)

Author: ThanhNguyxn
"""

import argparse

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
    parser.add_argument(
        "--poll",
        action="store_true",
        help="进入 pending 后自动轮询审查结果 (无需手动交互)",
    )
    parser.add_argument(
        "--poll-timeout",
        type=int,
        default=60,
        metavar="MINUTES",
        help="--poll 的最长等待时间（分钟，默认 60）",
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

    if not url or "sheerid.com" not in url or "verificationId=" not in url:
        print("\n   ❌ 无效 URL，必须包含 sheerid.com 且带有 verificationId= 参数")
        print("   示例: https://services.sheerid.com/verify/...?verificationId=abcdef...")
        return

    # 显示代理信息
    if args.proxy:
        proxy_display = args.proxy
        if not proxy_display.startswith("http"):
            print("   ⚠️  代理缺少 scheme，尝试自动补全 http://")
            proxy_display = "http://" + proxy_display
            args.proxy = proxy_display
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

    # ── 处理 pending：询问是否轮询 ─────────────────────────────────────────
    if result.get("pending") and not result.get("timed_out"):
        print()
        print("─" * 58)
        print("   ⏳ 文档已提交审核")
        print(f"   👤 {result.get('student')}")
        print(f"   📧 {result.get('email')}")
        print(f"   🏫 {result.get('school')}")
        print()

        do_poll = args.poll
        if not do_poll:
            ans = input(
                f"   是否启动自动轮询等待审查结果? (最长 {args.poll_timeout} 分钟) [y/N]: "
            ).strip().lower()
            do_poll = ans == "y"

        if do_poll:
            result = verifier._poll_result(
                status_url=result.get("status_url"),
                max_wait_minutes=args.poll_timeout,
                interval_seconds=30,
            )
        else:
            print()
            print("   ⚠️  文档已上传，等待审核 (24-48小时)")
            print("   ⚠️  审核结果将通过邮件通知")
            print("   ⚠️  下次可使用 --poll 参数自动等待结果")
            print("─" * 58)
            return

    # ── 打印最终结果 ──────────────────────────────────────────────────────
    print()
    print("─" * 58)
    if result.get("success"):
        print("   🎉 验证成功!")
        if result.get("student"):
            print(f"   👤 {result.get('student')}")
        if result.get("email"):
            print(f"   📧 {result.get('email')}")
        if result.get("school"):
            print(f"   🏫 {result.get('school')}")
        if result.get("rewardCode"):
            print(f"   🎁 奖励码: {result.get('rewardCode')}")
        print()
        print(f"   ✅ {result.get('message', '验证已通过')}")
    elif result.get("pending") and result.get("timed_out"):
        print("   ⏰ 轮询超时")
        print("   ⚠️  审核仍在进行中，请稍后查看邮件")
    elif result.get("attempts_exhausted"):
        print("   🚫 验证彻底失败")
        print(f"   ❌ {result.get('error')}")
    elif result.get("needs_reupload"):
        print("   🔄 需要重新上传文档")
        print(f"   ❌ {result.get('error')}")
    elif result.get("unknown"):
        print(f"   ❓ 未知状态: {result.get('message')}")
        if result.get("student"):
            print(f"   👤 {result.get('student')}")
        if result.get("email"):
            print(f"   📧 {result.get('email')}")
        if result.get("school"):
            print(f"   🏫 {result.get('school')}")
        print()
        print("   ⚠️  请登录 SheerID 手动确认验证状态")
    else:
        print(f"   ❌ 失败: {result.get('error')}")
        if result.get("system_message"):
            print(f"   ℹ️  系统消息: {result.get('system_message')}")
    print("─" * 58)


if __name__ == "__main__":
    main()
