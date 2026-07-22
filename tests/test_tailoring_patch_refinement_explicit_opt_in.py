import json

from src.app import services
from src.tailoring import llm as tailoring_llm
from src.tailoring import rendering


def _candidate():
    return {
        "candidate_id": "replacement_1",
        "source_bullet_id": "bullet_1",
        "operation_type": "rewrite",
        "proposal_status": "patch_ready",
        "proposal_type": "patch_ready_rewrite",
        "patch_ready": True,
        "original_text": "Built reporting dashboards for weekly stakeholder reviews.",
        "current_evidence": "Built reporting dashboards for weekly stakeholder reviews.",
        "patch_text": "Built SQL reporting dashboards for weekly stakeholder reviews.",
        "proposed_text": "Built SQL reporting dashboards for weekly stakeholder reviews.",
        "patch_generation_method": "deterministic_using_phrase",
        "materiality_validation_status": "material_candidate",
        "supported_jd_signals": ["SQL"],
        "unsupported_risk_signals": [],
        "priority_score": 0.91,
        "rank": 2,
        "queue_position": 3,
        "operator_state": "pending",
        "application_status": "not_applied",
        "auto_apply_performed": False,
    }


def _install_candidate_pipeline(monkeypatch, calls):
    monkeypatch.setattr(
        rendering,
        "_diagnosis_to_replacement_candidate",
        lambda payload, diagnosis, index: _candidate(),
    )
    monkeypatch.setattr(
        rendering,
        "_merge_anchor_candidates_for_diagnosis",
        lambda diagnosis, candidates: [],
    )
    monkeypatch.setattr(
        rendering,
        "_suppress_anchor_candidates_for_diagnosis",
        lambda diagnosis, candidates: [],
    )

    def validate(payload, candidate, context):
        calls["materiality"] += 1
        return dict(candidate)

    original_export_gate = rendering._apply_post_refinement_export_gate

    def export(candidate):
        calls["export"] += 1
        return original_export_gate(candidate)

    monkeypatch.setattr(rendering, "_materiality_validate_rewrite_candidate", validate)
    monkeypatch.setattr(rendering, "_apply_post_refinement_export_gate", export)


def _rewrite_diagnosis():
    return {"diagnosis_action": "rewrite", "bullet_id": "bullet_1"}


def test_none_context_skips_refinement_but_keeps_validation_and_export(monkeypatch):
    calls = {"helper": 0, "writer": 0, "judge": 0, "materiality": 0, "export": 0}
    _install_candidate_pipeline(monkeypatch, calls)

    def unexpected(name):
        def fail(*args, **kwargs):
            calls[name] += 1
            raise AssertionError(f"{name} must not run without explicit LLM opt-in")

        return fail

    monkeypatch.setattr(
        tailoring_llm,
        "_maybe_refine_patch_ready_rewrite_candidate",
        unexpected("helper"),
    )
    monkeypatch.setattr(
        tailoring_llm, "_run_patch_refinement_writer_plain_call", unexpected("writer")
    )
    monkeypatch.setattr(
        tailoring_llm, "_run_patch_refinement_judge_plain_call", unexpected("judge")
    )

    candidates = rendering._build_replacement_candidates(
        {}, [_rewrite_diagnosis()], llm_output=None
    )

    assert calls == {"helper": 0, "writer": 0, "judge": 0, "materiality": 2, "export": 1}
    protected = {
        key: _candidate()[key]
        for key in (
            "priority_score",
            "rank",
            "queue_position",
            "operator_state",
            "application_status",
            "auto_apply_performed",
        )
    }
    assert {key: candidates[0][key] for key in protected} == protected


def test_non_none_live_context_runs_existing_writer_judge_helper(monkeypatch):
    calls = {"writer": 0, "judge": 0, "materiality": 0, "export": 0}
    _install_candidate_pipeline(monkeypatch, calls)
    monkeypatch.setattr(
        tailoring_llm,
        "_patch_refinement_deterministic_alignment_sufficient",
        lambda payload, candidate: (False, "needs refinement"),
    )
    monkeypatch.setattr(
        tailoring_llm,
        "_validate_patch_refinement_output",
        lambda candidate, patch_text: (True, "valid"),
    )
    monkeypatch.setattr(
        tailoring_llm, "_patch_refinement_style_only_delta", lambda before, after: False
    )

    def writer(**kwargs):
        calls["writer"] += 1
        return (
            {
                "options": [
                    {
                        "patch_text": "Built weekly SQL dashboards that informed stakeholder reviews.",
                        "reason": "Fronts the supported signal.",
                    }
                ]
            },
            {"provider": "test", "model": "writer"},
            None,
            "writer output",
        )

    def judge(**kwargs):
        calls["judge"] += 1
        return (
            {"winner": "writer_option_1", "reason": "More direct."},
            {"provider": "test", "model": "judge"},
            None,
            "judge output",
        )

    monkeypatch.setattr(tailoring_llm, "_run_patch_refinement_writer_plain_call", writer)
    monkeypatch.setattr(tailoring_llm, "_run_patch_refinement_judge_plain_call", judge)

    candidates = rendering._build_replacement_candidates(
        {},
        [_rewrite_diagnosis()],
        llm_output={"provider": "test", "parsed": {}},
    )

    assert calls == {"writer": 1, "judge": 1, "materiality": 2, "export": 1}
    assert candidates[0]["llm_refinement_status"] == "judge_selected_writer_option"
    assert candidates[0]["llm_export_decision"] == "writer_kept_material"


def test_legacy_rehydration_and_repeated_reads_pass_none_without_provider_calls(
    monkeypatch, tmp_path
):
    packet_path = tmp_path / "job.json"
    packet_path.write_text(json.dumps({}), encoding="utf-8")
    artifact_path = tmp_path / "job__tailoring.json"
    calls = {"operator": 0, "writer": 0, "judge": 0}

    monkeypatch.setattr(
        services,
        "_infer_packet_json_path_from_tailoring_artifact",
        lambda path: packet_path,
    )
    monkeypatch.setattr("src.tailoring.packet_support._load_packet", lambda path: {})
    monkeypatch.setattr(rendering, "_build_payload", lambda packet, include_llm_prompts: {})

    def operator(payload, llm_output, **kwargs):
        calls["operator"] += 1
        assert llm_output is None
        return {"replacement_candidates": [{"candidate_id": "replacement_1"}]}

    def unexpected(name):
        def fail(*args, **kwargs):
            calls[name] += 1
            raise AssertionError(f"{name} must not run during artifact reads")

        return fail

    monkeypatch.setattr(rendering, "_build_operator_markdown_payload", operator)
    monkeypatch.setattr(
        tailoring_llm, "_run_patch_refinement_writer_plain_call", unexpected("writer")
    )
    monkeypatch.setattr(
        tailoring_llm, "_run_patch_refinement_judge_plain_call", unexpected("judge")
    )

    legacy_payload = {"rewrite_candidates": [{"bullet_id": "bullet_1"}]}
    first = services._rehydrate_legacy_tailoring_operator_payload(
        artifact_path, legacy_payload
    )
    second = services._rehydrate_legacy_tailoring_operator_payload(
        artifact_path, legacy_payload
    )

    assert first["replacement_candidates"] == second["replacement_candidates"]
    assert calls == {"operator": 2, "writer": 0, "judge": 0}
