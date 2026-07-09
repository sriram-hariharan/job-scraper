# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96
# phase23f legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents.jd_live_provider_canary_runbook import (
    build_jd_live_provider_canary_runbook,
)


ROOT = Path(__file__).resolve().parents[1]


def test_runbook_is_default_off_and_does_not_authorize_execution():
    runbook = build_jd_live_provider_canary_runbook()

    assert runbook["runbook_enabled"] is False
    assert runbook["runbook_status"] == (
        "jd_live_canary_runbook_skipped_default_off"
    )
    assert runbook["default_off"] is True
    assert runbook["execution_authorized"] is False
    assert runbook["manual_execution_only"] is True


def test_runbook_is_jd_only_one_job_shadow_only_and_external():
    runbook = build_jd_live_provider_canary_runbook(enabled=True)

    assert runbook["allowed_agent_name"] == "jd_intelligence"
    assert runbook["blocked_agent_names"] == [
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert runbook["one_job_only"] is True
    assert runbook["shadow_only_required"] is True
    assert runbook["external_adapter_required"] is True
    assert runbook["config_gate_allow_required"] is True
    shape = runbook["allowed_execution_shape"]
    assert shape["job_payload_count"] == 1
    assert shape["batch_allowed"] is False
    assert shape["automatic_execution_allowed"] is False


def test_runbook_defines_config_and_external_adapter_contracts():
    runbook = build_jd_live_provider_canary_runbook(enabled=True)
    required = runbook["required_config_fields"]
    values = runbook["required_config_values"]
    adapter_input = runbook["external_adapter_input_contract"]
    adapter_output = runbook["external_adapter_output_contract"]

    for field in (
        "live_canary_enabled",
        "agent_name",
        "shadow_only",
        "provider_name",
        "model_name",
        "timeout_seconds",
        "retry_limit",
        "max_input_tokens",
        "max_output_tokens",
        "max_estimated_cost",
        "prompt_version",
        "runtime_version",
    ):
        assert field in required
    assert values["agent_name"] == "jd_intelligence"
    assert values["shadow_only"] is True
    assert values["mutation_authorized"] is False
    assert adapter_input["job_payload_count"] == 1
    assert adapter_input["shadow_only"] is True
    assert adapter_output["required_fields"] == ["output"]
    assert adapter_output["structured_output_validation_required"] is True


def test_runbook_blocks_other_agents_mutation_and_decision_influence():
    runbook = build_jd_live_provider_canary_runbook(enabled=True)
    blocked = runbook["blocked_conditions"]

    for condition in (
        "tailoring_or_critic_selected",
        "multiple_jobs_supplied",
        "external_adapter_missing",
        "mutation_authority_requested",
        "decision_or_application_influence_requested",
        "adapter_exception",
        "adapter_output_invalid",
    ):
        assert condition in blocked
    assert runbook["mutation_authorized"] is False
    assert runbook["mutation_authorized_agent_count"] == 0
    assert runbook["scoring_influence_disabled"] is True
    assert runbook["ranking_influence_disabled"] is True
    assert runbook["queue_influence_disabled"] is True
    assert runbook["resume_mutation_disabled"] is True
    assert runbook["execution_submission_disabled"] is True


def test_runbook_includes_readback_llmops_rollback_and_proof_contract():
    runbook = build_jd_live_provider_canary_runbook(enabled=True)
    fields = runbook["required_readback_and_llmops_fields"]
    rollback = runbook["rollback_and_off_switch"]
    proof = runbook["proof_required_before_broader_rollout"]

    for field in (
        "provider_call_attempted",
        "provider_call_succeeded",
        "fallback_used",
        "schema_validation_status",
        "latency_ms",
        "total_tokens",
        "estimated_cost",
    ):
        assert field in fields
    assert rollback["stop_on_any_adapter_error"] is True
    assert rollback["stop_on_schema_validation_failure"] is True
    assert rollback["disable_manual_command"] is True
    assert rollback["disable_live_canary_config"] is True
    assert rollback["remove_external_adapter_injection"] is True
    assert rollback["broader_rollout_authorized"] is False
    assert "llmops_and_readback_verified" in proof
    assert "zero_mutation_authority_verified" in proof


def test_runbook_keeps_provider_implementation_outside_repository():
    runbook = build_jd_live_provider_canary_runbook(enabled=True)
    boundary = runbook["repository_boundary"]

    assert boundary["owns_provider_sdk_implementation"] is False
    assert boundary["owns_provider_credentials"] is False
    assert boundary["owns_direct_provider_network_implementation"] is False
    assert boundary["constructs_provider_clients"] is False
    assert boundary["external_callable_is_operator_supplied"] is True
    assert boundary["validates_request_and_response_contracts_only"] is True


def test_runbook_does_not_mutate_operator_context():
    context = {"ticket": "manual-review-only"}
    before = deepcopy(context)

    runbook = build_jd_live_provider_canary_runbook(
        enabled=True,
        operator_context=context,
    )

    assert context == before
    assert runbook["operator_context"] == before


def test_runbook_has_no_sdk_env_direct_network_or_execution_wiring():
    source = (
        ROOT / "src/agents/jd_live_provider_canary_runbook.py"
    ).read_text(encoding="utf-8").lower()
    for marker in (
        "from openai",
        "import openai",
        "anthropic",
        "langchain",
        "sentence_transformers",
        "requests.",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "os.getenv",
        "os.environ",
        "api_key",
        "provider_client(",
        "provider_client.invoke(",
        "database_url",
        "connect(",
        "cursor.execute(",
        ".commit(",
        "open(",
        "write_text(",
        "write_bytes(",
        "run_jd_live_provider_canary(",
        "run_manual_jd_live_provider_canary_command(",
        "invoke_jd_live_provider_external_adapter(",
    ):
        assert marker not in source


def test_safety_metadata_is_non_mutating():
    safety = build_jd_live_provider_canary_runbook(
        enabled=True
    )["safety_metadata"]

    assert safety["provider_calls_made"] is False
    assert safety["provider_sdk_imported"] is False
    assert safety["provider_client_constructed"] is False
    assert safety["environment_secrets_read"] is False
    assert safety["direct_provider_network_implemented"] is False
    for field in (
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
        assert safety[field] is False


def test_api_ui_service_pipeline_and_dependencies_are_unchanged():
    expected = {
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/app/api.py": ("85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96"),
        "src/app/services.py": ("e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c"),
        "src/app/static/agentic_review.js": ("1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b"),
        "src/pipeline/collector.py": ("29b74e6807b7942b0f35c67b1ed724262a9a8ce1488b7df669faf456a5cfea3f"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "application_execution_queue.py": ("c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"),
    }
    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
