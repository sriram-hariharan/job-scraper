"""Item 4B/C: planning owner isolation + artifact path hardening.

4A demonstrated that owner-scoped planning routes did not bind the request to
the authenticated owner, that patch selections persisted with a blank owner,
and that a caller-supplied output_dir acted as the security containment root.
These tests pin the repaired contract.
"""
from pathlib import Path

import pytest

from fastapi import HTTPException
from fastapi.testclient import TestClient


OWNER_A = "owner-a"
OWNER_B = "owner-b"
RUN_A = "20260101T000000000000Z"
RUN_B = "20260202T000000000000Z"


@pytest.fixture
def owner_runs(tmp_path, monkeypatch):
    """Owner/run separated planning roots plus a stubbed validated resolver."""
    from src.app import api as app_api

    roots = {}
    for owner, run in ((OWNER_A, RUN_A), (OWNER_B, RUN_B)):
        root = tmp_path / "tmp" / "pipeline_runs" / owner / run / "application_planning"
        root.mkdir(parents=True)
        (root / "current_run_job_corpus.jsonl").write_text("{}\n", encoding="utf-8")
        roots[(owner, run)] = root

    def fake_resolver(*, owner_user_id: str, run_id: str):
        key = (str(owner_user_id or "").strip(), str(run_id or "").strip())
        if key not in roots:
            # Mirrors the real resolver: a run that is not this owner's is rejected.
            raise ValueError("The selected pipeline run has an invalid artifact location.")
        return roots[key], roots[key] / "current_run_job_corpus.jsonl"

    monkeypatch.setattr(
        app_api.services, "resolve_user_pipeline_run_planning_paths", fake_resolver
    )
    return roots


def _auth(monkeypatch, owner: str | None):
    """Pin the authenticated owner, or simulate an unauthenticated request."""
    from src.app import api as app_api

    def fake_require(_request):
        if not owner:
            raise HTTPException(status_code=401, detail="Authentication required.")
        return owner

    monkeypatch.setattr(app_api, "_require_auth_owner_user_id", fake_require)


# --- Owner-scoped path resolver ------------------------------------------------

def test_resolver_requires_authenticated_owner(owner_runs):
    from src.app import api as app_api

    with pytest.raises(HTTPException) as exc:
        app_api._owner_scoped_planning_output_dir(
            owner_user_id="", pipeline_run_id=RUN_A, requested_output_dir=""
        )
    assert exc.value.status_code == 401


def test_resolver_requires_run_identity_and_never_defaults(owner_runs):
    """Fail closed: an authenticated owner-scoped op must not fall back to a shared root."""
    from src.app import api as app_api

    with pytest.raises(HTTPException) as exc:
        app_api._owner_scoped_planning_output_dir(
            owner_user_id=OWNER_A,
            pipeline_run_id="",
            requested_output_dir=str(app_api.services.DEFAULT_OUTPUT_DIR),
        )
    assert exc.value.status_code == 400
    assert "pipeline_run_id" in str(exc.value.detail)


def test_resolver_rejects_run_belonging_to_another_owner(owner_runs):
    from src.app import api as app_api

    with pytest.raises(HTTPException) as exc:
        app_api._owner_scoped_planning_output_dir(
            owner_user_id=OWNER_A, pipeline_run_id=RUN_B, requested_output_dir=""
        )
    assert exc.value.status_code == 400


def test_resolver_ignores_caller_supplied_output_dir(owner_runs):
    """The 4A weakness: a foreign output_dir must never become the containment root."""
    from src.app import api as app_api

    foreign = str(owner_runs[(OWNER_B, RUN_B)])
    resolved = app_api._owner_scoped_planning_output_dir(
        owner_user_id=OWNER_A,
        pipeline_run_id=RUN_A,
        requested_output_dir=foreign,
    )
    assert resolved == owner_runs[(OWNER_A, RUN_A)]
    assert OWNER_B not in str(resolved)
    assert str(resolved).endswith(f"{OWNER_A}/{RUN_A}/application_planning")


def test_recorded_output_dir_resolves_owner_run_without_path_parsing(owner_runs, monkeypatch):
    from types import SimpleNamespace

    from src.app import planning_ui, services

    rows = [
        {
            "run_id": RUN_A,
            "status": "succeeded",
            "config_json": {"output_dir": str(owner_runs[(OWNER_A, RUN_A)])},
        }
    ]
    monkeypatch.setattr(
        services,
        "get_user_pipeline_runs_postgres_payload",
        lambda **_kwargs: {"rows": rows},
    )

    assert services.resolve_user_pipeline_run_id_from_planning_output_dir(
        owner_user_id=OWNER_A,
        output_dir=str(owner_runs[(OWNER_A, RUN_A)]),
    ) == RUN_A
    assert services.resolve_user_pipeline_run_id_from_planning_output_dir(
        owner_user_id=OWNER_B,
        output_dir=str(owner_runs[(OWNER_B, RUN_B)]),
    ) == ""

    request = SimpleNamespace(
        state=SimpleNamespace(auth_user={"user_id": OWNER_A})
    )
    html = planning_ui.scan_workspace_route(
        request,
        resume="resume.pdf",
        output_dir=str(owner_runs[(OWNER_A, RUN_A)]),
    )
    assert f'data-pipeline-run-id="{RUN_A}"' in html


