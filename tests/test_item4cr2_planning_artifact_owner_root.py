"""Item 4C-R2: GET /planning-artifact authenticated owner-root containment.

This route is deliberately OWNER-scoped, not RUN-scoped: an owner may read any
of its own runs, but never another owner's. Authorization is decided solely by
a server-derived owner root, never by the requested path or output_dir.
"""
import json
from pathlib import Path

import pytest

from fastapi import HTTPException


OWNER_A = "owner-a"
OWNER_B = "owner-b"


def _write_artifact(root: Path, owner: str, run: str, name: str, data=None) -> Path:
    planning = root / owner / run / "application_planning" / "job_packets"
    planning.mkdir(parents=True, exist_ok=True)
    artifact = planning / name
    artifact.write_text(json.dumps(data if data is not None else {"ok": True}), encoding="utf-8")
    return artifact


@pytest.fixture
def scratch(tmp_path, monkeypatch):
    """Isolated pipeline-runs root with two owners and two Owner A runs."""
    from src.app import services

    monkeypatch.setattr(services, "DEFAULT_PIPELINE_SCRATCH_DIR", tmp_path)
    return {
        "root": tmp_path,
        "a_current": _write_artifact(tmp_path, OWNER_A, "run-current", "a1__tailoring.json"),
        "a_historical": _write_artifact(tmp_path, OWNER_A, "run-old", "a2__tailoring.json"),
        "b": _write_artifact(tmp_path, OWNER_B, "run-b", "b1__tailoring.json"),
    }


def _payload(path, owner: str | None, output_dir: Path | None = None):
    """Call the service exactly as the authenticated route does."""
    from src.app import services

    owner_root = services.owner_planning_artifact_root(owner) if owner else None
    return services.planning_artifact_payload(
        path=str(path),
        output_dir=output_dir if output_dir is not None else Path(str(path)).parent,
        owner_root=owner_root,
    )


# --- owner-root derivation -----------------------------------------------------

def test_owner_root_is_server_derived_from_existing_normalization(scratch):
    from src.app import services

    root = services.owner_planning_artifact_root(OWNER_A)
    assert root == (scratch["root"] / OWNER_A).resolve()
    # Reuses the same normalization the pipeline uses for its scratch dirs.
    assert root.name == services._safe_owner_dir_name(OWNER_A)


def test_blank_owner_is_rejected(scratch):
    from src.app import services

    with pytest.raises(ValueError, match="Authenticated owner is required"):
        services.owner_planning_artifact_root("")


def test_route_requires_explicit_owner_not_just_middleware(scratch, monkeypatch):
    """Being logged in is not authorization; the route needs the owner identity."""
    from src.app import api as app_api

    monkeypatch.setattr(
        app_api,
        "_require_auth_owner_user_id",
        lambda _r: (_ for _ in ()).throw(HTTPException(status_code=401, detail="x")),
    )
    with pytest.raises(HTTPException) as exc:
        app_api.planning_artifact(
            http_request=object(), path=str(scratch["a_current"])
        )
    assert exc.value.status_code == 401


# --- proof matrix: authenticated owner | artifact owner | run | result ---------

def test_owner_a_reads_own_current_run_artifact(scratch):
    payload = _payload(scratch["a_current"], OWNER_A)
    assert payload["ok"] is True


def test_owner_a_reads_own_historical_run_artifact(scratch):
    """Owner-scoped, not run-scoped: older runs of the SAME owner are allowed."""
    payload = _payload(scratch["a_historical"], OWNER_A)
    assert payload["ok"] is True


def test_owner_a_cannot_read_owner_b_artifact(scratch):
    with pytest.raises(ValueError, match="authenticated owner's planning directory"):
        _payload(scratch["b"], OWNER_A)


def test_owner_b_cannot_read_owner_a_artifact(scratch):
    with pytest.raises(ValueError, match="authenticated owner's planning directory"):
        _payload(scratch["a_current"], OWNER_B)


def test_blank_owner_cannot_read_any_artifact(scratch):
    from src.app import services

    with pytest.raises(ValueError, match="Authenticated owner is required"):
        services.owner_planning_artifact_root("")


# --- the path must never self-authorize ----------------------------------------

def test_foreign_output_dir_cannot_redirect_authorization(scratch):
    """output_dir is retained for compatibility but has zero authority."""
    with pytest.raises(ValueError, match="authenticated owner's planning directory"):
        _payload(
            scratch["b"], OWNER_A,
            output_dir=scratch["b"].parent,  # Owner B root supplied by caller
        )


def test_absolute_foreign_path_rejected(scratch):
    assert scratch["b"].is_absolute()
    with pytest.raises(ValueError, match="authenticated owner's planning directory"):
        _payload(scratch["b"], OWNER_A)


def test_traversal_toward_another_owner_rejected(scratch):
    traversal = (
        scratch["root"] / OWNER_A / "run-current" / "application_planning"
        / ".." / ".." / ".." / OWNER_B / "run-b" / "application_planning"
        / "job_packets" / "b1__tailoring.json"
    )
    with pytest.raises(ValueError):
        _payload(traversal, OWNER_A)


def test_job_packets_segment_cannot_self_authorize(scratch):
    """A syntactically valid application_planning/job_packets path is not authority."""
    assert "/application_planning/job_packets/" in str(scratch["b"]).replace("\\", "/")
    with pytest.raises(ValueError, match="authenticated owner's planning directory"):
        _payload(scratch["b"], OWNER_A)


def test_default_output_dir_cannot_become_fallback_root(scratch, monkeypatch):
    from src.app import services

    outside = scratch["root"].parent / "outside" / "application_planning"
    outside.mkdir(parents=True, exist_ok=True)
    stray = outside / "x__tailoring.json"
    stray.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(services, "DEFAULT_OUTPUT_DIR", outside)

    with pytest.raises(ValueError):
        _payload(stray, OWNER_A, output_dir=outside)


# --- preserved existing protections --------------------------------------------

def test_unsupported_extension_still_rejected(scratch):
    bad = scratch["a_current"].with_name("notes.txt")
    bad.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        _payload(bad, OWNER_A)


def test_missing_artifact_preserves_existing_failure(scratch):
    missing = scratch["a_current"].with_name("does_not_exist.json")
    with pytest.raises(ValueError):
        _payload(missing, OWNER_A)


def test_owner_neutral_service_callers_are_preserved(scratch):
    """Existing callers that pass no owner_root keep legacy behavior."""
    from src.app import services

    payload = services.planning_artifact_payload(
        path=str(scratch["a_current"]),
        output_dir=scratch["a_current"].parent,
    )
    assert payload["ok"] is True


def test_endpoint_remains_read_only():
    import inspect

    from src.app import api as app_api

    src = inspect.getsource(app_api.planning_artifact)
    for forbidden in ("insert_", "record_", "save_", "write_text", "delete_", "upsert_"):
        assert forbidden not in src


# --- caller compatibility (no pipeline_run_id requirement) ---------------------

def test_route_does_not_require_pipeline_run_id():
    """Scan-workspace has no run id; requiring one would break that caller."""
    import inspect

    from src.app import api as app_api

    sig = inspect.signature(app_api.planning_artifact)
    assert "pipeline_run_id" not in sig.parameters
    assert set(sig.parameters) == {"http_request", "path", "output_dir"}


def test_frontend_callers_unchanged_and_send_no_run_id():
    js = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    # buildArtifactUrl still sends only path + output_dir.
    assert "/planning-artifact?${params.toString()}" in js
    assert "async function loadArtifact(path, outputDir" in js
