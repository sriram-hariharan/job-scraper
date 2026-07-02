# phase56b legacy guard marker: changes_only 392145687e82bbcddc58ced1d3510aa0fa1342042e17e802e7aeac2a2631c04f 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 392145687e82bbcddc58ced1d3510aa0fa1342042e17e802e7aeac2a2631c04f
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96
# phase23f legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
from hashlib import sha256
from pathlib import Path

from src.agents.jd_live_provider_canary import (
    run_jd_live_provider_canary,
)
from src.agents.jd_live_provider_canary_readback import (
    build_jd_live_provider_canary_readback,
)
from src.agents.provider_live_activation_safety_plan import (
    build_provider_live_activation_safety_plan,
)
from src.agents.provider_live_config_gate import (
    evaluate_provider_live_config_gate,
)


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/jd-live-provider-canary-readback"
PHASE13_TESTS = (
    "tests/test_provider_live_activation_safety_plan_default_off.py",
    "tests/test_provider_live_config_gate_default_off.py",
    "tests/test_jd_live_provider_canary_default_off.py",
    "tests/test_jd_live_provider_canary_shadow_bridge_default_off.py",
    "tests/test_jd_live_provider_canary_readback_default_off.py",
    "tests/test_jd_live_provider_canary_service_readback_default_off.py",
    "tests/test_jd_live_provider_canary_api_readback_default_off.py",
    "tests/test_jd_live_provider_canary_ui_readback_default_off.py",
)