# --- select-patches ------------------------------------------------------------

def test_select_patches_rejects_unauthenticated(owner_runs, monkeypatch):
    from src.app import api as app_api

    _auth(monkeypatch, None)
    with pytest.raises(HTTPException) as exc:
        app_api.planning_select_patches(
            http_request=object(), payload={"pipeline_run_id": RUN_A}
        )
    assert exc.value.status_code == 401


def test_select_patches_requires_run_identity(owner_runs, monkeypatch):
    from src.app import api as app_api

    _auth(monkeypatch, OWNER_A)
    with pytest.raises(HTTPException) as exc:
        app_api.planning_select_patches(http_request=object(), payload={})
    assert exc.value.status_code == 400


def test_select_patches_threads_owner_and_authoritative_root(owner_runs, monkeypatch):
    from src.app import api as app_api

    _auth(monkeypatch, OWNER_A)
    seen = {}

    def fake_record(**kwargs):
        seen.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(
        app_api.services, "record_planning_patch_selection_payload", fake_record
    )

    app_api.planning_select_patches(
        http_request=object(),
        payload={
            "pipeline_run_id": RUN_A,
            "tailoring_json_path": "x__tailoring.json",
            "selected_candidate_ids": ["c1"],
        },
        output_dir=str(owner_runs[(OWNER_B, RUN_B)]),  # foreign root
    )

    assert seen["owner_user_id"] == OWNER_A
    assert seen["output_dir"] == owner_runs[(OWNER_A, RUN_A)]
    assert OWNER_B not in str(seen["output_dir"])


def test_patch_selection_service_fails_closed_on_blank_owner():
    """No new blank-owner patch-selection row may be created."""
    from src.app import services

    with pytest.raises(ValueError, match="Authenticated owner is required"):
        services.record_planning_patch_selection_payload(
            tailoring_json_path="x__tailoring.json",
            owner_user_id="",
        )


def test_patch_selection_service_accepts_owner_parameter():
    import inspect

    from src.app import services

    sig = inspect.signature(services.record_planning_patch_selection_payload)
    assert "owner_user_id" in sig.parameters


def test_patch_selection_row_carries_owner(monkeypatch, tmp_path):
    """The persisted row must include owner_user_id, not rely on the store default."""
    from src.app import services

    captured = {}
    monkeypatch.setattr(
        services,
        "_dual_write_patch_selection_postgres",
        lambda row: captured.update(row) or {"attempted": False, "ok": True},
    )

    artifact = tmp_path / "job__tailoring.json"
    artifact.write_text(
        '{"replacement_candidates": [{"candidate_id": "c1"}],'
        ' "selected_resume": "r.pdf"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        services, "_resolve_planning_artifact_path", lambda *_a, **_k: artifact
    )
    monkeypatch.setattr(services, "_tailoring_artifact_candidate_ids", lambda _p: ["c1"])

    try:
        services.record_planning_patch_selection_payload(
            output_dir=tmp_path,
            tailoring_json_path=str(artifact),
            selected_candidate_ids=["c1"],
            selected_resume="r.pdf",
            owner_user_id=OWNER_A,
        )
    except Exception:
        # Downstream artifact shaping is out of scope; the row is what matters.
        pass

    assert captured.get("owner_user_id") == OWNER_A, captured


# --- draft save / load ---------------------------------------------------------

def _draft_save_request(run_id: str):
    from src.app.api import PlanningWorkspaceDraftSaveRequest

    return PlanningWorkspaceDraftSaveRequest(
        tailoring_json_path="x__tailoring.json", pipeline_run_id=run_id
    )


def _draft_load_request(run_id: str):
    from src.app.api import PlanningWorkspaceDraftLoadRequest

    return PlanningWorkspaceDraftLoadRequest(
        tailoring_json_path="x__tailoring.json", pipeline_run_id=run_id
    )


def test_draft_save_rejects_unauthenticated(owner_runs, monkeypatch):
    from src.app import api as app_api

    _auth(monkeypatch, None)
    with pytest.raises(HTTPException) as exc:
        app_api.save_workspace_draft(
            http_request=object(), request=_draft_save_request(RUN_A)
        )
    assert exc.value.status_code == 401


