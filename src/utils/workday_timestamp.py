import requests
from src.utils.http_retry import record_http_request, record_http_response_status

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
})


def _result(posted_at=None, marker="", status_code=None):
    return {
        "posted_at": posted_at,
        "marker": marker,
        "status_code": status_code,
    }


def fetch_workday_timestamp_result(board_url, external_path):
    try:
        host = board_url.split(".myworkdayjobs.com")[0].replace("https://", "")
        tenant = host.split(".")[0]
        site = board_url.split(".myworkdayjobs.com/")[1].split("?")[0].strip("/")

        detail_url = (
            f"https://{host}.myworkdayjobs.com"
            f"/wday/cxs/{tenant}/{site}{external_path}"
        )
    except Exception:
        return _result(marker="workday_timestamp_request_failed")

    try:
        record_http_request()
        r = session.get(detail_url, timeout=10)
        record_http_response_status(r.status_code)
    except Exception:
        return _result(marker="workday_timestamp_request_failed")

    if r.status_code != 200:
        return _result(
            marker="workday_timestamp_non_200",
            status_code=r.status_code,
        )

    try:
        data = r.json()
    except Exception:
        return _result(
            marker="workday_timestamp_malformed_payload",
            status_code=r.status_code,
        )
    if not isinstance(data, dict):
        return _result(
            marker="workday_timestamp_malformed_payload",
            status_code=r.status_code,
        )

    info = data.get("jobPostingInfo")
    if info is None:
        info = {}
    if not isinstance(info, dict):
        return _result(
            marker="workday_timestamp_malformed_payload",
            status_code=r.status_code,
        )

    posted_at = info.get("startDate") or info.get("postedOn")
    if posted_at:
        return _result(
            posted_at=posted_at,
            marker="workday_timestamp_success",
            status_code=r.status_code,
        )

    return _result(
        marker="workday_timestamp_missing",
        status_code=r.status_code,
    )


def fetch_workday_timestamp(board_url, external_path):
    return fetch_workday_timestamp_result(board_url, external_path).get("posted_at")
