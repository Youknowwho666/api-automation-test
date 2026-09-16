"""基础 API 层：所有业务 API 的父类。

相比初版的三点升级：
1. requests.Session 复用连接，比每次新建连接快，且自动带 Cookie；
2. 统一日志：每个请求的 URL、状态码、耗时都落盘，排查问题不用复现；
3. 网络抖动自动重试（只重试网络层错误，绝不重试业务层的 4xx/5xx）。
"""
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from common.config import config
from common.logger import logger


class BaseApi:
    """通用 HTTP 客户端封装。"""

    def __init__(self, base_url=None, timeout=None, retry_times=None):
        self.base_url = (base_url or config.base_url).rstrip("/")
        self.timeout = timeout or config.timeout
        self.retry_times = config.retry_times if retry_times is None else retry_times
        self.session = self._build_session()

    def _build_session(self):
        """构建带自动重试的 Session。

        只对「连接失败 / 读超时」等网络层错误重试，业务层的 4xx/5xx 不重试
        —— 因为那是被测系统真实的返回，重试会掩盖缺陷。
        公开测试站点（如 JSONPlaceholder）网络波动大，这一层重试能显著降低假失败。
        """
        session = requests.Session()
        retry = Retry(
            total=self.retry_times,
            connect=self.retry_times,
            read=self.retry_times,
            status=0,  # 关键：不对任何状态码重试，保证 4xx/5xx 断言能拿到真实响应
            backoff_factor=config.retry_delay,
            raise_on_status=False,  # 5xx 直接返回给用例判断，而不是抛 ResponseError
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"],
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "api-automation-test/2.0",
        })
        return session

    def set_token(self, token):
        """统一设置鉴权头，避免在每个用例里硬编码 Token。"""
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        logger.info("已设置鉴权 Token")

    def clear_token(self):
        """清除鉴权头。"""
        self.session.headers.pop("Authorization", None)

    def send_request(self, method, url, **kwargs):
        """通用请求发送方法，带日志与耗时统计。

        额外做一层「应用级重试」：捕获连接异常与读超时后按退避重试，
        保证公开测试站点的偶发超时不会变成用例失败。
        """
        full_url = url if url.startswith("http") else self.base_url + url
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("verify", config.get("verify_ssl"))

        logger.info("→ %s %s | 入参: %s", method.upper(), full_url, _brief(kwargs))

        last_error = None
        for attempt in range(self.retry_times + 1):
            start = time.time()
            try:
                response = self.session.request(method=method, url=full_url, **kwargs)
                cost = time.time() - start
                logger.info(
                    "← %s %s | 状态码: %s | 耗时: %.3fs",
                    method.upper(), full_url, response.status_code, cost,
                )
                # 把耗时挂到 response 上，供 assert_response_time 使用
                response.elapsed_seconds = cost
                return response
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as e:
                last_error = e
                if attempt < self.retry_times:
                    wait = config.retry_delay * (attempt + 1)
                    logger.warning(
                        "网络异常，第 %s 次重试（%.1fs 后）: %s", attempt + 1, wait, e
                    )
                    time.sleep(wait)
                else:
                    logger.error("✗ %s %s 请求异常（已重试 %s 次）: %s",
                                 method.upper(), full_url, self.retry_times, e)
                    raise

    # ---------- 便捷方法 ----------
    def get(self, url, params=None, **kwargs):
        return self.send_request("GET", url, params=params, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return self.send_request("POST", url, data=data, json=json, **kwargs)

    def put(self, url, data=None, json=None, **kwargs):
        return self.send_request("PUT", url, data=data, json=json, **kwargs)

    def patch(self, url, data=None, json=None, **kwargs):
        return self.send_request("PATCH", url, data=data, json=json, **kwargs)

    def delete(self, url, **kwargs):
        return self.send_request("DELETE", url, **kwargs)


def _brief(kwargs):
    """截断过长的请求参数，避免日志刷屏。"""
    parts = []
    for key in ("params", "json", "data"):
        if kwargs.get(key):
            parts.append(f"{key}={str(kwargs[key])[:120]}")
    return "; ".join(parts) or "-"