def test_draft_save_uses_owner_run_root_and_ignores_output_dir(owner_runs, monkeypatch):
    from src.app import api as app_api

    _auth(monkeypatch, OWNER_A)
    seen = {}
    monkeypatch.setattr(
        app_api.services,
        "save_tailoring_workspace_draft_payload",
        lambda **kw: seen.update(kw) or {"ok": True},
    )

    app_api.save_workspace_draft(
        http_request=object(),
        request=_draft_save_request(RUN_A),
        output_dir=str(owner_runs[(OWNER_B, RUN_B)]),
    )
    assert seen["output_dir"] == owner_runs[(OWNER_A, RUN_A)]


def test_draft_save_cannot_target_another_owner_run(owner_runs, monkeypatch):
    from src.app import api as app_api

    _auth(monkeypatch, OWNER_A)
    with pytest.raises(HTTPException) as exc:
        app_api.save_workspace_draft(
            http_request=object(), request=_draft_save_request(RUN_B)
        )
    assert exc.value.status_code == 400


def test_draft_load_rejects_unauthenticated(owner_runs, monkeypatch):
    from src.app import api as app_api

    _auth(monkeypatch, None)
    with pytest.raises(HTTPException) as exc:
        app_api.load_workspace_draft(
            http_request=object(), request=_draft_load_request(RUN_A)
        )
    assert exc.value.status_code == 401


def test_draft_load_uses_owner_run_root_and_ignores_output_dir(owner_runs, monkeypatch):
    from src.app import api as app_api

    _auth(monkeypatch, OWNER_A)
    seen = {}
    monkeypatch.setattr(
        app_api.services,
        "load_tailoring_workspace_draft_payload",
        lambda **kw: seen.update(kw) or {"ok": True},
    )

    app_api.load_workspace_draft(
        http_request=object(),
        request=_draft_load_request(RUN_A),
        output_dir=str(owner_runs[(OWNER_B, RUN_B)]),
    )
    assert seen["output_dir"] == owner_runs[(OWNER_A, RUN_A)]


def test_draft_load_cannot_read_another_owner_run(owner_runs, monkeypatch):
    from src.app import api as app_api

    _auth(monkeypatch, OWNER_A)
    with pytest.raises(HTTPException) as exc:
        app_api.load_workspace_draft(
            http_request=object(), request=_draft_load_request(RUN_B)
        )
    assert exc.value.status_code == 400


def test_artifact_draft_http_round_trip_requires_run_identity(owner_runs, monkeypatch):
    from src.app import api as app_api

    output_dir = owner_runs[(OWNER_A, RUN_A)]
    packet_dir = output_dir / "job_packets"
    packet_dir.mkdir(exist_ok=True)
    artifact = packet_dir / "reddit__staff_data_scientist__resume__tailoring.json"
    artifact.write_text(
        '{"job":{"company":"reddit","title":"Staff Data Scientist"},'
        '"selection":{"selected_resume":"resume.pdf"},'
        '"selected_patch_candidate_ids":[]}',
        encoding="utf-8",
    )

    def auth_guard(request):
        request.state.auth_user = {"user_id": OWNER_A}
        return None

    monkeypatch.setattr(app_api, "auth_guard_response", auth_guard)
    monkeypatch.setattr(app_api, "_require_auth_owner_user_id", lambda _request: OWNER_A)
    monkeypatch.setattr(
        app_api.bulk_generation_service,
        "active_bulk_generation_guard_state",
        lambda **_kwargs: {},
    )
    client = TestClient(app_api.app)
    issue_id = "scan_issue:skills:keyword:python_or_r"
    request_body = {
        "pipeline_run_id": RUN_A,
        "tailoring_json_path": artifact.relative_to(output_dir).as_posix(),
        "selected_resume": "resume.pdf",
        "selected_patch_candidate_ids": [],
        "manual_bullet_edits": {},
        "rewrite_review_decisions": {},
        "excluded_scan_issue_ids": [issue_id],
        "personal_details": {},
    }

    saved = client.post("/planning/save-workspace-draft", json=request_body)
    assert saved.status_code == 200
    assert saved.json()["draft"]["excluded_scan_issue_ids"] == [issue_id]

    read_back = client.post(
        "/planning/load-workspace-draft",
        json={
            "pipeline_run_id": RUN_A,
            "tailoring_json_path": request_body["tailoring_json_path"],
            "selected_resume": "resume.pdf",
        },
    )
    assert read_back.status_code == 200
    assert read_back.json()["draft"]["excluded_scan_issue_ids"] == [issue_id]

    reinclude = client.post(
        "/planning/save-workspace-draft",
        json={**request_body, "excluded_scan_issue_ids": []},
    )
    assert reinclude.status_code == 200
    assert reinclude.json()["draft"]["excluded_scan_issue_ids"] == []


