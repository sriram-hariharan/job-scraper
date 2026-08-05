"""Explicit, dry-run-by-default Himalayas active-state retirement command."""

from __future__ import annotations

import argparse
import os
import re
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Iterator

from src.pipeline.himalayas_retention import run_himalayas_source_retirement


DEFAULT_CORPUS_PATH = Path("data/rag/job_corpus.jsonl")
MAX_BATCH_SIZE = 250
_ENV_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dry-run or explicitly execute Himalayas active-state retirement."
    )
    parser.add_argument("--corpus-path", default=str(DEFAULT_CORPUS_PATH))
    parser.add_argument("--owner-user-id", default="")
    parser.add_argument("--database-url-env", default="DATABASE_URL")
    parser.add_argument("--batch-size", type=int, default=MAX_BATCH_SIZE)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-source", default="")
    return parser


def validate_arguments(args: argparse.Namespace) -> None:
    if args.batch_size < 1 or args.batch_size > MAX_BATCH_SIZE:
        raise ValueError("Batch size must be between 1 and 250.")
    confirmation = str(args.confirm_source or "").strip()
    if confirmation and confirmation != "himalayas":
        raise ValueError("Source confirmation must be exactly himalayas.")
    if args.execute and confirmation != "himalayas":
        raise ValueError("Execute mode requires --confirm-source himalayas.")
    if args.execute and not str(args.owner_user_id or "").strip():
        raise ValueError("Execute mode requires --owner-user-id.")
    if not _ENV_NAME_PATTERN.fullmatch(str(args.database_url_env or "")):
        raise ValueError("Invalid database URL environment variable name.")


@contextmanager
def _rag_database_url_alias(database_url_env: str) -> Iterator[None]:
    env_name = str(database_url_env or "").strip()
    value = str(os.environ.get(env_name, "") or "").strip()
    if not value:
        raise ValueError("Configured database URL environment variable is unavailable.")
    if env_name == "DATABASE_URL":
        yield
        return

    sentinel = object()
    previous: object | str = os.environ.get("DATABASE_URL", sentinel)
    os.environ["DATABASE_URL"] = value
    try:
        yield
    finally:
        if previous is sentinel:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = str(previous)


def run_command(
    args: argparse.Namespace,
    *,
    retirement_owner: Callable[..., Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    validate_arguments(args)
    owner = retirement_owner or run_himalayas_source_retirement
    kwargs = {
        "corpus_path": Path(args.corpus_path).expanduser(),
        "owner_user_id": str(args.owner_user_id or "").strip(),
        "dry_run": not bool(args.execute),
        "batch_size": int(args.batch_size),
        "database_url_env": str(args.database_url_env),
    }
    if retirement_owner is not None:
        return owner(**kwargs)
    with _rag_database_url_alias(str(args.database_url_env)):
        return owner(**kwargs)


def public_summary(result: Dict[str, Any]) -> Dict[str, Any]:
    surfaces = dict(result.get("surfaces", {}) or {})
    jsonl = dict(
        surfaces.get("jsonl", {})
        or surfaces.get("jsonl_preflight", {})
        or {}
    )
    jsonl_preflight = dict(surfaces.get("jsonl_preflight", {}) or {})
    rag_candidates = dict(surfaces.get("rag_candidates", {}) or {})
    rag = dict(surfaces.get("rag", {}) or {})
    seen_candidates = dict(surfaces.get("seen_candidates", {}) or {})
    seen = dict(surfaces.get("seen", {}) or {})
    failures = list(result.get("failures", []) or [])
    jsonl_candidates = int(jsonl_preflight.get("retirement_candidates", 0) or 0)
    rag_candidate_count = int(rag_candidates.get("candidate_count", 0) or 0)
    seen_candidate_count = int(seen_candidates.get("candidate_count", 0) or 0)
    return {
        "ok": result.get("ok") is True,
        "mode": "dry_run" if result.get("dry_run") is True else "execute",
        "jsonl_candidates": jsonl_candidates,
        "rag_candidates": rag_candidate_count,
        "promoted_seen_candidates": int(
            seen.get("promoted_candidate_count", 0) or 0
        ),
        "staging_seen_candidates": int(
            seen.get("staging_candidate_count", 0) or 0
        ),
        "missing_identity": int(jsonl_preflight.get("missing_identity", 0) or 0),
        "malformed_records": int(jsonl_preflight.get("malformed_records", 0) or 0),
        "total_eligible": jsonl_candidates + rag_candidate_count + seen_candidate_count,
        "jsonl_retired": int(jsonl.get("retired", 0) or 0),
        "rag_deleted": int(rag.get("deleted_count", 0) or 0),
        "promoted_seen_deleted": int(seen.get("promoted_deleted_count", 0) or 0),
        "staging_seen_deleted": int(seen.get("staging_deleted_count", 0) or 0),
        "rag_cache_invalidation_succeeded": (
            rag.get("cache_invalidation_succeeded") is True
        ),
        "failures": len(failures),
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_command(args)
        summary = public_summary(result)
    except (OSError, RuntimeError, SystemExit, ValueError) as exc:
        print(f"error=validation_or_surface_failure error_type={type(exc).__name__}", file=sys.stderr)
        return 2

    for key in sorted(summary):
        print(f"{key}={summary[key]}")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
