from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import batch_select_best_resume_variant as selector
import run_application_planning as planning
from src.pipeline import shadow_resume_evidence_projection as projection


def _candidate(resume_id: str = "resume-a.pdf") -> dict:
    return {
        "contract_version": projection.PROJECTION_CONTRACT_VERSION,
        "resumes": [
            {
                "resume_id": resume_id,
                "evidence_rows": [
                    {"resume_id": resume_id, "skills": ["Python"]}
                ],
            }
        ],
    }


def _manifest(resume_id: str = "resume-a.pdf") -> list[dict]:
    return [{"job_doc_id": "job-1", "packet_resume": resume_id}]


def test_handoff_contract_is_deterministic_bounded_and_restrictive(tmp_path):
    status = projection.build_handoff_status(
        status="ready",
        reason_code="projection_ready",
        selected_resume_count=1,
        projected_resume_count=1,
    )
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    projection.write_handoff_status_atomic(first, status)
    projection.write_handoff_status_atomic(second, status)
    assert first.read_bytes() == second.read_bytes()
    assert len(first.read_bytes()) <= projection.MAX_HANDOFF_SERIALIZED_BYTES
    assert first.stat().st_mode & 0o777 == 0o600
    assert projection.load_handoff_status(first) == status
    assert "resume-a" not in first.read_text()
    assert set(status) == {
        "contract_version",
        "status",
        "reason_code",
        "projection_available",
        "selected_resume_count",
        "projected_resume_count",
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"contract_version": "wrong"},
        {
            "contract_version": projection.HANDOFF_CONTRACT_VERSION,
            "status": "ready",
            "reason_code": "unknown",
            "projection_available": True,
            "selected_resume_count": 1,
            "projected_resume_count": 1,
        },
    ],
)
def test_handoff_reader_rejects_malformed_contract(payload, tmp_path):
    path = tmp_path / "status.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(projection.ProjectionError):
        projection.load_handoff_status(path)


def test_handoff_reader_rejects_duplicate_fields(tmp_path):
    path = tmp_path / "status.json"
    path.write_text(
        '{"contract_version":"applylens-shadow-resume-evidence-handoff-v1",'
        '"status":"ready","status":"failed","reason_code":"projection_ready",'
        '"projection_available":true,"selected_resume_count":1,'
        '"projected_resume_count":1}',
        encoding="utf-8",
    )
    with pytest.raises(
        projection.ProjectionError, match="handoff_status_malformed"
    ):
        projection.load_handoff_status(path)


def test_non_authoritative_candidate_failure_is_isolated_and_removes_stale(
    monkeypatch, tmp_path
):
    output = tmp_path / "candidate.json"
    output.write_text("stale", encoding="utf-8")

    def fail(_values):
        raise projection.ProjectionError("projection_malformed")

    monkeypatch.setattr(projection, "build_candidate_projection", fail)
    assert not selector._write_requested_shadow_resume_evidence_candidate(
        str(output), [], non_authoritative=True
    )
    assert not output.exists()


def test_strict_candidate_failure_remains_fail_closed(monkeypatch, tmp_path):
    def fail(_values):
        raise projection.ProjectionError("projection_malformed")

    monkeypatch.setattr(projection, "build_candidate_projection", fail)
    with pytest.raises(projection.ProjectionError):
        selector._write_requested_shadow_resume_evidence_candidate(
            str(tmp_path / "candidate.json"), []
        )


def test_candidate_boundary_does_not_hide_authoritative_defects(
    monkeypatch, tmp_path
):
    def fail(_values):
        raise RuntimeError("authoritative defect")

    monkeypatch.setattr(projection, "build_candidate_projection", fail)
    with pytest.raises(RuntimeError, match="authoritative defect"):
        selector._write_requested_shadow_resume_evidence_candidate(
            str(tmp_path / "candidate.json"),
            [],
            non_authoritative=True,
        )


def test_non_authoritative_final_success_writes_projection_and_ready_status(
    tmp_path,
):
    candidate = tmp_path / "candidate.json"
    final = tmp_path / "final.json"
    status_path = tmp_path / "status.json"
    projection.write_projection_atomic(candidate, _candidate())
    status = planning._write_non_authoritative_shadow_resume_evidence_handoff(
        candidate_path=candidate,
        manifest_rows=_manifest(),
        output_path=final,
        status_output_path=status_path,
    )
    assert status["status"] == "ready"
    assert projection.load_projection(final) == _candidate()
    assert projection.load_handoff_status(status_path) == status
    assert final.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize(
    ("candidate_contents", "resume_id", "reason"),
    [
        (None, "resume-a.pdf", "candidate_projection_missing"),
        ("not json", "resume-a.pdf", "candidate_projection_malformed"),
        ("valid", "resume-b.pdf", "selected_resume_evidence_missing"),
    ],
)
def test_non_authoritative_final_failures_write_bounded_status(
    tmp_path, candidate_contents, resume_id, reason
):
    candidate = tmp_path / "candidate.json"
    final = tmp_path / "final.json"
    status_path = tmp_path / "status.json"
    final.write_text("stale", encoding="utf-8")
    if candidate_contents == "valid":
        projection.write_projection_atomic(candidate, _candidate())
    elif candidate_contents is not None:
        candidate.write_text(candidate_contents, encoding="utf-8")
    status = planning._write_non_authoritative_shadow_resume_evidence_handoff(
        candidate_path=candidate,
        manifest_rows=_manifest(resume_id),
        output_path=final,
        status_output_path=status_path,
    )
    assert status["status"] == "failed"
    assert status["reason_code"] == reason
    assert not status["projection_available"]
    assert not final.exists()
    assert projection.load_handoff_status(status_path) == status