# --- preview (read-only, still owner scoped) -----------------------------------

def test_preview_selected_patches_rejects_unauthenticated(owner_runs, monkeypatch):
    from src.app import api as app_api

    _auth(monkeypatch, None)
    with pytest.raises(HTTPException) as exc:
        app_api.planning_preview_selected_patches(
            http_request=object(), payload={"pipeline_run_id": RUN_A}
        )
    assert exc.value.status_code == 401


def test_preview_is_not_a_cross_owner_read_channel(owner_runs, monkeypatch):
    from src.app import api as app_api

    _auth(monkeypatch, OWNER_A)
    with pytest.raises(HTTPException) as exc:
        app_api.planning_preview_selected_patches(
            http_request=object(), payload={"pipeline_run_id": RUN_B}
        )
    assert exc.value.status_code == 400


def test_preview_uses_owner_run_root(owner_runs, monkeypatch):
    from src.app import api as app_api

    _auth(monkeypatch, OWNER_A)
    seen = {}
    monkeypatch.setattr(
        app_api.services,
        "preview_planning_patch_selection_payload",
        lambda **kw: seen.update(kw) or {"ok": True},
    )
    app_api.planning_preview_selected_patches(
        http_request=object(),
        payload={"pipeline_run_id": RUN_A, "tailoring_json_path": "x__tailoring.json"},
        output_dir=str(owner_runs[(OWNER_B, RUN_B)]),
    )
    assert seen["output_dir"] == owner_runs[(OWNER_A, RUN_A)]


# --- frontend run-identity threading -------------------------------------------

def test_workspace_page_renders_pipeline_run_id():
    from src.app.planning_ui import scan_workspace, tailoring_workspace

    html = tailoring_workspace(
        company="C", title="T", job_doc_id="J", output_dir="/tmp/x",
        pipeline_run_id=RUN_A,
    )
    assert f'data-pipeline-run-id="{RUN_A}"' in html

    scan_html = scan_workspace(
        company="C", title="T", resume="resume.pdf", output_dir="/tmp/x",
        pipeline_run_id=RUN_A,
    )
    assert f'data-pipeline-run-id="{RUN_A}"' in scan_html


def test_planning_js_threads_run_identity():
    js = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    # The workspace link propagates the identity the planning row already carries.
    assert 'params.set("pipeline_run_id", workspaceRunId)' in js
    # Context exposes it and both draft paths send it.
    assert "pipelineRunId: String(page.dataset.pipelineRunId" in js
    assert js.count('pipeline_run_id: context.pipelineRunId || ""') >= 3

    scan_js = Path("src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    assert "pipelineRunId: String(root.dataset.pipelineRunId" in scan_js
    assert "pipeline_run_id: context.pipelineRunId" in scan_js
    load_draft = scan_js.split("async function loadScanWorkspaceDraftState()", 1)[1].split(
        "async function saveScanWorkspaceDraftState", 1
    )[0]
    assert load_draft.count("pipeline_run_id: payload.pipeline_run_id") == 2


# --- preservation ---------------------------------------------------------------

def test_operator_resume_selection_owner_scoping_preserved():
    import inspect

    from src.app import services

    sig = inspect.signature(services.record_operator_resume_selection_payload)
    assert "owner_user_id" in sig.parameters


def test_unknown_candidate_ids_still_fail_closed(monkeypatch, tmp_path):
    from src.app import services

    artifact = tmp_path / "job__tailoring.json"
    artifact.write_text(
        '{"replacement_candidates": [{"candidate_id": "c1"}]}', encoding="utf-8"
    )
    monkeypatch.setattr(
        services, "_resolve_planning_artifact_path", lambda *_a, **_k: artifact
    )
    monkeypatch.setattr(services, "_tailoring_artifact_candidate_ids", lambda _p: ["c1"])

    with pytest.raises(ValueError, match="Unknown candidate IDs"):
        services.record_planning_patch_selection_payload(
            output_dir=tmp_path,
            tailoring_json_path=str(artifact),
            selected_candidate_ids=["does-not-exist"],
            owner_user_id=OWNER_A,
        )


def test_safety_metadata_flags_remain_false():
    """No auto-apply / ATS submission / recruiter messaging was introduced."""
    services_src = Path("src/app/services.py").read_text(encoding="utf-8")
    for flag in (
        '"auto_apply_performed": False',
        '"ats_submission_performed": False',
        '"recruiter_message_sent": False',
        '"mark_applied_performed": False',
        '"source_resume_mutation_performed": False',
    ):
        assert flag in services_src
