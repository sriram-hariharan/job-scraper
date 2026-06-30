# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only e658b1e05444d7cd2546d3d065cc325045a9d2bb1589b900c18d1aeea0fbd084
# phase23f legacy guard marker: changes_only e658b1e05444d7cd2546d3d065cc325045a9d2bb1589b900c18d1aeea0fbd084 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents.provider_live_activation_safety_plan import (
    build_provider_live_activation_safety_plan,
)


ROOT = Path(__file__).resolve().parents[1]


def test_live_activation_safety_plan_is_default_off_and_non_executing():
    plan = build_provider_live_activation_safety_plan()

    assert plan["live_activation_safety_plan_enabled"] is False
    assert plan["plan_status"] == (
        "live_activation_plan_skipped_default_off"
    )
    assert plan["default_off"] is True
    assert plan["planning_only"] is True
    assert plan["live_provider_execution_enabled"] is False
    assert plan["go_decision_authorized"] is False
    assert plan["next_safe_step"] == (
        "enable_live_activation_safety_plan_review_only"
    )
    assert plan["safety_metadata"]["provider_calls_made"] is False
    assert plan["safety_metadata"]["network_calls_made"] is False


def test_plan_selects_jd_only_and_blocks_tailoring_and_critic():
    plan = build_provider_live_activation_safety_plan(enabled=True)

    assert plan["plan_status"] == "live_activation_plan_ready_for_review"
    assert plan["first_real_canary_agent"] == "jd_intelligence"
    assert plan["first_real_canary_mode"] == "shadow_only"
    assert plan["blocked_real_execution_agent_names"] == [
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert plan["canary_constraints"]["single_agent_only"] is True
    assert plan["canary_constraints"]["single_agent_name"] == (
        "jd_intelligence"
    )


def test_plan_requires_explicit_gates_allowlists_and_injection():
    plan = build_provider_live_activation_safety_plan(enabled=True)

    assert plan["explicit_enable_flag_required"] is True
    assert plan["explicit_configuration_required"] is True
    assert plan["provider_name_allowlist_required"] is True
    assert plan["model_name_allowlist_required"] is True
    assert plan["provider_allowlist_default"] == []
    assert plan["model_allowlist_default"] == []
    assert plan["injected_provider_adapter_required"] is True
    assert plan["injected_provider_client_required"] is True
    assert plan["provider_client_constructed_internally"] is False
    assert plan["environment_secrets_read_by_plan"] is False
    assert plan["shadow_only_required"] is True


def test_plan_requires_bounded_timeout_retry_token_and_cost_limits():
    limits = build_provider_live_activation_safety_plan(
        enabled=True
    )["execution_limits"]

    for key in (
        "strict_timeout_required",
        "timeout_must_be_explicit",
        "retry_limit_required",
        "retry_limit_must_be_explicit",
        "token_budget_required",
        "token_budget_must_be_explicit",
        "cost_budget_required",
        "cost_budget_must_be_explicit",
    ):
        assert limits[key] is True
    assert limits["unbounded_retries_allowed"] is False
    assert limits["unbounded_tokens_allowed"] is False
    assert limits["unbounded_cost_allowed"] is False


def test_plan_requires_validation_fallback_llmops_and_error_classes():
    plan = build_provider_live_activation_safety_plan(enabled=True)
    validation = plan["validation_and_fallback"]
    observability = plan["observability_requirements"]

    assert validation[
        "structured_output_schema_validation_required"
    ] is True
    assert validation["deterministic_fallback_required"] is True
    assert validation["invalid_output_must_fallback"] is True
    assert validation["provider_exception_must_fallback"] is True
    assert validation["timeout_must_fallback"] is True
    for key in (
        "llmops_metadata_required",
        "prompt_version_required",
        "agent_version_required",
        "provider_name_required",
        "model_name_required",
        "latency_required",
        "token_usage_required",
        "estimated_cost_required",
        "retry_count_required",
        "fallback_status_required",
        "schema_validation_status_required",
        "provider_error_classification_required",
    ):
        assert observability[key] is True
    assert "timeout_error" in plan["provider_error_classifications"]
    assert "schema_validation_error" in (
        plan["provider_error_classifications"]
    )
    assert "budget_limit_error" in plan["provider_error_classifications"]


def test_plan_requires_rollback_smoke_tests_and_existing_readbacks():
    plan = build_provider_live_activation_safety_plan(enabled=True)
    rollback = plan["rollback"]
    smoke = plan["pre_live_smoke_test_plan"]
    readback = plan["audit_readback_expectations"]

    assert rollback["off_switch_required"] is True
    assert rollback["primary_off_switch"] == (
        "jd_live_canary_enabled_false"
    )
    assert rollback["normal_behavior_unchanged_when_off"] is True
    assert smoke["injected_fake_client_only"] is True
    assert smoke["live_network_allowed"] is False
    assert smoke["assert_allowlist_enforcement"] is True
    assert smoke["assert_structured_output_validation"] is True
    assert smoke["assert_llmops_metadata"] is True
    assert smoke["assert_deterministic_fallback"] is True
    assert smoke["assert_zero_mutation_authority"] is True
    assert readback["existing_service_readback_required"] is True
    assert readback["existing_api_readback_required"] is True
    assert readback["existing_ui_readback_required"] is True
    assert readback["ui_remains_manual_only"] is True
    assert readback["audit_payload_must_not_trigger_execution"] is True


def test_phase13b_go_no_go_checks_and_next_step_are_explicit():
    plan = build_provider_live_activation_safety_plan(enabled=True)
    checks = set(plan["phase_13b_go_no_go_checks"])

    assert {
        "jd_only_canary_scope_confirmed",
        "shadow_only_mode_confirmed",
        "provider_and_model_allowlists_defined",
        "timeout_and_retry_limits_defined",
        "token_and_cost_budgets_defined",
        "structured_output_validation_confirmed",
        "deterministic_fallback_confirmed",
        "llmops_and_prompt_version_metadata_confirmed",
        "rollback_switches_confirmed",
        "readback_audit_visibility_confirmed",
        "zero_mutation_authority_confirmed",
    }.issubset(checks)
    assert plan["go_decision_authorized"] is False
    assert plan["next_safe_step"] == (
        "review_phase_13b_jd_canary_scaffold_requirements"
    )


def test_plan_preserves_zero_mutation_authority():
    plan = build_provider_live_activation_safety_plan(enabled=True)
    influence = plan["no_influence_requirements"]
    safety = plan["safety_metadata"]

    assert plan["mutation_authorized"] is False
    assert plan["mutation_authorized_agent_count"] == 0
    for key in (
        "final_scoring_influence_allowed",
        "ranking_influence_allowed",
        "queue_influence_allowed",
        "approval_influence_allowed",
        "resume_mutation_allowed",
        "cover_letter_mutation_allowed",
        "execution_allowed",
        "submission_allowed",
    ):
        assert influence[key] is False
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
        "did_mutate_approval",
        "did_mutate_resume",
        "did_write_resume_draft",
        "did_write_cover_letter_draft",
        "did_create_execution_request",
        "did_create_execution_launch_request",
        "did_execute_application",
        "did_submit_application",
        "api_route_added",
        "ui_action_added",
        "service_behavior_added",
        "pipeline_stage_added",
        "mutation_authorized",
    ):
        assert safety[key] is False


def test_plan_does_not_mutate_context_or_read_secrets():
    context = {
        "review_owner": "operator",
        "notes": ["planning only"],
    }
    before = deepcopy(context)

    plan = build_provider_live_activation_safety_plan(
        enabled=True,
        planning_context=context,
    )

    assert context == before
    assert plan["planning_context"] == before
    assert plan["planning_context"] is not context
    assert plan["environment_secrets_read_by_plan"] is False


def test_plan_module_has_no_sdk_network_storage_or_runtime_wiring():
    source = (
        ROOT / "src/agents/provider_live_activation_safety_plan.py"
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
        "run_jd_provider_runtime_activation(",
        "provider_callable(",
        "provider_client.invoke(",
        "create_embedding(",
        "database_url",
        "connect(",
        "cursor.execute",
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
        assert marker not in source


def test_protected_runtime_dependencies_and_surfaces_are_unchanged():
    expected = {
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/app/api.py": ("e658b1e05444d7cd2546d3d065cc325045a9d2bb1589b900c18d1aeea0fbd084"),
        "src/app/services.py": ("c27f0c1a499398d423f8edd46165da784dabfea0309f2022ed88f9fc75d8df8f"),
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
