"""
proxy_checker.checker — 主代理检测器

提供同步 (check) 和异步 (check_async) 两种检测模式。
"""

import logging
import random
import threading
import time
from typing import Callable, List, Optional

from .formatter import print_result
from .geo import detect_geo, infer_country_from_hostname
from .models import ProxyCheckResult, ProxyType
from .reputation import evaluate_reputation

logger = logging.getLogger(__name__)


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
        logger.info(
            "开始代理检测: expected_country=%s, timeout=%ds",
            expected_country, timeout,
        )
        start = time.monotonic()

        try:
            # 1. 地理位置检测
            geo = detect_geo(session, timeout=timeout)
            logger.info(
                "[步骤1/3] 地理位置: ip=%s, country=%s, city=%s, org=%s",
                geo.ip, geo.country, geo.city, geo.org,
            )

            # 2. 纯净度评估
            reputation = evaluate_reputation(org=geo.org)
            logger.info(
                "[步骤2/3] 纯净度评估: type=%s, datacenter=%s, risk=%s, provider=%s",
                reputation.proxy_type.value, reputation.is_datacenter,
                reputation.risk_level.value, reputation.provider or "(无)",
            )

            # 3. 组装结果
            latency = (time.monotonic() - start) * 1000
            is_match = geo.country.upper() == expected_country.upper()

            result = ProxyCheckResult(
                geo=geo,
                reputation=reputation,
                is_country_match=is_match,
                expected_country=expected_country.upper(),
                latency_ms=round(latency, 1),
            )
            logger.info(
                "[步骤3/3] 综合结果: country_match=%s, passed=%s, latency=%.1fms",
                is_match, result.passed, result.latency_ms,
            )
            return result

        except Exception as e:
            logger.warning("代理检测失败: %s", e)
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
            logger.debug("异步检测线程启动: expected_country=%s", expected_country)
            result = self.check(
                session,
                expected_country=expected_country,
                timeout=timeout,
            )
            callback(result)
            logger.debug("异步检测线程完成: passed=%s", result.passed)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        logger.debug("异步检测守护线程已启动: thread=%s", thread.name)
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
            logger.debug("代理列表为空, 返回 None")
            return None

        target = target_country.upper()
        logger.debug("代理匹配: target=%s, 候选数=%d", target, len(proxies))

        # 1. 找国家匹配的
        matched = [
            p for p in proxies
            if infer_country_from_hostname(p) == target
        ]
        if matched:
            selected = random.choice(matched)
            logger.debug("策略1-国家匹配: 找到 %d 个, 选中=%s", len(matched), selected)
            return selected

        # 2. 优先住宅代理
        residential = [
            p for p in proxies
            if evaluate_reputation(org="", hostname=p).proxy_type == ProxyType.RESIDENTIAL
        ]
        if residential:
            selected = random.choice(residential)
            logger.debug("策略2-住宅代理: 找到 %d 个, 选中=%s", len(residential), selected)
            return selected

        # 3. 随机
        selected = random.choice(proxies)
        logger.debug("策略3-随机选择: 选中=%s", selected)
        return selected

