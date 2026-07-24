# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405 d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents.provider_runtime_adapter import run_provider_runtime_adapter
from src.agents.provider_runtime_readiness import (
    build_provider_runtime_readiness_payload,
)
from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/provider-runtime-readback"
SERVICE = "provider_runtime_readiness_service_payload"
ORDERED_AGENTS = [
    "jd_intelligence",
    "tailoring_suggestion",
    "critic_guardrail",
]


def _sources():
    paths = {
        "readiness": ROOT / "src/agents/provider_runtime_readiness.py",
        "adapter": ROOT / "src/agents/provider_runtime_adapter.py",
        "shadow_bridge": ROOT / "src/agents/shadow_sidecar_hook.py",
        "service": ROOT / "src/app/services.py",
        "api": ROOT / "src/app/api.py",
        "ui": ROOT / "src/app/static/agentic_review.js",
    }
    return {
        name: path.read_text(encoding="utf-8")
        for name, path in paths.items()
    }


def _complete_config():
    return {
        "provider_name": "injected-provider",
        "model_name": "shadow-model-v1",
        "configured_agent_names": list(ORDERED_AGENTS),
        "shadow_only": True,
        "mutation_authorized": False,
    }


def test_phase11_modules_and_boundaries_exist():
    sources = _sources()
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert "def build_provider_runtime_readiness_payload(" in sources[
        "readiness"
    ]
    assert "def run_provider_runtime_adapter(" in sources["adapter"]
    assert "provider_runtime_adapter_enabled: bool = False" in sources[
        "shadow_bridge"
    ]
    assert f"def {SERVICE}(" in sources["service"]
    assert f'@app.post("{ENDPOINT}")' in sources["api"]
    assert routes[ENDPOINT].methods == {"POST"}
    assert "function renderProviderRuntimeReadbackSection" in sources["ui"]
    assert "runtimeReadbackApiPath" in sources["ui"]


def test_phase11_contract_adapter_and_service_remain_default_off():
    calls = []
    request_payload = {"agent_name": "jd_intelligence"}
    request_before = deepcopy(request_payload)

    readiness = build_provider_runtime_readiness_payload()
    adapter = run_provider_runtime_adapter(
        request_payload=request_payload,
        provider_callable=lambda request: calls.append(request),
    )
    service = getattr(services, SERVICE)()

    assert readiness["readiness_status"] == "skipped_default_off"
    assert readiness["provider_runtime_readiness_enabled"] is False
    assert readiness["provider_calls_allowed"] is False
    assert readiness["next_safe_step"] == (
        "enable_provider_runtime_readiness_check"
    )
    assert adapter["status"] == (
        "provider_runtime_adapter_skipped_default_off"
    )
    assert adapter["provider_call_attempted"] is False
    assert adapter["provider_call_succeeded"] is False
    assert calls == []
    assert request_payload == request_before
    assert service["readiness_status"] == "skipped_default_off"
    assert service["default_off"] is True
    assert service["provider_calls_allowed"] is False


def test_phase11_ready_metadata_requires_explicit_shadow_configuration():
    config = _complete_config()
    before = deepcopy(config)
    readiness = build_provider_runtime_readiness_payload(
        enabled=True,
        config=config,
    )

    assert readiness["readiness_status"] == (
        "ready_shadow_provider_runtime"
    )
    assert readiness["provider_runtime_configured"] is True
    assert readiness["configured_agent_names"] == ORDERED_AGENTS
    assert readiness["provider_calls_allowed"] is False
    assert readiness["shadow_only"] is True
    assert readiness["mutation_authorized"] is False
    assert readiness["mutation_authorized_agent_count"] == 0
    assert readiness["next_safe_step"]
    assert config == before


def test_shadow_adapter_bridge_requires_explicit_enablement_and_injection():
    source = _sources()["shadow_bridge"]
    start = source.index("def run_shadow_sidecar_pipeline_hook(")
    snippet = source[start:]

    assert "provider_runtime_adapter_enabled: bool = False" in snippet
    assert "provider_runtime_adapter_client: Any = None" in snippet
    assert "provider_runtime_adapter_helper: Any = None" in snippet
    assert "if provider_runtime_adapter_enabled is True:" in snippet
    assert "provider_runtime_adapter_attempted" in snippet
    assert "provider_runtime_adapter_succeeded" in snippet
    assert "provider_runtime_adapter_blocked" in snippet
    assert '"did_mutate_scoring": False' in snippet
    assert '"did_change_ranking": False' in snippet
    assert '"did_mutate_queue": False' in snippet


