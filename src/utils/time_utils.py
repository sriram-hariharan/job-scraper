from datetime import datetime, timezone
from dateutil import parser


def time_ago(iso_timestamp):

    if not iso_timestamp:
        return ""

    try:
        posted = parser.parse(iso_timestamp)

        now = datetime.now(timezone.utc)

        diff = now - posted.astimezone(timezone.utc)

        seconds = diff.total_seconds()

        hours = int(seconds // 3600)

        if hours < 1:
            minutes = int(seconds // 60)
            return f"{minutes}m ago"

        if hours < 24:
            return f"{hours}h ago"

        days = hours // 24
        return f"{days}d ago"

    except Exception:
        return ""