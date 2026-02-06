"""
欺诈处理模块
处理 SheerID 欺诈规则拒绝
"""

FRAUD_ERROR_HELP = """\
🚨 检测到欺诈规则拒绝 (fraudRulesReject)

SheerID 的欺诈/风险引擎拒绝了此次尝试。这通常由以下一个或多个风险信号触发:
- TLS 指纹不匹配（Python HTTP 库 vs 真实浏览器）
- 数据中心 / 被标记的 IP 信誉
- 跨尝试重复使用的设备指纹 / 请求头 / NewRelic 模式
- 高重试频率或来自同一 IP 的重复失败
- 地理位置不匹配（IP 国家/地区 vs 组织）

✅ 解决方法（按顺序尝试）:
  1) 安装 curl_cffi 进行 TLS 伪装:
     pip install curl_cffi
  2) 使用住宅代理而非数据中心代理
  3) 等待 24-48 小时后再重试（风险分数通常会降低）
  4) 尝试不同的大学/组织（有些更严格）
  5) 检查您的 IP 是否被列入黑名单（如需要则更换 IP/提供商）

注意:
- 使用相同 IP + 指纹立即重试可能会使封锁持续更长时间。
- 如果无法安装 curl_cffi，预计欺诈拒绝率会高得多。
"""


def should_retry_fraud(retry_count: int):
    """判断在 fraudRulesReject 后是否应该重试。

    实现有上限的指数退避策略:
    - 30秒, 60秒, 120秒
    - 最多 3 次重试

    参数:
        retry_count: 已尝试的重试次数（从0开始）。

    返回:
        (should_retry, delay_seconds)
    """
    if retry_count < 0:
        retry_count = 0

    backoff_schedule = [30, 60, 120]

    if retry_count >= len(backoff_schedule):
        return False, 0

    return True, backoff_schedule[retry_count]


def handle_fraud_rejection(*, retry_count: int = 0, error_payload=None, message: str = None, ):
    """打印醒目的欺诈横幅和可操作的帮助信息，然后返回重试指导。

    此处理程序旨在当 SheerID 响应 `fraudRulesReject` 错误时调用。

    参数:
        retry_count: 已尝试的重试次数（从0开始）。
        error_payload: 可选的 API 错误 JSON 负载以显示（尽力而为）。
        message: 可选的人类可读消息/上下文以显示。

    返回:
        (should_retry, delay_seconds)
    """
    # ANSI 颜色（无外部依赖）。如果终端不支持 ANSI，输出仍然可读。
    red = "\x1b[31m"
    yellow = "\x1b[33m"
    cyan = "\x1b[36m"
    bold = "\x1b[1m"
    reset = "\x1b[0m"

    banner = "\n".join(
        [
            "+--------------------------------------------------------------+",
            "|                  !!! 检测到欺诈拦截 !!!                       |",
            "|               SheerID 返回 fraudRulesReject                   |",
            "+--------------------------------------------------------------+",
        ]
    )

    print(f"\n{red}{bold}{banner}{reset}")
    print(f"{yellow}❌ 验证被 SheerID 欺诈规则阻止。{reset}")

    if message:
        print(f"{cyan}🧾 上下文:{reset} {message}")

    # 尽力提取有用字段，不假设严格的模式。
    if isinstance(error_payload, dict) and error_payload:
        interesting_keys = ["code", "errorCode", "message", "detail", "details", "error", "errors", ]
        extracted = {}
        for k in interesting_keys:
            if k in error_payload and error_payload.get(k) not in (None, ""):
                extracted[k] = error_payload.get(k)

        if extracted:
            # 保持简洁，避免在控制台输出大量负载。
            print(f"{cyan}🔎 SheerID 错误负载（关键字段）:{reset}")
            for k, v in extracted.items():
                v_str = str(v)
                if len(v_str) > 400:
                    v_str = v_str[:400] + "..."
                print(f"  - {k}: {v_str}")

    print("\n" + "=" * 62)
    print(FRAUD_ERROR_HELP)
    print("=" * 62)

    should_retry, delay_seconds = should_retry_fraud(retry_count)
    if should_retry:
        print(
            f"{yellow}⏳ 建议重试:{reset} 第 #{retry_count + 1}/3 次，{delay_seconds}秒后"
        )
        print(
            f"{yellow}💡 提示:{reset} 重试前请更换 IP/指纹；避免快速连续重试。"
        )
    else:
        print(f"{red}🛑 已达最大重试次数。{reset} 请勿继续发送请求。")
        print(
            f"{yellow}✅ 最佳下一步:{reset} 等待 24-48 小时并更换 IP/指纹。"
        )

    return should_retry, delay_seconds
