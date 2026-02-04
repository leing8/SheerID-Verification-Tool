"""
欺诈处理模块 - 欺诈检测处理和重试

包含:
- should_retry_fraud: 判断是否应该重试
- handle_fraud_rejection: 处理欺诈拒绝
"""

from .constants import FRAUD_ERROR_HELP


def should_retry_fraud(retry_count: int):
    """
    判断是否应该重试欺诈拒绝
    
    指数退避：30s, 60s, 120s（最多 3 次）
    
    Returns:
        (should_retry, delay_seconds)
    """
    if retry_count < 0:
        retry_count = 0
    
    backoff_schedule = [30, 60, 120]
    
    if retry_count >= len(backoff_schedule):
        return False, 0
    
    return True, backoff_schedule[retry_count]


def handle_fraud_rejection(*, retry_count: int = 0, error_payload=None, message: str = None):
    """
    处理欺诈拒绝 - 输出帮助信息并返回重试建议
    
    Returns:
        (should_retry, delay_seconds)
    """
    print("\n" + "+" + "-" * 60 + "+")
    print("|" + " !!! 欺诈检测触发 !!! ".center(60) + "|")
    print("|" + " SheerID 返回 fraudRulesReject ".center(60) + "|")
    print("+" + "-" * 60 + "+")
    print("❌ 验证被 SheerID 欺诈规则阻止")
    
    if message:
        print(f"📋 上下文: {message}")
    
    if isinstance(error_payload, dict) and error_payload:
        interesting_keys = ["code", "errorCode", "message", "detail"]
        for k in interesting_keys:
            if k in error_payload and error_payload.get(k):
                v = str(error_payload.get(k))[:200]
                print(f"  - {k}: {v}")
    
    print("\n" + "=" * 62)
    print(FRAUD_ERROR_HELP)
    print("=" * 62)
    
    should_retry, delay = should_retry_fraud(retry_count)
    if should_retry:
        print(f"⏳ 建议重试: 第 {retry_count + 1}/3 次，等待 {delay}s")
    else:
        print("🛑 已达最大重试次数。请等待 24-48 小时后更换 IP 重试。")
    
    return should_retry, delay
