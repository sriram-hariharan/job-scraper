from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Iterable, Optional, Tuple
from urllib.parse import urlsplit

from src.config.consts import (
    SOURCE_HEALTH_DESCRIPTION_MISSING_DEGRADED_RATIO,
    SOURCE_HEALTH_RETRY_DEGRADED_COUNT,
    SOURCE_HEALTH_TIMESTAMP_MISSING_DEGRADED_RATIO,
    SOURCE_HEALTH_URL_MISSING_UNHEALTHY_RATIO,
)
from src.discovery.crawl_scheduler import AcquisitionOutcome, AcquisitionStatus
from src.utils.http_retry import capture_http_metrics
from src.utils.logging import get_logger

logger = get_logger("metrics")

HEALTHY = "healthy"
DEGRADED = "degraded"
UNHEALTHY = "unhealthy"
UNKNOWN = "unknown"
_HEALTH_ORDER = {UNKNOWN: 0, HEALTHY: 1, DEGRADED: 2, UNHEALTHY: 3}


def _bounded_text(value: Any, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit]


def _safe_identity(value: Any, limit: int = 256) -> str:
    text = _bounded_text(value, limit * 2)
    if "://" in text:
        parsed = urlsplit(text)
        text = f"{parsed.hostname or ''}{parsed.path or ''}"
    return _bounded_text(text, limit)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _field_present(job: dict, names: Iterable[str]) -> bool:
    return any(str(job.get(name) or "").strip() for name in names)


def _completeness_counts(jobs: Iterable[dict]):
    rows = list(jobs or [])
    url_present = sum(
        1 for job in rows if _field_present(job, ("url", "job_url"))
    )
    timestamp_present = sum(
        1 for job in rows if _field_present(job, ("posted_at", "timestamp"))
    )
    description_present = sum(
        1
        for job in rows
        if _field_present(
            job,
            ("description", "description_text", "summary", "short_description"),
        )
    )
    total = len(rows)
    return {
        "canonical_url_present_count": url_present,
        "canonical_url_missing_count": total - url_present,
        "timestamp_present_count": timestamp_present,
        "timestamp_missing_count": total - timestamp_present,
        "description_present_count": description_present,
        "description_missing_count": total - description_present,
    }


def classify_source_health(
    acquisition_status: str,
    *,
    normalized_job_count: int = 0,
    retry_count: int = 0,
    canonical_url_missing_count: int = 0,
    timestamp_missing_count: int = 0,
    description_missing_count: int = 0,
) -> str:
    status = str(acquisition_status or "").upper()
    if not status:
        return UNKNOWN
    if status == AcquisitionStatus.FAILED.value:
        return UNHEALTHY
    if status == AcquisitionStatus.PARTIAL.value:
        return DEGRADED
    if status == AcquisitionStatus.EMPTY.value:
        return HEALTHY
    if status != AcquisitionStatus.SUCCESS.value:
        return UNKNOWN

    total = max(0, int(normalized_job_count or 0))
    if total:
        if canonical_url_missing_count / total > SOURCE_HEALTH_URL_MISSING_UNHEALTHY_RATIO:
            return UNHEALTHY
        if (
            timestamp_missing_count / total
            > SOURCE_HEALTH_TIMESTAMP_MISSING_DEGRADED_RATIO
            or description_missing_count / total
            > SOURCE_HEALTH_DESCRIPTION_MISSING_DEGRADED_RATIO
        ):
            return DEGRADED
    if int(retry_count or 0) >= SOURCE_HEALTH_RETRY_DEGRADED_COUNT:
        return DEGRADED
    return HEALTHY


@dataclass(frozen=True)
class SourceHealthMetrics:
    source: str
    company: str
    acquisition_status: str = ""
    reason_code: str = ""
    request_count: int = 0
    response_status_counts: Tuple[Tuple[int, int], ...] = ()
    retry_count: int = 0
    page_count: Optional[int] = None
    partial_result_count: int = 0
    raw_job_count: Optional[int] = None
    normalized_job_count: int = 0
    filter_drop_count: int = 0
    duplicate_drop_count: int = 0
    final_retained_job_count: int = 0
    canonical_url_present_count: int = 0
    canonical_url_missing_count: int = 0
    timestamp_present_count: int = 0
    timestamp_missing_count: int = 0
    description_present_count: int = 0
    description_missing_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    schedule_advanced: bool = False
    health: str = UNKNOWN


_metrics_lock = Lock()
_acquisition_metrics = []


def reset_acquisition_metrics() -> None:
    with _metrics_lock:
        _acquisition_metrics.clear()


def acquisition_metrics_snapshot():
    with _metrics_lock:
        return tuple(
            sorted(
                _acquisition_metrics,
                key=lambda item: (item.source, item.company),
            )
        )


def _metric_from_outcome(
    source: str,
    outcome: AcquisitionOutcome,
    transport: dict,
    *,
    started_at: datetime,
    completed_at: datetime,
    duration_ms: int,
    schedule_advanced: bool,
) -> SourceHealthMetrics:
    completeness = _completeness_counts(outcome.jobs)
    status = outcome.status.value
    normalized_count = len(outcome.jobs)
    retry_count = int(transport.get("retry_count", 0) or 0)
    health = classify_source_health(
        status,
        normalized_job_count=normalized_count,
        retry_count=retry_count,
        canonical_url_missing_count=completeness["canonical_url_missing_count"],
        timestamp_missing_count=completeness["timestamp_missing_count"],
        description_missing_count=completeness["description_missing_count"],
    )
    return SourceHealthMetrics(
        source=_safe_identity(source, 64),
        company=_safe_identity(outcome.company),
        acquisition_status=status,
        reason_code=_bounded_text(outcome.reason, 64),
        request_count=int(transport.get("request_count", 0) or 0),
        response_status_counts=tuple(
            (int(code), int(count))
            for code, count in transport.get("response_status_counts", ())
        ),
        retry_count=retry_count,
        page_count=outcome.page_count,
        partial_result_count=int(outcome.status is AcquisitionStatus.PARTIAL),
        raw_job_count=outcome.raw_job_count,
        normalized_job_count=normalized_count,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=max(0, min(int(duration_ms), 86_400_000)),
        schedule_advanced=bool(schedule_advanced),
        health=health,
        **completeness,
    )


