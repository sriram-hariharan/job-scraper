from __future__ import annotations

from typing import Any, Dict, Iterable, List


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def safe_rate(numerator: int, denominator: int) -> float:
    if int(denominator or 0) <= 0:
        return 1.0
    return round(float(numerator or 0) / float(denominator), 6)


def accuracy(expected_actual: Iterable[tuple[Any, Any]]) -> Dict[str, Any]:
    pairs = list(expected_actual)
    failed: List[Dict[str, str]] = []
    for expected, actual in pairs:
        if _clean_text(expected) != _clean_text(actual):
            failed.append({"expected": _clean_text(expected), "actual": _clean_text(actual)})

    return {
        "total": len(pairs),
        "correct": len(pairs) - len(failed),
        "accuracy": safe_rate(len(pairs) - len(failed), len(pairs)),
        "failed": failed,
    }


def bool_rate(values: Iterable[bool]) -> float:
    items = [bool(value) for value in values]
    return safe_rate(sum(1 for value in items if value), len(items))
