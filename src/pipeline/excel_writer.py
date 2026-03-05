import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

def format_sheet(sheet):

    # Freeze header row
    sheet.freeze(rows=1)

    # Make the link column wider
    sheet.format(
        "D:D",
        {
            "wrapStrategy": "CLIP"
        }
    )

    # Auto sort newest entries by Date + Time
    sheet.sort((5, "des"), (6, "des"))

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
        "Job board",
        "Search Title",
        "Job Returned",
        "Link",
        "Date",
        "Time"
    ]

    existing_data = sheet.get_all_values()

    # ---------- HEADER CHECK ----------
    if not existing_data or existing_data[0] != headers:

        sheet.clear()

        sheet.append_row(headers)

        sheet.format(
            "A1:F1",
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
            if len(row) >= 4:
                existing_urls.add(row[3])

    rows_to_add = []

    now = datetime.now()

    date_str = now.strftime("%Y-%m-%d")

    time_str = now.strftime("%H:%M")  # hours + minutes

    for job in jobs:

        if job["url"] in existing_urls:
            continue

        job_board = job["url"].split("/")[2]

        job_title_searched = job["query"].split('"')[1]

        job_title_returned = job["title"]

        rows_to_add.append([
            job_board,
            job_title_searched,
            job_title_returned,
            job["url"],
            date_str,
            time_str
        ])

    if not rows_to_add:

        print("No new jobs found")
        return

    sheet.append_rows(rows_to_add)
    format_sheet(sheet)
    print(f"{len(rows_to_add)} new jobs written to sheet")

    