def _store_metric(metric: SourceHealthMetrics) -> None:
    with _metrics_lock:
        _acquisition_metrics.append(metric)
    logger.info(
        "source_health_event event=completed source=%s company=%s status=%s health=%s",
        metric.source,
        metric.company,
        metric.acquisition_status,
        metric.health,
    )


def observe_acquisition(
    source: str,
    acquire: Callable[[], AcquisitionOutcome],
    *,
    schedule_on_success: bool,
    company: str = "",
) -> AcquisitionOutcome:
    started_at = _utc_now()
    started_clock = time.monotonic()
    logger.info("source_health_event event=started source=%s", _safe_identity(source, 64))
    with capture_http_metrics() as transport:
        try:
            outcome = acquire()
        except Exception:
            completed_at = _utc_now()
            snapshot = transport.snapshot()
            reason = (
                "transport_error"
                if snapshot["request_count"] and not snapshot["response_status_counts"]
                else "parse_error"
            )
            failed = AcquisitionOutcome(
                company or f"<{_safe_identity(source, 64)}>",
                AcquisitionStatus.FAILED,
                reason=reason,
            )
            _store_metric(
                _metric_from_outcome(
                    source,
                    failed,
                    snapshot,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=round((time.monotonic() - started_clock) * 1000),
                    schedule_advanced=False,
                )
            )
            raise
    completed_at = _utc_now()
    metric = _metric_from_outcome(
        source,
        outcome,
        transport.snapshot(),
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=round((time.monotonic() - started_clock) * 1000),
        schedule_advanced=schedule_on_success and outcome.should_mark_scraped,
    )
    _store_metric(metric)
    return outcome


async def observe_acquisition_async(
    source: str,
    acquire: Callable[[], Any],
    *,
    schedule_on_success: bool,
    company: str = "",
) -> AcquisitionOutcome:
    started_at = _utc_now()
    started_clock = time.monotonic()
    logger.info("source_health_event event=started source=%s", _safe_identity(source, 64))
    with capture_http_metrics() as transport:
        try:
            outcome = await acquire()
        except Exception:
            completed_at = _utc_now()
            snapshot = transport.snapshot()
            reason = (
                "transport_error"
                if snapshot["request_count"] and not snapshot["response_status_counts"]
                else "parse_error"
            )
            failed = AcquisitionOutcome(
                company or f"<{_safe_identity(source, 64)}>",
                AcquisitionStatus.FAILED,
                reason=reason,
            )
            _store_metric(
                _metric_from_outcome(
                    source,
                    failed,
                    snapshot,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=round((time.monotonic() - started_clock) * 1000),
                    schedule_advanced=False,
                )
            )
            raise
    completed_at = _utc_now()
    metric = _metric_from_outcome(
        source,
        outcome,
        transport.snapshot(),
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=round((time.monotonic() - started_clock) * 1000),
        schedule_advanced=schedule_on_success and outcome.should_mark_scraped,
    )
    _store_metric(metric)
    return outcome


def _counts_by_source(jobs: Iterable[dict]) -> Counter:
    return Counter(
        _safe_identity(job.get("source") or "unknown", 64)
        for job in jobs or []
    )


def combine_source_stage_metrics(
    acquisition_metrics: Iterable[SourceHealthMetrics],
    *,
    filtered_jobs: Iterable[dict],
    deduped_jobs: Iterable[dict],
    final_jobs: Iterable[dict],
):
    acquisitions = tuple(acquisition_metrics or ())
    filtered = _counts_by_source(filtered_jobs)
    deduped = _counts_by_source(deduped_jobs)
    final = _counts_by_source(final_jobs)
    normalized = Counter()
    health_by_source = {}
    for metric in acquisitions:
        normalized[metric.source] += metric.normalized_job_count
        current = health_by_source.get(metric.source, UNKNOWN)
        if _HEALTH_ORDER[metric.health] > _HEALTH_ORDER[current]:
            health_by_source[metric.source] = metric.health

    summaries = []
    sources = sorted(set(normalized) | set(filtered) | set(deduped) | set(final))
    for source in sources:
        normalized_count = normalized[source]
        filtered_count = filtered[source]
        deduped_count = deduped[source]
        summaries.append(
            SourceHealthMetrics(
                source=source,
                company="",
                normalized_job_count=normalized_count,
                filter_drop_count=max(0, normalized_count - filtered_count),
                duplicate_drop_count=max(0, filtered_count - deduped_count),
                final_retained_job_count=final[source],
                health=health_by_source.get(source, UNKNOWN),
            )
        )
    return tuple(
        sorted(acquisitions + tuple(summaries), key=lambda item: (item.source, item.company))
    )


def log_stage_metrics(stage_name, jobs):
    counts = Counter(job.get("source", "unknown") for job in jobs)
    logger.info("")
    logger.info(f"PIPELINE METRICS — {stage_name}")
    for source, count in sorted(counts.items()):
        logger.info(f"{source:15} {count}")
    logger.info(f"TOTAL: {len(jobs)}")
    logger.info("")
    return counts