def test_no_selected_resumes_is_skipped(tmp_path):
    final = tmp_path / "final.json"
    status_path = tmp_path / "status.json"
    status = planning._write_non_authoritative_shadow_resume_evidence_handoff(
        candidate_path=tmp_path / "missing.json",
        manifest_rows=[{"job_doc_id": "job-1", "packet_resume": ""}],
        output_path=final,
        status_output_path=status_path,
    )
    assert status["status"] == "skipped"
    assert status["reason_code"] == "no_final_selected_resumes"
    assert not final.exists()


def test_final_projection_write_failure_isolated(monkeypatch, tmp_path):
    candidate = tmp_path / "candidate.json"
    projection.write_projection_atomic(candidate, _candidate())

    def fail(_path, _payload):
        raise projection.ProjectionError("projection_malformed")

    monkeypatch.setattr(projection, "write_projection_atomic", fail)
    status = planning._write_non_authoritative_shadow_resume_evidence_handoff(
        candidate_path=candidate,
        manifest_rows=_manifest(),
        output_path=tmp_path / "final.json",
        status_output_path=tmp_path / "status.json",
    )
    assert status["reason_code"] == "final_projection_failed"


def test_non_authoritative_boundary_does_not_hide_non_projection_exception(
    monkeypatch, tmp_path
):
    candidate = tmp_path / "candidate.json"
    projection.write_projection_atomic(candidate, _candidate())

    def fail(_payload, _rows):
        raise RuntimeError("planning defect")

    monkeypatch.setattr(projection, "filter_projection_by_packet_manifest", fail)
    with pytest.raises(RuntimeError, match="planning defect"):
        planning._write_non_authoritative_shadow_resume_evidence_handoff(
            candidate_path=candidate,
            manifest_rows=_manifest(),
            output_path=tmp_path / "final.json",
            status_output_path=tmp_path / "status.json",
        )


def test_temporary_candidate_workspace_is_0700_and_removed():
    with projection.temporary_candidate_projection_path() as candidate:
        directory = candidate.parent
        assert directory.stat().st_mode & 0o777 == 0o700
    assert not directory.exists()


def test_authoritative_main_failure_removes_both_handoffs(monkeypatch, tmp_path):
    final = tmp_path / "final.json"
    status = tmp_path / "status.json"
    final.write_text("stale", encoding="utf-8")
    status.write_text("stale", encoding="utf-8")
    monkeypatch.setattr(
        planning,
        "_main",
        lambda _candidate=None: (_ for _ in ()).throw(
            RuntimeError("authoritative failure")
        ),
    )
    monkeypatch.setattr(
        planning.sys,
        "argv",
        [
            "run_application_planning.py",
            "--shadow-resume-evidence-output",
            str(final),
            "--shadow-resume-evidence-non-authoritative",
            "--shadow-resume-evidence-status-output",
            str(status),
        ],
    )
    with pytest.raises(RuntimeError, match="authoritative failure"):
        planning.main()
    assert not final.exists()
    assert not status.exists()


def test_absent_options_bypass_projection_workspace(monkeypatch):
    called = []
    monkeypatch.setattr(planning, "_main", lambda: called.append(True))
    monkeypatch.setattr(planning.sys, "argv", ["run_application_planning.py"])
    planning.main()
    assert called == [True]


def test_no_environment_activation(monkeypatch):
    monkeypatch.setenv("SHADOW_RESUME_EVIDENCE_NON_AUTHORITATIVE", "1")
    assert not planning._shadow_projection_requested([])


@pytest.mark.parametrize(
    "arguments",
    [
        ["--shadow-resume-evidence-non-authoritative"],
        [
            "--shadow-resume-evidence-output",
            "projection.json",
            "--shadow-resume-evidence-non-authoritative",
        ],
        ["--shadow-resume-evidence-status-output", "status.json"],
        [
            "--shadow-resume-evidence-output",
            "same.json",
            "--shadow-resume-evidence-non-authoritative",
            "--shadow-resume-evidence-status-output",
            "same.json",
        ],
    ],
)
def test_invalid_mode_combinations_fail_before_authoritative_work(
    monkeypatch, arguments
):
    monkeypatch.setattr(
        planning.sys, "argv", ["run_application_planning.py", *arguments]
    )
    monkeypatch.setattr(
        planning,
        "_job_corpus_has_records",
        lambda _path: pytest.fail("authoritative work started"),
    )
    with pytest.raises(SystemExit) as exc:
        planning._main()
    assert exc.value.code == 2


def test_expected_safety_boundaries_remain_absent():
    root = Path(__file__).resolve().parents[1]
    main_source = (root / "main.py").read_text(encoding="utf-8")
    planning_source = (root / "run_application_planning.py").read_text(
        encoding="utf-8"
    )
    assert "shadow-resume-evidence-non-authoritative" not in main_source
    assert "run_evidence_chain_shadow" not in planning_source
    assert "evidence_chain_shadow_execution" not in planning_source
