from __future__ import annotations

from typing import Any, Optional


def score_to_points(value: Any) -> Optional[int]:
    if value is None:
        return None

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    points = numeric * 100 if 0 <= numeric <= 1 else numeric
    return max(0, min(100, int(round(points))))


def score_delta_to_points(value: Any) -> Optional[int]:
    if value is None:
        return None

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    return int(round(numeric * 100 if -1 <= numeric <= 1 else numeric))


def score_delta_value(value: Any) -> Optional[float]:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_score_positive(value: Any) -> bool:
    delta = score_delta_value(value)
    return delta is not None and delta > 0


def is_score_neutral(value: Any) -> bool:
    delta = score_delta_value(value)
    return delta is not None and delta == 0


def is_score_negative(value: Any) -> bool:
    delta = score_delta_value(value)
    return delta is not None and delta < 0