def _source(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _valid_config() -> dict:
    return {
        "live_canary_enabled": True,
        "agent_name": "jd_intelligence",
        "shadow_only": True,
        "provider_name": "approved-provider",
        "model_name": "approved-model",
        "allowed_provider_names": ["approved-provider"],
        "allowed_model_names": ["approved-model"],
        "timeout_seconds": 10,
        "retry_limit": 1,
        "max_input_tokens": 4_000,
        "max_output_tokens": 1_000,
        "max_estimated_cost": 0.25,
        "structured_output_validation_required": True,
        "deterministic_fallback_required": True,
        "llmops_metadata_required": True,
        "prompt_version": "jd-live-canary-prompt-v1",
        "runtime_version": "jd-live-canary-runtime-v1",
        "no_mutation_authority": True,
        "mutation_authorized": False,
        "final_scoring_influence_enabled": False,
        "ranking_influence_enabled": False,
        "queue_influence_enabled": False,
        "resume_mutation_enabled": False,
        "execution_enabled": False,
        "submission_enabled": False,
    }


def test_all_phase13_modules_surfaces_and_focused_tests_are_present():
    expected = (
        "src/agents/provider_live_activation_safety_plan.py",
        "src/agents/provider_live_config_gate.py",
        "src/agents/jd_live_provider_canary.py",
        "src/agents/jd_live_provider_canary_readback.py",
        "src/agents/shadow_sidecar_hook.py",
        "src/agents/pipeline_agent_review_packet.py",
        "src/app/services.py",
        "src/app/api.py",
        "src/app/static/agentic_review.js",
        *PHASE13_TESTS,
    )

    for relative_path in expected:
        assert (ROOT / relative_path).is_file(), relative_path


def test_safety_plan_selects_jd_only_and_blocks_other_live_agents():
    plan = build_provider_live_activation_safety_plan(enabled=True)

    assert plan["first_real_canary_agent"] == "jd_intelligence"
    assert plan["first_real_canary_mode"] == "shadow_only"
    assert plan["blocked_real_execution_agent_names"] == [
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert plan["injected_provider_adapter_required"] is True
    assert plan["injected_provider_client_required"] is True
    assert plan["provider_client_constructed_internally"] is False
    assert plan["live_provider_execution_enabled"] is False
    assert plan["go_decision_authorized"] is False


def test_default_gate_and_canary_block_without_calling_injected_adapter():
    calls = []
    gate = evaluate_provider_live_config_gate()
    canary = run_jd_live_provider_canary(
        provider_adapter=lambda request: calls.append(request),
    )

    assert calls == []
    assert gate["gate_status"] == "live_config_gate_skipped_default_off"
    assert gate["canary_allowed"] is False
    assert gate["provider_calls_made"] is False
    assert canary["canary_status"] == (
        "jd_live_canary_skipped_default_off"
    )
    assert canary["canary_allowed"] is False
    assert canary["provider_call_attempted"] is False
    assert canary["fallback_used"] is True
    assert canary["shadow_only"] is True


def test_only_explicit_valid_jd_shadow_config_can_pass_gate():
    valid = evaluate_provider_live_config_gate(
        enabled=True,
        config=_valid_config(),
    )
    tailoring = _valid_config()
    tailoring["agent_name"] = "tailoring_suggestion"
    critic = _valid_config()
    critic["agent_name"] = "critic_guardrail"

    assert valid["gate_status"] == (
        "live_config_gate_allowed_for_future_canary"
    )
    assert valid["canary_allowed"] is True
    assert valid["provider_calls_allowed"] is True
    assert valid["provider_calls_made"] is False
    for blocked_config in (tailoring, critic):
        blocked = evaluate_provider_live_config_gate(
            enabled=True,
            config=blocked_config,
        )
        assert blocked["canary_allowed"] is False
        assert "agent_name_must_be_jd_intelligence" in (
            blocked["blocked_reasons"]
        )


def test_valid_gate_still_requires_an_injected_adapter():
    canary = run_jd_live_provider_canary(
        enabled=True,
        job_payload={"job_description": "Build Python systems."},
        live_config=_valid_config(),
    )

    assert canary["canary_allowed"] is True
    assert canary["canary_status"] == "jd_live_canary_blocked"
    assert canary["provider_call_attempted"] is False
    assert canary["fallback_used"] is True
    assert canary["fallback_reason"] == (
        "missing_injected_provider_adapter"
    )
    assert canary["mutation_authorized"] is False
    assert canary["mutation_authorized_agent_count"] == 0


def test_runner_has_deterministic_fallback_llmops_and_budget_guards():
    source = _source("src/agents/jd_live_provider_canary.py")

    assert "evaluate_provider_live_config_gate(" in source
    assert "if not callable(provider_adapter):" in source
    assert "build_live_jd_intelligence_dry_run_payload(" in source
    assert "def _fallback_output(" in source
    assert "def _llmops_metadata(" in source
    assert "def _limit_violation(" in source
    assert '"fallback_used": True' in source
    assert '"schema_validation_status": validation_status' in source
    assert '"did_mutate_scoring": False' in source
    assert '"did_change_ranking": False' in source
    assert '"did_mutate_queue": False' in source
    assert '"did_mutate_resume": False' in source
    assert '"did_execute_application": False' in source
    assert '"did_submit_application": False' in source


def test_shadow_bridge_is_explicit_jd_only_and_default_off():
    source = _source("src/agents/shadow_sidecar_hook.py")
    start = source.index("def run_shadow_sidecar_pipeline_hook(")
    snippet = source[start:]

    assert "jd_live_provider_canary_enabled: bool = False" in snippet
    assert "jd_live_provider_canary_config" in snippet
    assert "jd_live_provider_canary_adapter" in snippet
    assert "jd_live_provider_canary_helper" in snippet
    assert "if jd_live_provider_canary_enabled is True:" in snippet
    assert "run_jd_live_provider_canary" in snippet
    assert "tailoring_live_provider_canary" not in snippet
    assert "critic_live_provider_canary" not in snippet
    assert '"jd_live_provider_canary_succeeded"' in snippet
    assert '"did_mutate_scoring": False' in snippet
    assert '"did_change_ranking": False' in snippet
    assert '"did_mutate_queue": False' in snippet


def test_readback_review_packet_service_and_api_are_non_executing():
    readback = _source(
        "src/agents/jd_live_provider_canary_readback.py"
    )
    packet = _source("src/agents/pipeline_agent_review_packet.py")
    service = _source("src/app/services.py")
    api = _source("src/app/api.py")

    packet_start = packet.index(
        "def _jd_live_provider_canary_readback("
    )
    packet_end = packet.index("\ndef ", packet_start + 5)
    packet_helper = packet[packet_start:packet_end]
    service_start = service.index(
        "def jd_live_provider_canary_readback_service_payload("
    )
    service_end = service.index("\ndef ", service_start + 5)
    service_helper = service[service_start:service_end]
    api_start = api.index(f'@app.post("{ENDPOINT}")')
    api_end = api.index("\n\n@app.", api_start + 5)
    api_route = api[api_start:api_end]

    assert "def build_jd_live_provider_canary_readback(" in readback
    assert "build_jd_live_provider_canary_readback(" in packet_helper
    assert "build_jd_live_provider_canary_readback" in service_helper
    assert (
        "services.jd_live_provider_canary_readback_service_payload("
        in api_route
    )
    assert '"read_only": True' in service_helper
    assert '"read_only": True' in api_route
    for snippet in (readback, packet_helper, service_helper, api_route):
        assert "run_jd_live_provider_canary(" not in snippet
        assert "provider_adapter(" not in snippet


def test_ui_is_passive_readback_with_no_execution_control():
    source = _source("src/app/static/agentic_review.js")
    start = source.index(
        "function renderJdLiveProviderCanaryReadbackSection"
    )
    end = source.index(
        "function renderHumanReviewedInfluencePreviewSection",
        start,
    )
    section = source[start:end]

    assert "Default-off read-only" in section
    assert "reviewPacket.jd_live_provider_canary_readback" in section
    assert "No JD live canary metadata yet" in section
    assert 'renderWorkflowSummaryMetric("Canary attempted"' in section
    assert 'renderWorkflowSummaryMetric("Estimated cost"' in section
    assert 'renderWorkflowSummaryMetric("Scoring influence disabled"' in section
    assert 'renderWorkflowSummaryMetric("Submission influence disabled"' in section
    assert "fetchJson(" not in section
    assert "addEventListener(" not in section
    assert "data-jd-live" not in section
    assert ENDPOINT not in section


def test_default_readback_is_safe_and_mutation_authority_is_zero():
    readback = build_jd_live_provider_canary_readback()

    assert readback["readback_status"] == (
        "jd_live_canary_readback_skipped_default_off"
    )
    assert readback["provider_call_attempted"] is False
    assert readback["mutation_authorized"] is False
    assert readback["mutation_authorized_agent_count"] == 0
    assert all(readback["influence_disabled"].values())
    for key in (
        "provider_calls_made",
        "network_calls_made",
        "environment_secrets_read",
        "embeddings_created",
        "did_read_database",
        "did_write_database",
        "did_write_files",
        "did_mutate_scoring",
        "did_change_ranking",
        "did_mutate_queue",
        "did_create_approval",
        "did_mutate_resume",
        "did_create_execution_request",
        "did_execute_application",
        "did_submit_application",
    ):
        assert readback["safety_metadata"][key] is False


def test_phase13_has_no_sdk_env_direct_network_or_storage_wiring():
    sources = "\n".join(
        _source(path)
        for path in (
            "src/agents/provider_live_activation_safety_plan.py",
            "src/agents/provider_live_config_gate.py",
            "src/agents/jd_live_provider_canary.py",
            "src/agents/jd_live_provider_canary_readback.py",
        )
    ).lower()
    for marker in (
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
        "provider_client(",
        "provider_client.invoke(",
        "create_embedding(",
        "database_url",
        "connect(",
        "cursor.execute(",
        ".commit(",
        "open(",
        "write_text(",
        "write_bytes(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in sources


def test_protected_surfaces_dependencies_and_pipeline_are_unchanged():
    expected = {
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/app/api.py": ("85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96"),
        "src/app/services.py": ("392145687e82bbcddc58ced1d3510aa0fa1342042e17e802e7aeac2a2631c04f"),
        "src/app/static/agentic_review.js": ("1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b"),
        "src/pipeline/collector.py": ("73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "application_execution_queue.py": ("c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"),
    }

    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
