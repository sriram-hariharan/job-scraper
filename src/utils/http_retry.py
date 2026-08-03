import functools
import math
import time
from collections import Counter
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import timezone
from email.utils import parsedate_to_datetime

import requests

from src.config.consts import (
    SCRAPER_HTTP_TIMEOUT_SECONDS,
    SCRAPER_RETRY_ATTEMPTS,
    SCRAPER_RETRY_DELAY_SECONDS,
    SCRAPER_RETRY_MAX_DELAY_SECONDS,
)


TRANSIENT_HTTP_STATUSES = frozenset({429, 500, 502, 503, 504})
RETRYABLE_REQUEST_EXCEPTIONS = (requests.Timeout, requests.ConnectionError)


@dataclass
class HttpRequestMetrics:
    request_count: int = 0
    retry_count: int = 0
    response_status_counts: Counter = field(default_factory=Counter)

    def snapshot(self):
        return {
            "request_count": self.request_count,
            "retry_count": self.retry_count,
            "response_status_counts": tuple(
                sorted(self.response_status_counts.items())
            ),
        }


_active_http_metrics = ContextVar("active_http_metrics", default=None)


@contextmanager
def capture_http_metrics():
    metrics = HttpRequestMetrics()
    token = _active_http_metrics.set(metrics)
    try:
        yield metrics
    finally:
        _active_http_metrics.reset(token)


def record_http_request():
    metrics = _active_http_metrics.get()
    if metrics is not None:
        metrics.request_count += 1


def record_http_response_status(status_code):
    metrics = _active_http_metrics.get()
    if metrics is None:
        return
    try:
        status = int(status_code)
    except (TypeError, ValueError):
        return
    if 100 <= status <= 599:
        metrics.response_status_counts[status] += 1


def record_http_retry():
    metrics = _active_http_metrics.get()
    if metrics is not None:
        metrics.retry_count += 1


def retry_delay_seconds(
    headers,
    *,
    fallback_delay=SCRAPER_RETRY_DELAY_SECONDS,
    max_delay=SCRAPER_RETRY_MAX_DELAY_SECONDS,
    now=None,
):
    """Return a deterministic bounded delay from a Retry-After header."""
    value = headers.get("Retry-After") if headers is not None else None
    delay = None

    if value is not None:
        text = str(value).strip()
        try:
            numeric_delay = float(text)
            if math.isfinite(numeric_delay):
                delay = max(0.0, numeric_delay)
        except (TypeError, ValueError):
            try:
                retry_at = parsedate_to_datetime(text)
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=timezone.utc)
                current_time = time.time() if now is None else float(now)
                delay = max(0.0, retry_at.timestamp() - current_time)
            except (TypeError, ValueError, OverflowError):
                delay = None

    if delay is None:
        delay = max(0.0, float(fallback_delay))

    return min(delay, max(0.0, float(max_delay)))


def retry_request(
    retries=SCRAPER_RETRY_ATTEMPTS,
    delay=SCRAPER_RETRY_DELAY_SECONDS,
    retry_status=TRANSIENT_HTTP_STATUSES,
    max_delay=SCRAPER_RETRY_MAX_DELAY_SECONDS,
    retry_exceptions=RETRYABLE_REQUEST_EXCEPTIONS,
):

    if retries < 1:
        raise ValueError("retries must be at least one")

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            last_response = None

            for attempt in range(retries):

                try:
                    record_http_request()
                    response = func(*args, **kwargs)

                    if response is None:
                        return None

                    last_response = response
                    record_http_response_status(
                        getattr(response, "status_code", None)
                    )

                    if response.status_code not in retry_status:
                        return response

                except retry_exceptions:
                    if attempt == retries - 1:
                        raise
                except Exception:
                    raise

                if attempt < retries - 1:
                    record_http_retry()
                    headers = getattr(last_response, "headers", None)
                    time.sleep(
                        retry_delay_seconds(
                            headers,
                            fallback_delay=delay,
                            max_delay=max_delay,
                        )
                    )

            return last_response

        return wrapper

    return decorator

@retry_request(retries=SCRAPER_RETRY_ATTEMPTS)
def http_get(url, **kwargs):
    kwargs.setdefault("timeout", SCRAPER_HTTP_TIMEOUT_SECONDS)
    return requests.get(url, **kwargs)


@retry_request(retries=SCRAPER_RETRY_ATTEMPTS)
def http_post(url, **kwargs):
    kwargs.setdefault("timeout", SCRAPER_HTTP_TIMEOUT_SECONDS)
    return requests.post(url, **kwargs)
