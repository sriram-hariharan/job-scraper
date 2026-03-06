import re
from datetime import datetime, timedelta, timezone

try:
    from dateutil import parser as dtparser
except Exception:
    dtparser = None


WORKDAY_RE = re.compile(r"posted\s+(today|yesterday|(\d+)\s+day[s]?\s+ago)", re.I)


def parse_posted_at(value):
    """
    Returns a timezone-aware datetime in UTC, or None if cannot parse.
    Accepts:
      - ISO strings (with Z or offsets)
      - Workday-style strings like "Posted Yesterday", "Posted 3 Days Ago", "Posted Today"
    """
    if not value:
        return None

    # If someone accidentally passed a display string like "5d ago", treat as unparseable
    if isinstance(value, str) and re.fullmatch(r"\d+\s*[dhm]\s*ago", value.strip().lower()):
        return None

    # datetime input
    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    if not isinstance(value, str):
        return None

    s = value.strip()

    # Workday "Posted Yesterday" etc.
    m = WORKDAY_RE.search(s)
    if m:
        now = datetime.now(timezone.utc)
        word = m.group(1).lower()
        if word == "today":
            return now
        if word == "yesterday":
            return now - timedelta(days=1)
        if m.group(2):
            days = int(m.group(2))
            return now - timedelta(days=days)

    # ISO parsing
    # Prefer dateutil if installed (handles Z, offsets, many formats)
    if dtparser:
        try:
            dt = dtparser.parse(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None

    # Fallback: basic ISO handling
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None