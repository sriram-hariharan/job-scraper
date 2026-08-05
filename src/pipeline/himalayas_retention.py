from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional


MANAGED_SOURCE = "himalayas"
MAX_BATCH_SIZE = 250
MAX_EXPIRY_LENGTH = 64
MAX_IDENTITY_LENGTH = 4096
_IDENTITY_FIELDS = ("merge_key", "doc_id", "job_doc_id", "job_id")


def _clean_string(value: Any, maximum: int) -> str:
    if not isinstance(value, str):
        return ""
    text = value.strip()
    if not text or len(text) > maximum:
        return ""
    return text


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_stored_expiry(value: Any) -> Optional[datetime]:
    text = _clean_string(value, MAX_EXPIRY_LENGTH)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def stable_identity(record: Dict[str, Any]) -> str:
    if not isinstance(record, dict):
        return ""
    for field in _IDENTITY_FIELDS:
        value = _clean_string(record.get(field), MAX_IDENTITY_LENGTH)
        if value:
            return value
    return ""


def classify_expired_record(
    record: Dict[str, Any],
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    if not isinstance(record, dict) or record.get("source") != MANAGED_SOURCE:
        return {"eligible": False, "reason": "unmanaged_source", "identity": ""}
    identity = stable_identity(record)
    if not identity:
        return {"eligible": False, "reason": "missing_identity", "identity": ""}
    expiry = parse_stored_expiry(record.get("expiry_date"))
    if expiry is None:
        return {
            "eligible": False,
            "reason": "missing_or_invalid_expiry",
            "identity": identity,
        }
    clock = now if now is not None else utc_now()
    if not isinstance(clock, datetime) or clock.tzinfo is None or clock.utcoffset() is None:
        raise ValueError("Cleanup clock must be timezone-aware.")
    eligible = expiry <= clock.astimezone(timezone.utc)
    return {
        "eligible": eligible,
        "reason": "expired" if eligible else "unexpired",
        "identity": identity,
    }


def classify_retirement_record(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict) or record.get("source") != MANAGED_SOURCE:
        return {"eligible": False, "reason": "unmanaged_source", "identity": ""}
    identity = stable_identity(record)
    if not identity:
        return {"eligible": False, "reason": "missing_identity", "identity": ""}
    return {"eligible": True, "reason": "managed_source", "identity": identity}


def summarize_expiry_candidates(
    records: Iterable[Dict[str, Any]],
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    summary = {
        "inspected": 0,
        "eligible_expired": 0,
        "unexpired": 0,
        "unmanaged_source": 0,
        "missing_identity": 0,
        "missing_or_invalid_expiry": 0,
        "identities": [],
    }
    for record in records:
        summary["inspected"] += 1
        classification = classify_expired_record(record, now=now)
        reason = classification["reason"]
        if classification["eligible"]:
            summary["eligible_expired"] += 1
            summary["identities"].append(classification["identity"])
        elif reason in summary:
            summary[reason] += 1
    summary["identities"] = sorted(set(summary["identities"]))[:MAX_BATCH_SIZE]
    return summary


def run_himalayas_retention_foundation(
    *,
    corpus_path: str | Path,
    owner_user_id: str = "",
    dry_run: bool = True,
    batch_size: int = MAX_BATCH_SIZE,
    now: Optional[datetime] = None,
    jsonl_pruner: Optional[Callable[..., Dict[str, Any]]] = None,
    rag_candidate_lister: Optional[Callable[..., Dict[str, Any]]] = None,
    rag_deleter: Optional[Callable[..., Dict[str, Any]]] = None,
    seen_deleter: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    safe_batch = int(batch_size)
    if safe_batch < 1 or safe_batch > MAX_BATCH_SIZE:
        raise ValueError("Himalayas retention batch size must be between 1 and 250.")
    clock = now if now is not None else utc_now()
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise ValueError("Cleanup clock must be timezone-aware.")

    if jsonl_pruner is None:
        from src.rag.export_job_corpus import prune_expired_himalayas_jsonl

        jsonl_pruner = prune_expired_himalayas_jsonl
    if rag_candidate_lister is None or rag_deleter is None:
        from src.storage.rag_store import (
            delete_himalayas_rag_merge_keys,
            list_himalayas_rag_candidates,
        )

        rag_candidate_lister = rag_candidate_lister or list_himalayas_rag_candidates
        rag_deleter = rag_deleter or delete_himalayas_rag_merge_keys
    if seen_deleter is None and owner_user_id:
        from src.storage.user_pipeline.store import (
            delete_himalayas_seen_jobs_exact_postgres_payload,
        )

        seen_deleter = delete_himalayas_seen_jobs_exact_postgres_payload

    result: Dict[str, Any] = {
        "ok": True,
        "dry_run": bool(dry_run),
        "cross_store_atomic": False,
        "surface_order": ["jsonl", "rag_candidates", "rag_delete", "seen_delete"],
        "surfaces": {},
        "failures": [],
    }

    try:
        result["surfaces"]["jsonl"] = jsonl_pruner(
            corpus_path,
            dry_run=dry_run,
            now=clock,
        )
    except Exception as exc:
        result["ok"] = False
        result["failures"].append({"surface": "jsonl", "error": exc.__class__.__name__})

    candidates = []
    try:
        listed = rag_candidate_lister(limit=safe_batch)
        candidates = list(listed.get("rows", []) or [])
        result["surfaces"]["rag_candidates"] = {
            "count": len(candidates),
            "next_cursor_present": bool(listed.get("next_cursor")),
        }
    except Exception as exc:
        result["ok"] = False
        result["failures"].append(
            {"surface": "rag_candidates", "error": exc.__class__.__name__}
        )

    summary = summarize_expiry_candidates(candidates, now=clock)
    merge_keys = [
        record.get("merge_key", "")
        for record in candidates
        if classify_expired_record(record, now=clock)["eligible"]
    ]
    merge_keys = sorted({value for value in merge_keys if isinstance(value, str) and value})
    try:
        result["surfaces"]["rag_delete"] = rag_deleter(
            merge_keys,
            dry_run=dry_run,
        )
        result["surfaces"]["rag_expiry_summary"] = {
            key: value for key, value in summary.items() if key != "identities"
        }
    except Exception as exc:
        result["ok"] = False
        result["failures"].append({"surface": "rag_delete", "error": exc.__class__.__name__})

    seen_keys = sorted(
        {
            f"{MANAGED_SOURCE}:{record['job_id'].strip()}"
            for record in candidates
            if classify_expired_record(record, now=clock)["eligible"]
            and isinstance(record.get("job_id"), str)
            and record["job_id"].strip()
        }
    )
    if owner_user_id and seen_deleter is not None:
        try:
            result["surfaces"]["seen_delete"] = seen_deleter(
                owner_user_id=owner_user_id,
                seen_keys=seen_keys,
                dry_run=dry_run,
            )
        except Exception as exc:
            result["ok"] = False
            result["failures"].append(
                {"surface": "seen_delete", "error": exc.__class__.__name__}
            )
    else:
        result["surfaces"]["seen_delete"] = {
            "attempted": False,
            "reason": "owner_not_requested",
        }

    return result


def _retirement_failure(
    result: Dict[str, Any],
    surface: str,
    exc: BaseException | None = None,
) -> Dict[str, Any]:
    result["ok"] = False
    result["failures"].append(
        {
            "surface": surface,
            "error": exc.__class__.__name__ if exc is not None else "operation_failed",
        }
    )
    return result


def run_himalayas_source_retirement(
    *,
    corpus_path: str | Path,
    owner_user_id: str = "",
    dry_run: bool = True,
    batch_size: int = MAX_BATCH_SIZE,
    database_url_env: str = "DATABASE_URL",
    jsonl_retirement_owner: Optional[Callable[..., Dict[str, Any]]] = None,
    rag_candidate_lister: Optional[Callable[..., Dict[str, Any]]] = None,
    rag_deleter: Optional[Callable[..., Dict[str, Any]]] = None,
    seen_candidate_lister: Optional[Callable[..., Dict[str, Any]]] = None,
    seen_deleter: Optional[Callable[..., Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    safe_batch = int(batch_size)
    if safe_batch < 1 or safe_batch > MAX_BATCH_SIZE:
        raise ValueError("Himalayas retirement batch size must be between 1 and 250.")
    owner = _clean_string(owner_user_id, MAX_IDENTITY_LENGTH)
    if not dry_run and not owner:
        raise ValueError("Execute mode requires an owner for seen-job cleanup.")

    if jsonl_retirement_owner is None:
        from src.rag.export_job_corpus import retire_himalayas_jsonl

        jsonl_retirement_owner = retire_himalayas_jsonl
    if rag_candidate_lister is None or rag_deleter is None:
        from src.storage.rag_store import (
            delete_himalayas_rag_merge_keys,
            list_himalayas_rag_candidates,
        )

        rag_candidate_lister = rag_candidate_lister or list_himalayas_rag_candidates
        rag_deleter = rag_deleter or delete_himalayas_rag_merge_keys
    if owner and (seen_candidate_lister is None or seen_deleter is None):
        from src.storage.user_pipeline.store import (
            delete_himalayas_seen_jobs_exact_postgres_payload,
            list_himalayas_seen_job_candidates_postgres_payload,
        )

        if seen_candidate_lister is None:
            seen_candidate_lister = lambda **kwargs: (
                list_himalayas_seen_job_candidates_postgres_payload(
                    database_url_env=database_url_env,
                    **kwargs,
                )
            )
        if seen_deleter is None:
            seen_deleter = lambda **kwargs: (
                delete_himalayas_seen_jobs_exact_postgres_payload(
                    database_url_env=database_url_env,
                    **kwargs,
                )
            )

    result: Dict[str, Any] = {
        "ok": True,
        "dry_run": bool(dry_run),
        "cross_store_atomic": False,
        "surface_order": ["preflight", "jsonl", "rag", "seen"],
        "surfaces": {},
        "failures": [],
    }

    try:
        jsonl_preflight = jsonl_retirement_owner(corpus_path, dry_run=True)
        result["surfaces"]["jsonl_preflight"] = dict(jsonl_preflight or {})
    except Exception as exc:
        return _retirement_failure(result, "jsonl_preflight", exc)

    try:
        rag_listing = rag_candidate_lister(limit=safe_batch)
        if not isinstance(rag_listing, dict) or rag_listing.get("ok") is not True:
            return _retirement_failure(result, "rag_candidates")
        rag_rows = list(rag_listing.get("rows", []) or [])
        if len(rag_rows) > safe_batch or any(
            not isinstance(row, dict)
            or row.get("source") != MANAGED_SOURCE
            or not isinstance(row.get("merge_key"), str)
            or not row["merge_key"].strip()
            for row in rag_rows
        ):
            return _retirement_failure(result, "rag_candidates")
        merge_keys = sorted(
            {
                row.get("merge_key", "").strip()
                for row in rag_rows
                if isinstance(row, dict)
                and isinstance(row.get("merge_key"), str)
                and row.get("source") == MANAGED_SOURCE
                and row["merge_key"].strip()
            }
        )
        result["surfaces"]["rag_candidates"] = {
            "candidate_count": len(merge_keys),
            "next_cursor_present": bool(rag_listing.get("next_cursor")),
        }
    except Exception as exc:
        return _retirement_failure(result, "rag_candidates", exc)

    seen_keys = []
    if owner:
        try:
            seen_listing = seen_candidate_lister(
                owner_user_id=owner,
                limit=safe_batch,
            )
            if not isinstance(seen_listing, dict) or seen_listing.get("ok") is not True:
                return _retirement_failure(result, "seen_candidates")
            seen_rows = list(seen_listing.get("rows", []) or [])
            if len(seen_rows) > safe_batch or any(
                not isinstance(row, dict)
                or not isinstance(row.get("seen_key"), str)
                or not row["seen_key"].strip()
                for row in seen_rows
            ):
                return _retirement_failure(result, "seen_candidates")
            seen_keys = sorted(
                {
                    row.get("seen_key", "").strip()
                    for row in seen_rows
                    if isinstance(row, dict)
                    and isinstance(row.get("seen_key"), str)
                    and row["seen_key"].strip()
                }
            )
            result["surfaces"]["seen_candidates"] = {
                "candidate_count": len(seen_keys),
                "next_cursor_present": bool(seen_listing.get("next_cursor")),
            }
        except Exception as exc:
            return _retirement_failure(result, "seen_candidates", exc)
    else:
        result["surfaces"]["seen_candidates"] = {
            "candidate_count": 0,
            "attempted": False,
            "reason": "owner_not_requested",
        }

    if dry_run:
        try:
            rag_result = rag_deleter(merge_keys, dry_run=True)
            result["surfaces"]["rag"] = rag_result
            if not isinstance(rag_result, dict) or rag_result.get("ok") is not True:
                return _retirement_failure(result, "rag")
        except Exception as exc:
            return _retirement_failure(result, "rag", exc)
        if owner:
            try:
                seen_result = seen_deleter(
                    owner_user_id=owner,
                    seen_keys=seen_keys,
                    dry_run=True,
                )
                result["surfaces"]["seen"] = seen_result
                if not isinstance(seen_result, dict) or seen_result.get("ok") is not True:
                    return _retirement_failure(result, "seen")
            except Exception as exc:
                return _retirement_failure(result, "seen", exc)
        else:
            result["surfaces"]["seen"] = {
                "attempted": False,
                "reason": "owner_not_requested",
                "promoted_candidate_count": 0,
                "staging_candidate_count": 0,
            }
        return result

    try:
        result["surfaces"]["jsonl"] = jsonl_retirement_owner(
            corpus_path,
            dry_run=False,
        )
    except Exception as exc:
        return _retirement_failure(result, "jsonl", exc)

    try:
        rag_result = rag_deleter(merge_keys, dry_run=False)
        result["surfaces"]["rag"] = rag_result
        if not isinstance(rag_result, dict) or rag_result.get("ok") is not True:
            return _retirement_failure(result, "rag")
    except Exception as exc:
        return _retirement_failure(result, "rag", exc)

    try:
        seen_result = seen_deleter(
            owner_user_id=owner,
            seen_keys=seen_keys,
            dry_run=False,
        )
        result["surfaces"]["seen"] = seen_result
        if not isinstance(seen_result, dict) or seen_result.get("ok") is not True:
            return _retirement_failure(result, "seen")
    except Exception as exc:
        return _retirement_failure(result, "seen", exc)

    return result
