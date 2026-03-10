import requests

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
})

def fetch_workday_timestamp(board_url, external_path):

    try:

        host = board_url.split(".myworkdayjobs.com")[0].replace("https://", "")
        tenant = host.split(".")[0]
        site = board_url.split(".myworkdayjobs.com/")[1].split("?")[0].strip("/")

        detail_url = (
            f"https://{host}.myworkdayjobs.com"
            f"/wday/cxs/{tenant}/{site}{external_path}"
        )

        r = session.get(detail_url, timeout=10)

        if r.status_code != 200:
            return None

        data = r.json()

        info = data.get("jobPostingInfo", {})

        return info.get("startDate")

    except Exception:
        return None