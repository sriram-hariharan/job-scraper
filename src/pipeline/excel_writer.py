import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

from src.utils.location_cleaner import normalize_location
from src.utils.time_utils import time_ago
from src.utils.logging import get_logger

logger = get_logger("excel_writer")


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


def format_sheet(sheet, headers):
    sheet.freeze(rows=1)

    numeric_formats = {
        "Planning Winner Score": "0.000",
        "Priority Score": "0.00",
        "Resume Match": "0.00",
        "AI Score": "0.00",
        "Planning Runner Up Score": "0.000",
        "Planning Score Gap": "0.000",
        "Queue Rank": "0",
        "Missing Requirement Count": "0",
    }

    for header, pattern in numeric_formats.items():
        col = _header_letter(headers, header)
        sheet.format(
            f"{col}:{col}",
            {
                "numberFormat": {
                    "type": "NUMBER",
                    "pattern": pattern
                }
            }
        )

    wrap_columns = [
        "Title",
        "Queue Priority Reason",
    ]

    clip_columns = [
        "Link",
        "AI Evaluation",
        "Packet JSON",
        "Tailoring Markdown",
        "Tailoring LLM JSON",
    ]

    for header in wrap_columns:
        col = _header_letter(headers, header)
        sheet.format(
            f"{col}:{col}",
            {
                "wrapStrategy": "WRAP"
            }
        )

    for header in clip_columns:
        col = _header_letter(headers, header)
        sheet.format(
            f"{col}:{col}",
            {
                "wrapStrategy": "CLIP"
            }
        )

    posted_at_col = _header_index(headers, "Posted At")
    priority_col = _header_index(headers, "Priority Score")

    sheet.sort(
        (posted_at_col, "des"),
        (priority_col, "des")
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

    sheet = client.open("AI Job Scraper").sheet1

    headers = [
        "Company",
        "Title",
        "Link",
        "Location",
        "Posted At",
        "Posted",
        "Best Resume",
        "Planning Winner Resume",
        "Planning Runner Up Resume",
        "Planning Winner Score",
        "Priority Score",
        "Resume Match",
        "AI Score",
        "Planning Runner Up Score",
        "Planning Score Gap",
        "Source",
        "Planning Action",
        "Planning Is Tie",
        "Needs Variant Review",
        "Queue Rank",
        "Missing Requirement Count",
        "Queue Priority Reason",
        "Visa",
        "Role Family",
        "LLM Tailoring Status",
        "LLM Error Type",
        "AI Evaluation",
        "Packet JSON",
        "Tailoring Markdown",
        "Tailoring LLM JSON",
        "Run Timestamp",
    ]

    existing_data = sheet.get_all_values()
    link_index = headers.index("Link")

    if not existing_data or existing_data[0] != headers:
        sheet.clear()
        sheet.append_row(headers)

        sheet.format(
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
            }
        )

        existing_urls = set()
    else:
        existing_urls = set()

        for row in existing_data[1:]:
            if len(row) > link_index:
                existing_urls.add(row[link_index])

    rows_to_add = []
    run_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    for job in jobs:
        url = job.get("url")

        if not url:
            continue

        if url in existing_urls:
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

        rows_to_add.append([
            job.get("company"),
            job.get("title"),
            url,
            location,
            raw_posted,
            relative_posted,
            job.get("best_resume"),
            planning.get("winner_resume", ""),
            planning.get("runner_up_resume", ""),
            planning.get("winner_score", ""),
            priority,
            resume_match,
            ai_score,
            planning.get("runner_up_score", ""),
            planning.get("score_gap", ""),
            job.get("source"),
            planning.get("action", ""),
            planning.get("is_tie", ""),
            planning.get("needs_variant_review", ""),
            planning.get("queue_rank", ""),
            planning.get("missing_requirement_count", ""),
            planning.get("queue_priority_reason", ""),
            intelligence.get("visa_sponsorship"),
            intelligence.get("role_family"),
            planning.get("llm_tailoring_status", ""),
            planning.get("llm_error_type", ""),
            job.get("ai_fit"),
            planning.get("packet_json", ""),
            planning.get("tailoring_md", ""),
            planning.get("tailoring_llm_json", ""),
            run_time,
        ])

    if not rows_to_add:
        logger.info("No new jobs found")
        return

    sheet.append_rows(
        rows_to_add,
        value_input_option="RAW"
    )

    format_sheet(sheet, headers)

    logger.info(f"{len(rows_to_add)} new jobs written to sheet")