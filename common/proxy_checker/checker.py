"""
proxy_checker.checker — 主代理检测器

提供同步 (check) 和异步 (check_async) 两种检测模式。
"""

import random
import threading
import time
from typing import Callable, List, Optional

from .formatter import print_result
from .geo import detect_geo, infer_country_from_hostname
from .models import ProxyCheckResult, ProxyType
from .reputation import evaluate_reputation


class ProxyChecker:
    """
    代理 IP 检测器，支持主线程同步和子线程异步两种模式。

    用法:
        checker = ProxyChecker()

        # 同步检测 (阻塞当前线程)
        result = checker.check(session, expected_country="US")

        # 异步检测 (不阻塞主线程)
        thread = checker.check_async(session, expected_country="US")
    """

    def check(
        self,
        session,
        *,
        expected_country: str = "US",
        timeout: int = 8,
    ) -> ProxyCheckResult:
        """
        同步检测代理 IP — 阻塞当前线程直到完成。

        流程: 地理位置检测 → 纯净度评估 → 综合结果

        Args:
            session:          已配置代理的 HTTP 会话
            expected_country: 预期国家代码 (默认 "US")
            timeout:          单次 API 请求超时秒数

        Returns:
            ProxyCheckResult 完整检测结果
        """
        start = time.monotonic()

        try:
            # 1. 地理位置检测
            geo = detect_geo(session, timeout=timeout)

            # 2. 纯净度评估
            reputation = evaluate_reputation(org=geo.org)

            # 3. 组装结果
            latency = (time.monotonic() - start) * 1000
            is_match = geo.country.upper() == expected_country.upper()

            return ProxyCheckResult(
                geo=geo,
                reputation=reputation,
                is_country_match=is_match,
                expected_country=expected_country.upper(),
                latency_ms=round(latency, 1),
            )

        except Exception as e:
            return ProxyCheckResult(
                expected_country=expected_country.upper(),
                error=str(e),
            )

    def check_async(
        self,
        session,
        *,
        expected_country: str = "US",
        timeout: int = 8,
        callback: Optional[Callable[[ProxyCheckResult], None]] = None,
    ) -> threading.Thread:
        """
        异步检测代理 IP — 启动守护线程，不阻塞主线程。

        Args:
            session:          已配置代理的 HTTP 会话
            expected_country: 预期国家代码
            timeout:          单次 API 请求超时秒数
            callback:         检测完成后的回调函数，
                              默认使用 print_result 输出到终端

        Returns:
            threading.Thread 守护线程对象 (已启动)
        """
        if callback is None:
            callback = print_result

        def _worker():
            result = self.check(
                session,
                expected_country=expected_country,
                timeout=timeout,
            )
            callback(result)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread

    @staticmethod
    def get_matched_proxy(
        target_country: str,
        proxies: List[str],
    ) -> Optional[str]:
        """
        从代理列表中选取最佳匹配目标国家的代理。

        优先级: 国家匹配 > 住宅代理 > 随机

        Args:
            target_country: 目标国家代码 (US, NL, UK 等)
            proxies:        代理 URL 列表

        Returns:
            选中的代理 URL，列表为空则返回 None
        """
        if not proxies:
            return None

        target = target_country.upper()

        # 1. 找国家匹配的
        matched = [
            p for p in proxies
            if infer_country_from_hostname(p) == target
        ]
        if matched:
            return random.choice(matched)

        # 2. 优先住宅代理
        residential = [
            p for p in proxies
            if evaluate_reputation(org="", hostname=p).proxy_type == ProxyType.RESIDENTIAL
        ]
        if residential:
            return random.choice(residential)

        # 3. 随机
        return random.choice(proxies)
