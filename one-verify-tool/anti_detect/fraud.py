"""
反检测模块 - 欺诈拒绝处理

SheerID 欺诈规则拒绝（fraudRulesReject）的诊断与建议输出。

官方参考：
- https://developer.sheerid.com/concepts (Errors 章节)
- https://developer.sheerid.com/rest-api (verification response errorIds)
"""

# 官方文档说明：
# currentStep="error" + errorIds=["fraudRulesReject"] 是不可恢复错误（non-recoverable）。
# 官方明确："某些罕见错误不可恢复，需要重新开始验证流程（start a new verification）"。
# 因此：不应对同一 verificationId 进行任何重试。
FRAUD_ERROR_HELP = """\
📋 SheerID 官方文档参考 (fraudRulesReject):

  错误性质: 不可恢复 (non-recoverable)
  官方处置: 必须重新发起验证 (new verification)，不得对同一
            verificationId 重试，否则风险评分只会升高。

可能触发 Fraud Rules Engine 的原因 (来自 SheerID 官方文档):

  [风险信号]
  1. TLS/JA3 指纹不匹配
     - Python 默认 HTTP 库 (requests/httpx) 与真实 Chrome 指纹不同
     - 解决: 使用 curl_cffi 并指定 impersonate="chromeXXX"

  2. IP 声誉 / 数据中心 IP
     - SheerID ADP（受众数据平台）会分析请求的 IP 地理位置和声誉
     - 解决: 改用美国住宅代理（residential proxy）

  3. 数字上下文信号异常
     - SheerID AI 模型会在提交时评估 User-Agent、Accept-Language、
       Sec-Ch-Ua 等浏览器上下文指纹
     - 解决: 确保设备指纹与 TLS 版本、UA 版本三者一致

  4. 重复失败 / 速率触发
     - 同 IP 对同一 program 多次失败会触发渐进式风险规则
     - 解决: 更换 IP，等待风险评分冷却（官方建议 24-48 小时）

  5. 地理位置不匹配
     - IP 归属国家/地区与填报的学校或机构不符
     - 解决: 代理 IP 应与目标大学所在地一致（美国大学 → 美国 IP）

  ✅ 官方最佳实践:
     - 每次验证必须使用全新 verificationId
     - 确保 curl_cffi TLS 指纹 ↔ 设备 UA ↔ 请求头版本三一致
     - 使用住宅代理并验证 IP 归属国为美国
"""


def handle_fraud_rejection(
    *,
    error_payload=None,
    message: str = None,
) -> None:
    """输出 fraudRulesReject 诊断横幅与官方文档对齐的解决建议。

    Args:
        error_payload: API 错误 JSON 负载（可选），用于提取关键字段
        message:       人类可读的上下文信息（可选）

    Notes:
        fraudRulesReject 是 SheerID 官方定义的不可恢复错误。
        此函数仅负责诊断输出，不返回重试指导。
        调用方应放弃当前 verificationId，重新发起新验证。
    """
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
            "|         此为不可恢复错误，当前验证已终止                  |",
            "+--------------------------------------------------------------+",
        ]
    )

    print(f"\n{red}{bold}{banner}{reset}")
    print(f"{yellow}❌ 验证被 SheerID Fraud Rules Engine 拦截{reset}")

    if message:
        print(f"{cyan}🧾 上下文:{reset} {message}")

    # 提取 API 返回的关键错误字段
    if isinstance(error_payload, dict) and error_payload:
        interesting_keys = ["errorIds", "code", "errorCode", "message", "detail"]
        extracted = {
            k: error_payload[k]
            for k in interesting_keys
            if k in error_payload and error_payload[k] not in (None, "", [])
        }
        if extracted:
            print(f"{cyan}🔎 SheerID 错误负载 (关键字段):{reset}")
            for k, v in extracted.items():
                v_str = str(v)
                if len(v_str) > 300:
                    v_str = v_str[:300] + "..."
                print(f"  - {k}: {v_str}")

    print("\n" + "=" * 62)
    print(FRAUD_ERROR_HELP)
    print("=" * 62)
    print(f"{red}🛑 请勿重试当前 verificationId — 重新发起新验证{reset}")
