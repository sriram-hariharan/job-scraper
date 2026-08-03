import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from src.storage.discovery_store import load_discovery_crawl_schedule, save_discovery_crawl_schedule

CRAWL_INTERVAL = 6 * 3600  # 6 hours


class AcquisitionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    EMPTY = "EMPTY"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


ACQUISITION_FAILURE_REASONS = frozenset({
    "transport_error",
    "non_200_response",
    "malformed_payload",
    "parse_error",
    "pagination_interrupted",
})


@dataclass(frozen=True)
class AcquisitionOutcome:
    company: str
    status: AcquisitionStatus
    jobs: Tuple[Dict[str, Any], ...] = ()
    reason: str = ""
    page_count: Optional[int] = None
    raw_job_count: Optional[int] = None

    def __post_init__(self):
        if not isinstance(self.company, str) or not self.company.strip():
            raise ValueError("company must be a nonempty string")
        if not isinstance(self.status, AcquisitionStatus):
            raise ValueError("status must use AcquisitionStatus")
        if not isinstance(self.jobs, tuple) or not all(
            isinstance(job, dict) for job in self.jobs
        ):
            raise ValueError("jobs must be a tuple of dictionaries")
        if self.page_count is not None and (
            not isinstance(self.page_count, int) or self.page_count < 0
        ):
            raise ValueError("page_count must be a nonnegative integer")
        if self.raw_job_count is not None and (
            not isinstance(self.raw_job_count, int) or self.raw_job_count < 0
        ):
            raise ValueError("raw_job_count must be a nonnegative integer")

        has_jobs = bool(self.jobs)
        if self.status in {AcquisitionStatus.SUCCESS, AcquisitionStatus.PARTIAL}:
            if not has_jobs:
                raise ValueError(f"{self.status.value} requires jobs")
        elif has_jobs:
            raise ValueError(f"{self.status.value} cannot contain jobs")

        if self.status in {AcquisitionStatus.SUCCESS, AcquisitionStatus.EMPTY}:
            if self.reason:
                raise ValueError(f"{self.status.value} cannot contain a failure reason")
        elif self.reason not in ACQUISITION_FAILURE_REASONS:
            raise ValueError("failure outcome requires a sanitized reason code")

    @property
    def should_mark_scraped(self):
        return self.status in {
            AcquisitionStatus.SUCCESS,
            AcquisitionStatus.EMPTY,
        }


def load_schedule():
    return load_discovery_crawl_schedule()


def save_schedule(schedule):
    save_discovery_crawl_schedule(schedule)


def should_scrape(company, schedule):
    entry = schedule.get(company)

    if not entry:
        return True

    last_scraped = entry.get("last_scraped", 0)

    return (time.time() - last_scraped) >= CRAWL_INTERVAL


def mark_scraped(company, schedule):
    now = time.time()

    if company not in schedule:
        schedule[company] = {}

    schedule[company]["last_scraped"] = now
