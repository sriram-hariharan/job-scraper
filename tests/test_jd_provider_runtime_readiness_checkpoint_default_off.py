from hashlib import sha256
from pathlib import Path

from src.agents.jd_provider_runtime_activation import (
    run_jd_provider_runtime_activation,
)
from src.agents.jd_provider_runtime_trace_readback import (
    build_jd_provider_runtime_trace_readback,
)
from src.agents.provider_runtime_activation_plan import (
    build_provider_runtime_activation_plan,
)


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/jd-provider-runtime-readback"
PHASE12_TESTS = (
    "tests/test_provider_runtime_activation_plan_default_off.py",
    "tests/test_jd_provider_runtime_activation_default_off.py",
    "tests/test_jd_provider_runtime_shadow_bridge_default_off.py",
    "tests/test_jd_provider_runtime_trace_readback_default_off.py",
    "tests/test_jd_provider_runtime_review_packet_default_off.py",
    "tests/test_jd_provider_runtime_service_readback_default_off.py",
    "tests/test_jd_provider_runtime_api_readback_default_off.py",
    "tests/test_jd_provider_runtime_ui_readback_default_off.py",
)


def _source(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_all_phase12_jd_runtime_modules_and_focused_tests_are_present():
    expected = (
        "src/agents/provider_runtime_activation_plan.py",
        "src/agents/jd_provider_runtime_activation.py",
        "src/agents/shadow_sidecar_hook.py",
        "src/agents/jd_provider_runtime_trace_readback.py",
        "src/agents/pipeline_agent_review_packet.py",
        "src/app/services.py",
        "src/app/api.py",
        "src/app/static/agentic_review.js",
        *PHASE12_TESTS,
    )

    for relative_path in expected:
        assert (ROOT / relative_path).is_file(), relative_path


def test_activation_plan_selects_jd_first_and_defers_other_agents():
    plan = build_provider_runtime_activation_plan(enabled=True)

    assert plan["first_activation_agent"] == "jd_intelligence"
    assert plan["first_activation_mode"] == "shadow_only"
    assert plan["deferred_agent_names"] == [
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert plan["injected_provider_adapter_required"] is True
    assert plan["injected_provider_client_required"] is True
    assert plan["provider_client_constructed_internally"] is False
    assert plan["deterministic_fallback_required"] is True
    assert plan["structured_output_validation_required"] is True
    assert plan["llmops_metadata_required"] is True
    assert plan["next_safe_step"]


def test_jd_activation_and_readback_remain_default_off():
    calls = []
    activation = run_jd_provider_runtime_activation(
        provider_callable=lambda request: calls.append(request),
    )
    readback = build_jd_provider_runtime_trace_readback()

    assert calls == []
    assert activation["status"] == (
        "jd_provider_runtime_activation_skipped_default_off"
    )
    assert activation["llmops_trace_metadata"][
        "provider_call_attempted"
    ] is False
    assert activation["shadow_only"] is True
    assert activation["fallback_used"] is True
    assert readback["readback_status"] == (
        "jd_provider_runtime_readback_skipped_default_off"
    )
    assert readback["jd_provider_runtime_attempted"] is False
    assert readback["mutation_authorized"] is False
    assert readback["mutation_authorized_agent_count"] == 0
    assert readback["next_safe_step"]


def test_missing_client_blocks_safely_and_requires_explicit_injection():
    blocked = run_jd_provider_runtime_activation(
        enabled=True,
        job_payload={
            "title": "Analyst",
            "description": "Analyze job data.",
        },
    )

    assert blocked["status"] == "jd_provider_runtime_activation_blocked"
    assert blocked["llmops_trace_metadata"][
        "provider_call_attempted"
    ] is False
    assert blocked["llmops_trace_metadata"][
        "provider_call_succeeded"
    ] is False
    assert blocked["fallback_used"] is True
    assert blocked["shadow_only"] is True
    assert blocked["mutation_authorized"] is False


def test_shadow_bridge_is_jd_only_explicit_and_default_off():
    source = _source("src/agents/shadow_sidecar_hook.py")
    start = source.index("def run_shadow_sidecar_pipeline_hook(")
    snippet = source[start:]

    assert "jd_provider_runtime_activation_enabled: bool = False" in snippet
    assert "jd_provider_runtime_activation_client: Any = None" in snippet
    assert "jd_provider_runtime_activation_helper: Any = None" in snippet
    assert "if jd_provider_runtime_activation_enabled is True:" in snippet
    assert "run_jd_provider_runtime_activation" in snippet
    assert "tailoring_provider_runtime_activation_enabled" not in snippet
    assert "critic_provider_runtime_activation_enabled" not in snippet
    assert '"did_mutate_scoring": False' in snippet
    assert '"did_change_ranking": False' in snippet
    assert '"did_mutate_queue": False' in snippet


def test_trace_review_packet_service_and_api_are_readback_only():
    trace_source = _source(
        "src/agents/jd_provider_runtime_trace_readback.py"
    )
    packet_source = _source("src/agents/pipeline_agent_review_packet.py")
    service_source = _source("src/app/services.py")
    api_source = _source("src/app/api.py")

    packet_start = packet_source.index("def _jd_provider_runtime_readback(")
    packet_end = packet_source.index("\ndef ", packet_start + 5)
    packet_helper = packet_source[packet_start:packet_end]
    service_start = service_source.index(
        "def jd_provider_runtime_readback_service_payload("
    )
    service_end = service_source.index("\ndef ", service_start + 5)
    service_helper = service_source[service_start:service_end]
    api_start = api_source.index(f'@app.post("{ENDPOINT}")')
    api_end = api_source.index("\n\n@app.", api_start + 5)
    api_route = api_source[api_start:api_end]

    assert "def build_jd_provider_runtime_trace_readback(" in trace_source
    assert "build_jd_provider_runtime_trace_readback(" in packet_helper
    assert "build_jd_provider_runtime_trace_readback" in service_helper
    assert "services.jd_provider_runtime_readback_service_payload(" in api_route
    assert '"read_only": True' in service_helper
    assert '"read_only": True' in api_route
    for snippet in (trace_source, packet_helper, service_helper, api_route):
        assert "run_jd_provider_runtime_activation(" not in snippet
        assert "run_provider_runtime_adapter(" not in snippet


def test_ui_readback_is_manual_only_default_off_and_not_auto_refreshed():
    source = _source("src/app/static/agentic_review.js")
    section_start = source.index(
        "function renderJdProviderRuntimeReadbackSection"
    )
    section_end = source.index(
        "function renderHumanReviewedInfluencePreviewSection",
        section_start,
    )
    section = source[section_start:section_end]
    handler_start = source.index(
        'event.target.closest("[data-jd-runtime-readback]")'
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
    assert "data-jd-runtime-readback-enable" in section
    assert "data-jd-runtime-readback" in section
    assert "jdRuntimeReadbackApiPath" in handler
    assert 'method: "POST"' in handler
    assert ENDPOINT not in handler
    assert ENDPOINT not in init
    assert "setInterval" not in handler
    assert "setInterval" not in init
    assert "run_jd_provider_runtime_activation(" not in handler


def test_phase12_readiness_has_no_sdk_network_or_mutation_wiring():
    sources = "\n".join(
        _source(path)
        for path in (
            "src/agents/provider_runtime_activation_plan.py",
            "src/agents/jd_provider_runtime_activation.py",
            "src/agents/jd_provider_runtime_trace_readback.py",
        )
    ).lower()
    forbidden = (
        "from openai",
        "import openai",
        "from anthropic",
        "import anthropic",
        "langchain",
        "sentence_transformers",
        "requests.",
        "httpx",
        "urllib",
        "socket",
        "os.getenv",
        "os.environ",
        "create_embedding(",
        "cursor.execute(",
        ".commit(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    )

    for marker in forbidden:
        assert marker not in sources


def test_dependency_pipeline_and_application_authority_files_are_unchanged():
    expected = {
        "requirements.txt": (
            "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"
        ),
        "src/app/api.py": (
            "8ab44f7e97113f6d28e9a8f7d032affef2e1f8f891286986d9e95d581ff97fbf"
        ),
        "src/app/services.py": (
            "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee"
        ),
        "src/app/static/agentic_review.js": (
            "94e9f1c484f6459833141a37cddd7a0bb092fb185c7119b4909a5ed9d925ed6a"
        ),
        "src/pipeline/collector.py": (
            "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"
        ),
        "src/pipeline/application_scorer.py": (
            "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"
        ),
        "src/pipeline/job_ranker.py": (
            "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"
        ),
        "application_execution_queue.py": (
            "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"
        ),
    }

    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
