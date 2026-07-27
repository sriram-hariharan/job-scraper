from copy import deepcopy

import pytest

from src.evaluation import controlled_groq_canary_run_004_identity as owner


def test_identity_owns_exact_two_rows_and_fresh_namespace():
    identity = owner.build_run_004_identity_contract()
    assert identity["run_identifier"] == "phase11-groq-canary-004"
    assert len(identity["schedule"]) == 2
    assert identity["target_workloads"] == [
        "jd_intelligence", "tailoring_generation"
    ]
    assert identity["future_artifact_identities"] == {
        kind: f"outputs/provider_benchmark/phase11_groq_canary_{kind}_004.json"
        for kind in ("pricing", "authorization", "checkpoint", "result")
    }


def test_all_prior_runs_are_immutable_and_nonresumable():
    protected = owner.build_run_004_identity_contract()[
        "protected_prior_artifacts"
    ]
    assert set(protected) == {"run_001", "run_002", "run_003"}
    for row in protected.values():
        assert row["resume_allowed"] is False
        assert row["key_replay_allowed"] is False
        assert row["writes_allowed"] is False
        assert row["checkpoint_as_run_004_initial_state_allowed"] is False
        assert row["result_as_run_004_initial_state_allowed"] is False


def test_inactive_authorization_is_exactly_bounded_and_default_off():
    template = owner.build_run_004_authorization_template()
    identity = owner.build_run_004_identity_contract()
    assert template["approved_schedule_keys"] == [
        row["schedule_key"] for row in identity["schedule"]
    ]
    assert template["approved_workloads"] == [
        "jd_intelligence", "tailoring_generation"
    ]
    assert template["candidate_provider_models"] == [
        {"provider": "groq", "model": "openai/gpt-oss-120b"}
    ]
    assert template["operator_approved"] is False
    assert template["live_execution_authorized"] is False
    assert template["retry_count"] == 0
    assert template["fallback_allowed"] is False
    for key in (
        "gemini_allowed", "openai_provider_allowed",
        "production_activation_allowed", "mutation_authority_allowed",
        "application_authority_allowed", "ats_authority_allowed",
    ):
        assert template[key] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("approved_schedule_keys", []),
        ("approved_workloads", ["skill_extraction"]),
        ("openai_provider_allowed", True),
        ("production_activation_allowed", True),
    ],
)
def test_authorization_scope_drift_is_rejected(field, value):
    template = owner.build_run_004_authorization_template()
    template[field] = value
    with pytest.raises(ValueError):
        owner.validate_run_004_authorization_template(template)


def test_identity_and_template_digests_are_stable_and_inputs_immutable():
    identity = owner.build_run_004_identity_contract()
    template = owner.build_run_004_authorization_template()
    before = deepcopy((identity, template))
    assert owner.run_004_identity_sha256(identity) == owner.run_004_identity_sha256()
    assert owner.run_004_authorization_template_sha256(
        template
    ) == owner.run_004_authorization_template_sha256()
    assert (identity, template) == before
