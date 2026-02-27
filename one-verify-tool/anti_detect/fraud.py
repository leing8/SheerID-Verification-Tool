"""
反检测模块 - 欺诈拒绝处理

SheerID 欺诈规则拒绝的诊断、建议和重试逻辑。
"""

FRAUD_ERROR_HELP = """\
🚨 检测到欺诈规则拒绝 (fraudRulesReject)

SheerID 的欺诈/风控引擎拒绝了此次尝试。通常由以下风险信号触发:
- TLS 指纹不匹配 (Python HTTP 库 vs 真实浏览器)
- 数据中心 / 被标记的 IP 声誉
- 多次尝试复用设备指纹 / 请求头 / NewRelic 模式
- 同一 IP 重试速度过快或重复失败
- 地理位置不匹配 (IP 国家/地区 vs 组织)

✅ 建议解决方案 (按优先级):
  1) 安装 curl_cffi 进行 TLS 伪装:
     pip install curl_cffi
  2) 使用住宅代理替代数据中心代理
  3) 等待 24-48 小时后重试 (风险评分通常会冷却)
  4) 尝试不同的大学/组织 (部分更严格)
  5) 检查 IP 是否被拉黑 (必要时更换 IP/提供商)

注意:
- 使用相同 IP + 指纹立即重试可能导致封禁时间延长
- 未安装 curl_cffi 时欺诈拒绝率会显著增加
"""


def should_retry_fraud(retry_count: int):
    """判断欺诈拒绝后是否重试，使用指数退避调度: 30s, 60s, 120s，最多3次"""
    if retry_count < 0:
        retry_count = 0

    backoff_schedule = [30, 60, 120]

    if retry_count >= len(backoff_schedule):
        return False, 0

    return True, backoff_schedule[retry_count]


def handle_fraud_rejection(
    *,
    retry_count: int = 0,
    error_payload=None,
    message: str = None,
):
    """打印欺诈拒绝横幅 + 可操作建议，并返回重试指导

    Args:
        retry_count: 已重试次数 (0开始)
        error_payload: API 错误 JSON 负载 (可选)
        message: 人类可读的上下文信息 (可选)

    Returns:
        (should_retry, delay_seconds)
    """
    # ANSI 颜色 (无外部依赖，终端不支持 ANSI 也可正常显示)
    red = "\x1b[31m"
    yellow = "\x1b[33m"
    cyan = "\x1b[36m"
    bold = "\x1b[1m"
    reset = "\x1b[0m"

    banner = "\n".join(
        [
            "+--------------------------------------------------------------+",
            "|                  !!! 欺诈检测触发 !!!                    |",
            "|              SheerID 返回 fraudRulesReject                 |",
            "+--------------------------------------------------------------+",
        ]
    )

    print(f"\n{red}{bold}{banner}{reset}")
    print(f"{yellow}❌ 验证被 SheerID 欺诈规则拦截{reset}")

    if message:
        print(f"{cyan}🧾 上下文:{reset} {message}")

    # 尽力提取有用的错误字段
    if isinstance(error_payload, dict) and error_payload:
        interesting_keys = [
            "code",
            "errorCode",
            "message",
            "detail",
            "details",
            "error",
            "errors",
        ]
        extracted = {}
        for k in interesting_keys:
            if k in error_payload and error_payload.get(k) not in (None, ""):
                extracted[k] = error_payload.get(k)

        if extracted:
            # 保持简洁，避免输出过大的负载
            print(f"{cyan}🔎 SheerID 错误负载 (关键字段):{reset}")
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
        print(f"{yellow}⏳ 建议重试:{reset} 第 {retry_count + 1}/3 次，{delay_seconds}秒后")
        print(f"{yellow}💡 提示:{reset} 重试前建议更换 IP/指纹，避免快速重试")
    else:
        print(f"{red}🛑 达到最大重试次数{reset}，请勿继续发送请求")
        print(f"{yellow}✅ 最佳下一步:{reset} 等待 24-48 小时并更换 IP/指纹")

    return should_retry, delay_seconds