def test_service_and_api_readbacks_are_read_only_and_non_executing():
    sources = _sources()
    service_start = sources["service"].index(f"def {SERVICE}(")
    service_end = sources["service"].index(
        "\ndef vector_evidence_readback_service_helper_payload(",
        service_start,
    )
    service = sources["service"][service_start:service_end]
    api_start = sources["api"].index(f'@app.post("{ENDPOINT}")')
    api_end = sources["api"].index(
        '\n\n@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")',
        api_start,
    )
    api_route = sources["api"][api_start:api_end]

    assert "build_provider_runtime_readiness_payload" in service
    assert '"read_only": True' in service
    assert '"shadow_only": True' in service
    assert '"provider_calls_made": False' in service
    assert "services.provider_runtime_readiness_service_payload(" in api_route
    assert '"read_only": True' in api_route
    assert '"api_readback_only": True' in api_route
    assert '"provider_calls_made": False' in api_route
    assert "run_provider_runtime_adapter(" not in service
    assert "run_provider_runtime_adapter(" not in api_route


def test_ui_readback_is_manual_default_off_and_does_not_auto_refresh():
    source = _sources()["ui"]
    section_start = source.index(
        "function renderProviderRuntimeReadbackSection"
    )
    section_end = source.index(
        "function renderHumanReviewedInfluencePreviewSection",
        section_start,
    )
    section = source[section_start:section_end]
    handler_start = source.index(
        'event.target.closest("[data-runtime-readback]")'
    )
    handler_end = source.index(
        'event.target.closest("[data-manual-human-decision-capture-dry-run]")',
        handler_start,
    )
    handler = source[handler_start:handler_end]
    init_start = source.index("async function initAgenticReviewPage")
    init_end = source.index(
        'window.addEventListener("DOMContentLoaded", initAgenticReviewPage);',
        init_start,
    )
    init = source[init_start:init_end]

    assert "Default-off read-only" in section
    assert "Provider runtime not enabled" in section
    assert "data-runtime-readback-enable" in section
    assert "data-runtime-readback" in section
    assert "runtimeReadbackApiPath" in handler
    assert 'method: "POST"' in handler
    assert ENDPOINT not in handler
    assert ENDPOINT not in init
    assert "setInterval" not in handler
    assert "setInterval" not in init
    assert "provider" not in handler.lower()


def test_phase11_safety_metadata_keeps_mutation_authority_zero():
    readiness = build_provider_runtime_readiness_payload(
        enabled=True,
        config=_complete_config(),
    )
    service = getattr(services, SERVICE)(
        enabled=True,
        config=_complete_config(),
    )
    required = {
        "provider_calls_made": False,
        "embeddings_created": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_create_approval": False,
        "did_mutate_resume": False,
        "did_create_execution_request": False,
        "did_execute_application": False,
        "did_submit_application": False,
    }

    for key, value in required.items():
        assert readiness["safety_metadata"][key] is value
        assert service["safety_metadata"][key] is value
    assert readiness["mutation_authorized_agent_count"] == 0
    assert service["mutation_authorized_agent_count"] == 0


def test_phase11_has_no_sdk_network_embedding_storage_or_mutation_wiring():
    sources = _sources()
    readiness = sources["readiness"].lower()
    adapter = sources["adapter"].lower()
    service_start = sources["service"].index(f"def {SERVICE}(")
    service_end = sources["service"].index(
        "\ndef vector_evidence_readback_service_helper_payload(",
        service_start,
    )
    api_start = sources["api"].index(f'@app.post("{ENDPOINT}")')
    api_end = sources["api"].index(
        '\n\n@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")',
        api_start,
    )
    combined = "\n".join(
        (
            readiness,
            adapter,
            sources["service"][service_start:service_end].lower(),
            sources["api"][api_start:api_end].lower(),
        )
    )
    forbidden = (
        "from openai",
        "import openai",
        "anthropic",
        "langchain",
        "sentence_transformers",
        "requests.",
        "httpx",
        "urllib",
        "socket",
        "create_embedding(",
        "database_url",
        "connect(",
        "cursor.execute",
        ".commit(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "record_approval_decision(",
        "mutate_resume(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
    )
    for marker in forbidden:
        assert marker not in combined


def test_pipeline_decision_queue_and_dependencies_are_unchanged():
    expected = {
        "requirements.txt": (
            "75d10d919dd53cdc3e55056abe28503b5b0bde38d5e61d944beb794562886cc3"
        ),
        "src/pipeline/collector.py": (
            "75bda61d0bdc4cf388586d141541be486a9e01b5062f5cc91fe6dc63c46546dc"
        ),
        "src/pipeline/application_scorer.py": (
            "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"
        ),
        "src/pipeline/job_ranker.py": (
            "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"
        ),
        "application_execution_queue.py": (
            "28ac5d153eeb1d3e6238bed57418a45b603f72caea6c0f671a8dcbb3b0a76097"
        ),
    }
    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
