from copy import deepcopy

import pytest

from src.evaluation import controlled_groq_canary_run_005_identity as owner


PLAN_SHA = "57c46f89f3d53ab3e8a82f73a7fffdd9e5157db5459521f06950f74d679f5e62"
IDENTITY_SHA = "3c365a5cf931a3d6b2d855db27ab7762e5454c89085a32a203a244ec55e11ea1"
AUTH_SHA = "00080272f28d202c38de019d4478941a2b7ac8a37c7beebd7d1df72b60b42882"
SCHEDULE_KEY = (
    "canary_run_005_"
    "a8a5414230a2a0da4a3bfb532df06b0dc4b17eb062076909a77c855d26bdae7c"
)


def test_identity_and_artifact_namespace_are_exact():
    identity = owner.build_run_005_identity_contract()

    assert identity["run_identifier"] == "phase11-groq-canary-005"
    assert identity["run_005_plan_sha256"] == PLAN_SHA
    assert identity["target_case_aliases"] == ["case_ece85e9411ca52b579359fb8"]
    assert identity["target_workloads"] == ["tailoring_generation"]
    assert len(identity["schedule"]) == 1
    assert owner.RUN_005_ARTIFACT_PATHS == {
        kind: f"outputs/provider_benchmark/phase11_groq_canary_{kind}_005.json"
        for kind in ("pricing", "authorization", "checkpoint", "result")
    }


def test_all_prior_run_namespaces_are_protected():
    protected = owner.build_run_005_identity_contract()[
        "protected_prior_artifacts"
    ]

    assert set(protected) == {"run_001", "run_002", "run_003", "run_004"}
    for row in protected.values():
        assert row["resume_allowed"] is False
        assert row["key_replay_allowed"] is False
        assert row["writes_allowed"] is False
        assert row["checkpoint_as_run_005_initial_state_allowed"] is False
        assert row["result_as_run_005_initial_state_allowed"] is False


def test_inactive_authorization_is_one_case_120b_only_and_default_off():
    template = owner.build_run_005_authorization_template()

    assert template["candidate_provider_models"] == [
        {"provider": "groq", "model": "openai/gpt-oss-120b"}
    ]
    assert template["approved_schedule_keys"] == [SCHEDULE_KEY]
    assert template["approved_case_aliases"] == [
        "case_ece85e9411ca52b579359fb8"
    ]
    assert template["approved_workloads"] == ["tailoring_generation"]
    assert template["operator_approved"] is False
    assert template["live_execution_authorized"] is False
    assert template["fallback_allowed"] is False
    assert template["retry_count"] == 0
    for field in (
        "gemini_allowed",
        "openai_provider_allowed",
        "production_activation_allowed",
        "mutation_authority_allowed",
        "application_authority_allowed",
        "ats_authority_allowed",
        "run_001_resume_allowed",
        "run_001_key_replay_allowed",
        "run_002_resume_allowed",
        "run_002_key_replay_allowed",
        "run_003_resume_allowed",
        "run_003_key_replay_allowed",
        "run_004_resume_allowed",
        "run_004_key_replay_allowed",
    ):
        assert template[field] is False


def test_identity_and_authorization_digests_are_stable_and_defensive():
    identity = owner.build_run_005_identity_contract()
    template = owner.build_run_005_authorization_template()
    identity_before = deepcopy(identity)
    template_before = deepcopy(template)

    assert owner.run_005_identity_sha256(identity) == IDENTITY_SHA
    assert owner.run_005_authorization_template_sha256(template) == AUTH_SHA
    assert identity == identity_before
    assert template == template_before

    identity["authority_invariants"]["provider_calls_allowed"] = True
    template["live_execution_authorized"] = True
    with pytest.raises(ValueError):
        owner.validate_run_005_identity_contract(identity)
    with pytest.raises(ValueError):
        owner.validate_run_005_authorization_template(template)
