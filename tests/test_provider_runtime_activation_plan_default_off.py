from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents.provider_runtime_activation_plan import (
    build_provider_runtime_activation_plan,
)


ROOT = Path(__file__).resolve().parents[1]


def test_activation_plan_is_default_off_and_non_executing():
    payload = build_provider_runtime_activation_plan()

    assert payload["activation_plan_enabled"] is False
    assert payload["activation_status"] == (
        "activation_plan_skipped_default_off"
    )
    assert payload["default_off"] is True
    assert payload["live_provider_execution_enabled"] is False
    assert payload["next_safe_step"] == (
        "enable_activation_plan_review_only"
    )
    assert payload["safety_metadata"]["provider_calls_made"] is False
    assert payload["safety_metadata"]["network_calls_made"] is False


def test_first_recommended_path_is_jd_intelligence_shadow_only():
    payload = build_provider_runtime_activation_plan(enabled=True)

    assert payload["activation_status"] == (
        "activation_plan_ready_for_review"
    )
    assert payload["first_activation_agent"] == "jd_intelligence"
    assert payload["first_activation_mode"] == "shadow_only"
    assert "read_only_job_description_analysis" in payload[
        "first_activation_reason"
    ]
    assert payload["shadow_only_required"] is True
    assert payload["live_provider_execution_enabled"] is False


def test_tailoring_and_critic_are_deferred_from_first_activation():
    payload = build_provider_runtime_activation_plan(enabled=True)

    assert payload["deferred_agent_names"] == [
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert payload["first_activation_agent"] not in payload[
        "deferred_agent_names"
    ]
    assert set(payload["deferred_agent_reasons"]) == {
        "tailoring_suggestion",
        "critic_guardrail",
    }


def test_activation_requires_explicit_configuration_and_injection():
    payload = build_provider_runtime_activation_plan(enabled=True)

    assert payload["explicit_configuration_required"] is True
    assert payload["injected_provider_adapter_required"] is True
    assert payload["injected_provider_client_required"] is True
    assert payload["provider_client_constructed_internally"] is False
    assert payload["smoke_test_plan"]["automated_test_client"] == (
        "injected_fake_client_only"
    )
    assert payload["smoke_test_plan"]["live_network_allowed"] is False


def test_validation_fallback_llmops_and_state_logging_are_required():
    payload = build_provider_runtime_activation_plan(enabled=True)

    assert payload["structured_output_validation_required"] is True
    assert payload["deterministic_fallback_required"] is True
    assert payload["llmops_metadata_required"] is True
    assert set(payload["provider_state_logging_required"]) == {
        "attempted",
        "succeeded",
        "failed",
        "fallback",
    }
    for field in (
        "provider_call_attempted",
        "provider_call_succeeded",
        "provider_call_blocked",
        "fallback_used",
        "schema_validation_status",
        "latency_ms",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "estimated_cost",
        "error_type",
    ):
        assert field in payload["required_llmops_fields"]


def test_rollback_and_fake_client_smoke_plan_are_explicit():
    payload = build_provider_runtime_activation_plan(enabled=True)
    rollback = payload["rollback"]
    smoke = payload["smoke_test_plan"]

    assert rollback["off_switch_required"] is True
    assert rollback["off_switch"] == (
        "provider_runtime_adapter_enabled_false"
    )
    assert rollback["fallback_behavior"] == (
        "deterministic_existing_shadow_output"
    )
    assert rollback["normal_behavior_unchanged_when_off"] is True
    assert smoke["assert_structured_output_validation"] is True
    assert smoke["assert_llmops_metadata"] is True
    assert smoke["assert_deterministic_fallback"] is True
    assert smoke["assert_zero_mutation_authority"] is True


def test_plan_does_not_mutate_planning_context():
    context = {
        "requested_by": "operator",
        "notes": ["review only"],
    }
    before = deepcopy(context)

    payload = build_provider_runtime_activation_plan(
        enabled=True,
        planning_context=context,
    )

    assert context == before
    assert payload["planning_context"] == before
    assert payload["planning_context"] is not context


def test_plan_preserves_zero_mutation_authority():
    payload = build_provider_runtime_activation_plan(enabled=True)
    safety = payload["safety_metadata"]

    assert payload["mutation_authorized"] is False
    assert payload["mutation_authorized_agent_count"] == 0
    for key in (
        "provider_calls_made",
        "network_calls_made",
        "embeddings_created",
        "did_read_database",
        "did_write_database",
        "did_mutate_scoring",
        "did_change_ranking",
        "did_mutate_queue",
        "did_create_approval",
        "did_mutate_approval",
        "did_mutate_resume",
        "did_write_resume_draft",
        "did_write_cover_letter_draft",
        "did_create_execution_request",
        "did_create_execution_launch_request",
        "did_execute_application",
        "did_submit_application",
        "pipeline_stage_added",
        "mutation_authorized",
    ):
        assert safety[key] is False


def test_plan_module_has_no_sdk_network_or_runtime_execution_wiring():
    source = (
        ROOT / "src/agents/provider_runtime_activation_plan.py"
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
        "os.getenv",
        "os.environ",
        "run_provider_runtime_adapter(",
        "provider_callable(",
        "provider_client.invoke(",
        "create_embedding(",
        "database_url",
        "connect(",
        "cursor.execute",
        ".commit(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in source


def test_pipeline_dependencies_and_application_authority_are_unchanged():
    expected = {
        "requirements.txt": (
            "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"
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
