import time
from datetime import datetime

import gspread
from gspread.exceptions import APIError
from google.oauth2.service_account import Credentials

from src.utils.location_cleaner import normalize_location
from src.utils.time_utils import time_ago
from src.utils.logging import get_logger

logger = get_logger("excel_writer")

def _is_retryable_sheet_error(exc: Exception) -> bool:
    if not isinstance(exc, APIError):
        return False

    status_code = None
    response = getattr(exc, "response", None)
    if response is not None:
        status_code = getattr(response, "status_code", None)

    text = str(exc).lower()

    if status_code in {429, 500, 502, 503, 504}:
        return True

    if status_code == 403 and (
        "rate limit" in text
        or "user rate limit exceeded" in text
        or "quota" in text
    ):
        return True

    return False


def _call_sheet_api(operation_name: str, fn, *args, **kwargs):
    max_attempts = 5
    base_sleep_seconds = 2.0

    for attempt in range(1, max_attempts + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            if not _is_retryable_sheet_error(exc) or attempt == max_attempts:
                raise

            sleep_seconds = base_sleep_seconds * (2 ** (attempt - 1))
            logger.warning(
                "Google Sheets %s failed with retryable error on attempt %s/%s. Sleeping %.1fs. Error=%s",
                operation_name,
                attempt,
                max_attempts,
                sleep_seconds,
                exc,
            )
            time.sleep(sleep_seconds)

def _column_letter(index: int) -> str:
    result = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _header_index(headers, name: str) -> int:
    return headers.index(name) + 1


def _header_letter(headers, name: str) -> str:
    return _column_letter(_header_index(headers, name))

def _scale_score_100(value):
    raw = str(value).strip() if value is not None else ""
    if raw == "":
        return ""

    try:
        return round(float(raw) * 100.0, 2)
    except Exception:
        return value


def format_sheet(sheet, headers):
    _call_sheet_api("freeze", sheet.freeze, rows=1)

    numeric_formats = {
        "Planning Winner Score": "0.00",
        "Planning Runner Up Score": "0.00",
        "Planning Score Gap": "0.00",
        "LLM Fallback Best Score": "0.00",
        "LLM Fallback Backup Score": "0.00",
        "Queue Rank": "0",
        "Missing Requirement Count": "0",
        "Resume Match": "0.00",
        "Priority Score": "0.00",
        "AI Signal Score": "0.00",
    }

    for header, pattern in numeric_formats.items():
        col = _header_letter(headers, header)
        _call_sheet_api(
            f"format numeric column {header}",
            sheet.format,
            f"{col}:{col}",
            {
                "numberFormat": {
                    "type": "NUMBER",
                    "pattern": pattern
                }
            },
        )

    wrap_columns = [
        "Title",
        "Queue Priority Reason",
        "LLM Fallback Reason",
    ]

    clip_columns = [
        "Link",
        "LLM Job Triage",
        "Packet JSON",
        "Tailoring Markdown",
        "Tailoring LLM JSON",
    ]

    for header in wrap_columns:
        col = _header_letter(headers, header)
        _call_sheet_api(
            f"format wrap column {header}",
            sheet.format,
            f"{col}:{col}",
            {
                "wrapStrategy": "WRAP"
            },
        )

    for header in clip_columns:
        col = _header_letter(headers, header)
        _call_sheet_api(
            f"format clip column {header}",
            sheet.format,
            f"{col}:{col}",
            {
                "wrapStrategy": "CLIP"
            },
        )

    planning_score_col = _header_index(headers, "Planning Winner Score")
    posted_at_col = _header_index(headers, "Posted At")

    _call_sheet_api(
        "sort sheet",
        sheet.sort,
        (planning_score_col, "des"),
        (posted_at_col, "des"),
    )


def write_jobs_to_sheet(jobs):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_file(
        "job-scraper-489208-d8667c88c023.json",
        scopes=scope
    )

    client = gspread.authorize(creds)

    sheet = _call_sheet_api(
        "open spreadsheet",
        lambda: client.open("AI Job Scraper").sheet1,
    )

    headers = [
        "Company",
        "Title",
        "Link",
        "Posted At",
        "Posted",
        "Location",
        "Planning Winner Resume",
        "Planning Winner Score",
        "Planning Runner Up Resume",
        "Planning Runner Up Score",
        "Planning Score Gap",
        "Planning Action",
        "Queue Rank",
        "Needs Variant Review",
        "Missing Requirement Count",
        "Planning Is Tie",
        "Queue Priority Reason",
        "LLM Fallback Best Resume",
        "LLM Fallback Best Score",
        "LLM Fallback Backup Resume",
        "LLM Fallback Backup Score",
        "LLM Fallback Confidence",
        "LLM Fallback Status",
        "LLM Fallback Cache Hit",
        "LLM Fallback Reason",
        "Embedding Best Resume",
        "Resume Match",
        "Priority Score",
        "AI Signal Score",
        "LLM Job Triage",
        "Visa",
        "Role Family",
        "Source",
        "LLM Tailoring Status",
        "LLM Error Type",
        "Packet JSON",
        "Tailoring Markdown",
        "Tailoring LLM JSON",
        "Run Timestamp",
    ]

    existing_data = _call_sheet_api("get existing sheet values", sheet.get_all_values)
    link_index = headers.index("Link")
    last_col_letter = _column_letter(len(headers))

    if not existing_data or existing_data[0] != headers:
        _call_sheet_api("clear sheet", sheet.clear)
        _call_sheet_api("append header row", sheet.append_row, headers)

        _call_sheet_api(
            "format header row",
            sheet.format,
            f"A1:{_column_letter(len(headers))}1",
            {
                "backgroundColor": {
                    "red": 0.15,
                    "green": 0.55,
                    "blue": 0.85
                },
                "textFormat": {
                    "bold": True
                }
            },
        )

        existing_data = [headers]

    existing_url_to_row = {}

    for row_number, row in enumerate(existing_data[1:], start=2):
        if len(row) > link_index:
            existing_url = row[link_index].strip()
            if existing_url and existing_url not in existing_url_to_row:
                existing_url_to_row[existing_url] = row_number

    rows_to_add = []
    row_updates = []
    run_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    for job in jobs:
        url = job.get("url") or job.get("job_doc_id") or job.get("link")

        if not url:
            continue

        location = normalize_location(job.get("location"))
        raw_posted = job.get("posted_at")
        relative_posted = time_ago(raw_posted)

        priority = job.get("priority_score", 0)
        ai_score = job.get("ai_signal_score", 0)
        resume_match = job.get("resume_match_score", 0)

        try:
            priority = float(priority)
        except Exception:
            priority = 0.0

        try:
            ai_score = float(ai_score)
        except Exception:
            ai_score = 0.0

        try:
            resume_match = float(resume_match)
        except Exception:
            resume_match = 0.0

        intelligence = job.get("intelligence", {})
        planning = job.get("application_planning", {}) or {}

        row_values = [
            job.get("company"),
            job.get("title"),
            url,
            raw_posted,
            relative_posted,
            location,
            planning.get("winner_resume", ""),
            _scale_score_100(planning.get("winner_score", "")),
            planning.get("runner_up_resume", ""),
            _scale_score_100(planning.get("runner_up_score", "")),
            _scale_score_100(planning.get("score_gap", "")),
            planning.get("action", ""),
            planning.get("queue_rank", ""),
            planning.get("needs_variant_review", ""),
            planning.get("missing_requirement_count", ""),
            planning.get("is_tie", ""),
            planning.get("queue_priority_reason", ""),
            planning.get("llm_fallback_best_resume", ""),
            _scale_score_100(planning.get("llm_fallback_best_score", "")),
            planning.get("llm_fallback_backup_resume", ""),
            _scale_score_100(planning.get("llm_fallback_backup_score", "")),
            planning.get("llm_fallback_confidence", ""),
            planning.get("llm_fallback_status", ""),
            planning.get("llm_fallback_cache_hit", ""),
            planning.get("llm_fallback_reason", ""),
            job.get("best_resume"),
            _scale_score_100(resume_match),
            priority,
            ai_score,
            job.get("ai_fit"),
            intelligence.get("visa_sponsorship"),
            intelligence.get("role_family"),
            job.get("source"),
            planning.get("llm_tailoring_status", ""),
            planning.get("llm_error_type", ""),
            planning.get("packet_json", ""),
            planning.get("tailoring_md", ""),
            planning.get("tailoring_llm_json", ""),
            run_time,
        ]

        if url in existing_url_to_row:
            row_number = existing_url_to_row[url]
            row_updates.append(
                {
                    "range": f"A{row_number}:{last_col_letter}{row_number}",
                    "values": [row_values],
                }
            )
        else:
            rows_to_add.append(row_values)

    if not row_updates and not rows_to_add:
        logger.info("No sheet changes needed")
        return

    if row_updates:
        _call_sheet_api("batch update rows", sheet.batch_update, row_updates)

    if rows_to_add:
        _call_sheet_api(
            "append new rows",
            sheet.append_rows,
            rows_to_add,
            value_input_option="RAW"
        )

    format_sheet(sheet, headers)

    logger.info(
        "Sheet sync complete: %s updated, %s appended",
        len(row_updates),
        len(rows_to_add),
    )