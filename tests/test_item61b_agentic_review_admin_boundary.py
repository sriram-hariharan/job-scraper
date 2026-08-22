from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]
PROFILE_JS_PATH = ROOT / "src/app/static/profile.js"

ADMIN_USER = {
    "user_id": "admin-owner",
    "email": "admin@example.test",
    "is_admin": True,
    "access_level": "user",
}
ACCESS_LEVEL_ADMIN_USER = {
    "user_id": "access-admin-owner",
    "email": "access-admin@example.test",
    "is_admin": False,
    "access_level": "admin",
}
NON_ADMIN_USER = {
    "user_id": "non-admin-owner",
    "email": "user@example.test",
    "is_admin": False,
    "access_level": "user",
}

DEDICATED_APIS = (
    (
        "/profile/pipeline-runs/run-61b/agentic-review-data",
        "profile_pipeline_run_agentic_review_payload",
        "run_id",
    ),
    (
        "/profile/pipeline-runs/run-61b/agent-trace",
        "agent_trace_payload",
        "pipeline_run_id",
    ),
    (
        "/profile/pipeline-runs/run-61b/evidence-chain-trace",
        "get_evidence_chain_trace_readback_payload",
        "pipeline_run_id",
    ),
)


def _client_as(monkeypatch: pytest.MonkeyPatch, user: dict | None) -> TestClient:
    def guard(request):
        if user is not None:
            request.state.auth_user = dict(user)
        return None

    monkeypatch.setattr(api, "auth_guard_response", guard)
    return TestClient(api.app)


@pytest.mark.parametrize("admin_user", [ADMIN_USER, ACCESS_LEVEL_ADMIN_USER])
def test_admin_can_load_agentic_review_html(monkeypatch, admin_user) -> None:
    response = _client_as(monkeypatch, admin_user).get(
        "/profile/pipeline-runs/run-61b/agentic-review"
    )

    assert response.status_code == 200
    assert '<div class="page agentic-review-page" data-agentic-review-run-id="run-61b">' in response.text


def test_authenticated_non_admin_cannot_load_agentic_review_html(monkeypatch) -> None:
    response = _client_as(monkeypatch, NON_ADMIN_USER).get(
        "/profile/pipeline-runs/run-61b/agentic-review"
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required."}


@pytest.mark.parametrize(("path", "service_name", "run_key"), DEDICATED_APIS)
def test_admin_api_preserves_authenticated_owner_scope(
    monkeypatch,
    path: str,
    service_name: str,
    run_key: str,
) -> None:
    captured: dict = {}

    def readback(**kwargs):
        captured.update(kwargs)
        return {"ok": True, "owner_user_id": kwargs["owner_user_id"]}

    monkeypatch.setattr(services, service_name, readback)
    response = _client_as(monkeypatch, ADMIN_USER).get(
        f"{path}?owner_user_id=another-user"
    )

    assert response.status_code == 200
    assert response.json()["owner_user_id"] == ADMIN_USER["user_id"]
    assert captured["owner_user_id"] == ADMIN_USER["user_id"]
    assert captured[run_key] == "run-61b"
    assert "another-user" not in captured.values()


@pytest.mark.parametrize(("path", "service_name", "run_key"), DEDICATED_APIS)
def test_non_admin_api_is_forbidden_before_service_invocation(
    monkeypatch,
    path: str,
    service_name: str,
    run_key: str,
) -> None:
    called = False

    def forbidden_readback(**_kwargs):
        nonlocal called
        called = True
        raise AssertionError("Non-admin request must not reach the service.")

    monkeypatch.setattr(services, service_name, forbidden_readback)
    response = _client_as(monkeypatch, NON_ADMIN_USER).get(path)

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required."}
    assert called is False


@pytest.mark.parametrize("path", [item[0] for item in DEDICATED_APIS])
def test_unauthenticated_dedicated_api_keeps_existing_401(monkeypatch, path: str) -> None:
    monkeypatch.setenv("JOB_STACK_AUTH_ENABLED", "true")

    response = TestClient(api.app).get(path)

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated."}


def test_profile_action_visibility_uses_existing_current_user_admin_state() -> None:
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the focused Profile action visibility test.")

    script = f"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync({json.dumps(str(PROFILE_JS_PATH))}, "utf8");
const elements = {{
  pipelineRunsTableBody: {{ innerHTML: "" }},
  pipelineRunsMeta: {{ textContent: "" }},
}};
const document = {{
  getElementById(id) {{ return elements[id] || null; }},
  querySelector() {{ return null; }},
  querySelectorAll() {{ return []; }},
  addEventListener() {{}},
}};
const window = {{ addEventListener() {{}}, location: {{ search: "" }} }};
const context = {{
  console, document, window, URLSearchParams, Date, Intl, Object, Array, String,
  Boolean, Number, Math, JSON, Error, encodeURIComponent,
}};
vm.createContext(context);
vm.runInContext(source, context);
const renderFor = (user) => {{
  vm.runInContext(`profileState.currentUser = ${{JSON.stringify(user)}}`, context);
  vm.runInContext(`renderPipelineRuns([{{ run_id: "run-61b", status: "succeeded" }}])`, context);
  return elements.pipelineRunsTableBody.innerHTML;
}};
const byFlag = renderFor({json.dumps(ADMIN_USER)});
const byAccess = renderFor({json.dumps(ACCESS_LEVEL_ADMIN_USER)});
const nonAdmin = renderFor({json.dumps(NON_ADMIN_USER)});
console.log(JSON.stringify({{
  flagHasAgentic: byFlag.includes("pipeline-run-agentic-review-btn"),
  accessHasAgentic: byAccess.includes("pipeline-run-agentic-review-btn"),
  nonAdminHasAgentic: nonAdmin.includes("pipeline-run-agentic-review-btn"),
  nonAdminHasView: nonAdmin.includes("pipeline-run-view-btn"),
  nonAdminHasRerun: nonAdmin.includes("pipeline-run-rerun-btn"),
}}));
"""
    completed = subprocess.run(
        [node, "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == {
        "flagHasAgentic": True,
        "accessHasAgentic": True,
        "nonAdminHasAgentic": False,
        "nonAdminHasView": True,
        "nonAdminHasRerun": True,
    }
    assert PROFILE_JS_PATH.read_text(encoding="utf-8").count('fetchJson("/auth/me")') == 1
