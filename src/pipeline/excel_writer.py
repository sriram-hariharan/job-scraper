import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

from src.utils.location_cleaner import normalize_location
from src.utils.time_utils import time_ago
from src.utils.logging import get_logger

logger = get_logger("excel_writer")


def format_sheet(sheet):

    sheet.freeze(rows=1)

    # Priority column numeric
    sheet.format(
        "G:G",
        {
            "numberFormat": {
                "type": "NUMBER",
                "pattern": "0.00"
            }
        }
    )

    # Resume similarity numeric
    sheet.format(
        "I:I",
        {
            "numberFormat": {
                "type": "NUMBER",
                "pattern": "0.00"
            }
        }
    )

    # Make link column wider
    sheet.format(
        "O:O",
        {
            "wrapStrategy": "CLIP"
        }
    )

    # Sort newest first, then priority
    sheet.sort(
        (5, "des"),  # Posted At
        (7, "des")   # Priority Score
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
        "Source",
        "Company",
        "Title",
        "Location",
        "Posted At",
        "Posted",
        "Priority Score",
        "AI Score",
        "Resume Match",
        "Visa",
        "Role Family",
        "Best Resume",
        "AI Evaluation",
        "Run Timestamp",
        "Link"
    ]

    existing_data = sheet.get_all_values()

    # ---------- HEADER CHECK ----------
    if not existing_data or existing_data[0] != headers:

        sheet.clear()
        sheet.append_row(headers)

        sheet.format(
            "A1:O1",
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
            if len(row) >= 15:
                existing_urls.add(row[14])

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
            resume_match = float(resume_match)
        except Exception:
            resume_match = 0.0

        intelligence = job.get("intelligence", {})

        rows_to_add.append([
            job.get("source"),
            job.get("company"),
            job.get("title"),
            location,
            raw_posted,
            relative_posted,
            priority,
            ai_score,
            resume_match,
            intelligence.get("visa_sponsorship"),
            intelligence.get("role_family"),
            job.get("best_resume"),
            job.get("ai_fit"),
            run_time,
            url
        ])

    if not rows_to_add:
        logger.info("No new jobs found")
        return

    sheet.append_rows(
        rows_to_add,
        value_input_option="RAW"
    )

    format_sheet(sheet)

    logger.info(f"{len(rows_to_add)} new jobs written to sheet")