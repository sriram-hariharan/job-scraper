"""Bounded substantive parity for authoritative production-shadow facts."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Dict, Mapping

from src.agents.evidence_chain_shadow_parity import canonical_artifact_digest


PRODUCTION_SHADOW_PARITY_VERSION = "production-shadow-parity-v1"
PARITY_CLASSIFICATIONS = frozenset(
    {
        "exact_match",
        "mismatch",
        "authoritative_missing",
        "shadow_missing",
        "both_missing",
        "incomparable",
    }
)
PARITY_STATUSES = frozenset(
    {"passed", "mismatch", "incomplete", "incomparable", "failed"}
)
_FIELD_SPECS = (
    ("job_id", True),
    ("selected_resume_id", True),
    ("queue_rank", True),
    ("action", True),
    ("advisory_priority", True),
    ("advisory_reason_codes", False),
    ("tailoring_decision", True),
    ("tailoring_reason_codes", False),
    ("operator_review_lane", True),
    ("packet_generation_allowed", True),
    ("requires_manual_review", True),
    ("packet_resume", True),
)
_CODE = re.compile(r"[a-z0-9_.-]{1,120}")
_IDENTITY = re.compile(r"[A-Za-z0-9_.:@/-]{1,200}")
_ENUM = re.compile(r"[A-Za-z0-9_.:-]{1,80}")


class ProductionShadowParityError(ValueError):
    """A parity input or output contract was unsafe or malformed."""


def _present(value: Mapping[str, Any], field: str) -> bool:
    return field in value and value[field] is not None and value[field] != ""


def _canonical_value(field: str, value: Any) -> Any:
    if field == "queue_rank":
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ProductionShadowParityError("parity_value_invalid")
        return value
    if field in {"packet_generation_allowed", "requires_manual_review"}:
        if not isinstance(value, bool):
            raise ProductionShadowParityError("parity_value_invalid")
        return value
    if field in {"advisory_reason_codes", "tailoring_reason_codes"}:
        if not isinstance(value, list):
            raise ProductionShadowParityError("parity_value_invalid")
        codes: list[str] = []
        for item in value:
            code = str(item or "").strip()
            if not _CODE.fullmatch(code):
                raise ProductionShadowParityError("parity_value_invalid")
            if code not in codes:
                codes.append(code)
        return sorted(codes)[:25]
    text = str(value or "").strip()
    pattern = (
        _IDENTITY
        if field in {"job_id", "selected_resume_id", "packet_resume"}
        else _ENUM
    )
    if not pattern.fullmatch(text):
        raise ProductionShadowParityError("parity_value_invalid")
    return text


def _record(
    *,
    field: str,
    classification: str,
    reason_code: str,
    authoritative_present: bool,
    shadow_present: bool,
    authoritative_digest: str | None = None,
    shadow_digest: str | None = None,
) -> Dict[str, Any]:
    if classification not in PARITY_CLASSIFICATIONS:
        raise ProductionShadowParityError("parity_classification_invalid")
    if not _CODE.fullmatch(reason_code):
        raise ProductionShadowParityError("parity_reason_invalid")
    return {
        "field": field,
        "classification": classification,
        "reason_code": reason_code,
        "authoritative_present": authoritative_present,
        "shadow_present": shadow_present,
        "authoritative_digest": authoritative_digest,
        "shadow_digest": shadow_digest,
    }


def compare_production_shadow_parity(
    *,
    authoritative_facts: Mapping[str, Any],
    shadow_facts: Mapping[str, Any],
    incomparable_fields: Mapping[str, str] | None = None,
) -> Dict[str, Any]:
    """Compare detached allowlisted facts without retaining underlying values."""

    if not isinstance(authoritative_facts, Mapping) or not isinstance(
        shadow_facts, Mapping
    ):
        raise ProductionShadowParityError("parity_contract_invalid")
    authoritative = deepcopy(dict(authoritative_facts))
    shadow = deepcopy(dict(shadow_facts))
    incomparable = deepcopy(dict(incomparable_fields or {}))
    known_fields = {field for field, _required in _FIELD_SPECS}
    if not set(authoritative).issubset(known_fields) or not set(
        shadow
    ).issubset(known_fields):
        raise ProductionShadowParityError("parity_contract_invalid")
    if not set(incomparable).issubset(known_fields):
        raise ProductionShadowParityError("parity_field_invalid")

    records: list[Dict[str, Any]] = []
    required_by_field = dict(_FIELD_SPECS)
    substantive_fields: set[str] = set()
    malformed = False
    for field, required in _FIELD_SPECS:
        left_present = _present(authoritative, field)
        right_present = _present(shadow, field)
        if field in incomparable:
            reason = str(incomparable[field] or "").strip()
            if not _CODE.fullmatch(reason):
                raise ProductionShadowParityError("parity_reason_invalid")
            records.append(
                _record(
                    field=field,
                    classification="incomparable",
                    reason_code=reason,
                    authoritative_present=left_present,
                    shadow_present=right_present,
                )
            )
            continue
        if required or left_present or right_present:
            substantive_fields.add(field)
        if not left_present and not right_present:
            records.append(
                _record(
                    field=field,
                    classification="both_missing",
                    reason_code="fact_absent_on_both_sides",
                    authoritative_present=False,
                    shadow_present=False,
                )
            )
            continue
        if not left_present:
            records.append(
                _record(
                    field=field,
                    classification="authoritative_missing",
                    reason_code="authoritative_fact_missing",
                    authoritative_present=False,
                    shadow_present=True,
                )
            )
            continue
        if not right_present:
            records.append(
                _record(
                    field=field,
                    classification="shadow_missing",
                    reason_code="shadow_fact_missing",
                    authoritative_present=True,
                    shadow_present=False,
                )
            )
            continue
        try:
            left = _canonical_value(field, authoritative[field])
            right = _canonical_value(field, shadow[field])
            left_digest = canonical_artifact_digest(left)
            right_digest = canonical_artifact_digest(right)
        except (TypeError, ValueError):
            malformed = True
            records.append(
                _record(
                    field=field,
                    classification="incomparable",
                    reason_code="unsafe_or_malformed_fact",
                    authoritative_present=True,
                    shadow_present=True,
                )
            )
            continue
        exact = left_digest == right_digest
        records.append(
            _record(
                field=field,
                classification="exact_match" if exact else "mismatch",
                reason_code=(
                    "canonical_values_equal"
                    if exact
                    else "canonical_values_differ"
                ),
                authoritative_present=True,
                shadow_present=True,
                authoritative_digest=left_digest,
                shadow_digest=right_digest,
            )
        )

    counts = {
        classification: sum(
            row["classification"] == classification for row in records
        )
        for classification in PARITY_CLASSIFICATIONS
    }
    substantive_records = [
        row for row in records if row["field"] in substantive_fields
    ]
    substantive_mismatches = sum(
        row["classification"] == "mismatch" for row in substantive_records
    )
    required_missing = any(
        required_by_field[row["field"]]
        and row["classification"]
        in {"authoritative_missing", "shadow_missing", "both_missing"}
        for row in records
    )
    if malformed:
        status = "failed"
    elif substantive_mismatches:
        status = "mismatch"
    elif required_missing:
        status = "incomplete"
    elif substantive_records and all(
        row["classification"] == "exact_match"
        for row in substantive_records
    ):
        status = "passed"
    elif records and all(
        row["classification"] == "incomparable" for row in records
    ):
        status = "incomparable"
    else:
        status = "passed"
    if status not in PARITY_STATUSES:
        raise ProductionShadowParityError("parity_status_invalid")
    return {
        "parity_version": PRODUCTION_SHADOW_PARITY_VERSION,
        "parity_status": status,
        "compared_field_count": len(records) - counts["incomparable"],
        "exact_match_count": counts["exact_match"],
        "mismatch_count": counts["mismatch"],
        "authoritative_missing_count": (
            counts["authoritative_missing"] + counts["both_missing"]
        ),
        "shadow_missing_count": (
            counts["shadow_missing"] + counts["both_missing"]
        ),
        "incomparable_count": counts["incomparable"],
        "substantive_field_count": len(substantive_records),
        "substantive_exact_match_count": sum(
            row["classification"] == "exact_match"
            for row in substantive_records
        ),
        "substantive_mismatch_count": substantive_mismatches,
        "comparison_records": deepcopy(records),
    }
