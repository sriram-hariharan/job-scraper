from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import stat
import sys

import pytest

import batch_select_best_resume_variant as selector
import run_application_planning as planning
from run_evidence_chain_shadow import _resume_evidence
from src.pipeline.shadow_resume_evidence_projection import (
    MAX_EVIDENCE_ROWS_PER_RESUME,
    MAX_LIST_ITEMS,
    MAX_SELECTED_RESUMES,
    MAX_SERIALIZED_BYTES,
    MAX_STRING_LENGTH,
    PROJECTION_CONTRACT_VERSION,
    ProjectionError,
    build_candidate_projection,
    filter_projection_by_packet_manifest,
    load_projection,
    remove_projection_output,
    temporary_candidate_projection_path,
    validate_projection,
    write_projection_atomic,
)
from src.resume.models import (
    ResumeDocument,
    ResumeEvidence,
    ResumeExperienceEntry,
    ResumeProjectEntry,
)


def _evidence(resume_id: str, *, marker: str = "python") -> ResumeEvidence:
    return ResumeEvidence(
        document=ResumeDocument(
            resume_id=resume_id,
            resume_name=resume_id,
            path=f"/private/{resume_id}",
            raw_text=f"SECRET RAW {resume_id}",
            normalized_text=f"secret normalized {resume_id}",
        ),
        titles=["Machine Learning Engineer"],
        companies=["Private Employer"],
        locations=["Private Location"],
        skills=[marker, "sql"],
        experience_entries=[
            ResumeExperienceEntry(
                entry_id="experience:0:stable",
                title="Engineer",
                company="Private Employer",
                location="Private Location",
                bullets=[f"Built {marker} systems"],
                bullet_ids=[f"{resume_id}:experience:0:b0"],
            )
        ],
        project_entries=[
            ResumeProjectEntry(
                entry_id="project:0:stable",
                name="Private Project",
                bullets=[f"Deployed {marker} workflows"],
                bullet_ids=[f"{resume_id}:project:0:b0"],
            )
        ],
        domain_signals=["healthcare"],
        analytics_ml_signals=["machine learning"],
        tooling_signals=["docker"],
        quantified_bullets=["Improved quality by 20%"],
        methods=["experimentation"],
        tools=["python", "docker"],
        workflows=["model deployment"],
        business_contexts=["customer analytics"],
        stakeholder_contexts=["executive communication"],
        ownership_signals=["owned roadmap"],
        notes={
            "email": "must-not-project@example.test",
            "provider_response": "must not project",
        },
    )


def _candidate(*resume_ids: str) -> dict:
    return build_candidate_projection(
        [_evidence(resume_id, marker=f"skill-{index}") for index, resume_id in enumerate(resume_ids)]
    )


def _manifest(*pairs: tuple[str, str]) -> list[dict[str, str]]:
    return [
        {"job_doc_id": job_id, "packet_resume": resume_id}
        for job_id, resume_id in pairs
    ]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_projection_normalization_is_deterministic_non_mutating_and_step3_shaped():
    evidence_objects = [_evidence("resume-b.pdf"), _evidence("resume-a.pdf")]
    before = deepcopy(evidence_objects)

    first = build_candidate_projection(evidence_objects)
    second = build_candidate_projection(evidence_objects)

    assert first == second
    assert evidence_objects == before
    assert first["contract_version"] == PROJECTION_CONTRACT_VERSION
    assert [entry["resume_id"] for entry in first["resumes"]] == [
        "resume-a.pdf",
        "resume-b.pdf",
    ]
    accepted = _resume_evidence(first)
    assert set(accepted) == {"resume-a.pdf", "resume-b.pdf"}
    assert accepted["resume-a.pdf"][0]["resume_id"] == "resume-a.pdf"


def test_projection_uses_only_existing_allowed_evidence_and_excludes_sensitive_fields():
    payload = _candidate("resume-a.pdf")
    serialized = json.dumps(payload, sort_keys=True)
    row = payload["resumes"][0]["evidence_rows"][0]

    assert set(row) == {
        "resume_id",
        "resume_name",
        "titles",
        "skills",
        "tools",
        "methods",
        "workflows",
        "business_contexts",
        "stakeholder_contexts",
        "ownership_signals",
        "domain_signals",
        "analytics_ml_signals",
        "tooling_signals",
        "quantified_bullets",
        "bullets",
        "source_bullet_ids",
    }
    for forbidden in (
        "SECRET RAW",
        "secret normalized",
        "/private/",
        "Private Employer",
        "Private Location",
        "Private Project",
        "must-not-project@example.test",
        "provider_response",
        "notes",
    ):
        assert forbidden not in serialized


def test_resume_count_blank_and_duplicate_identity_bounds():
    with pytest.raises(ProjectionError, match="projection_limit_exceeded"):
        build_candidate_projection(
            [_evidence(f"resume-{index}.pdf") for index in range(MAX_SELECTED_RESUMES + 1)]
        )
    with pytest.raises(ProjectionError, match="blank_resume_identity"):
        build_candidate_projection([_evidence("")])
    with pytest.raises(ProjectionError, match="duplicate_resume_identity"):
        build_candidate_projection([_evidence("same.pdf"), _evidence("same.pdf")])


def test_row_count_malformed_nested_and_sensitive_fields_are_rejected():
    payload = _candidate("resume-a.pdf")
    payload["resumes"][0]["evidence_rows"] = [
        {"resume_id": "resume-a.pdf"}
        for _ in range(MAX_EVIDENCE_ROWS_PER_RESUME + 1)
    ]
    with pytest.raises(ProjectionError, match="projection_limit_exceeded"):
        validate_projection(payload)

    malformed = _candidate("resume-a.pdf")
    malformed["resumes"][0]["evidence_rows"][0]["skills"] = {"python": True}
    with pytest.raises(ProjectionError, match="projection_malformed"):
        validate_projection(malformed)

    sensitive = _candidate("resume-a.pdf")
    sensitive["resumes"][0]["evidence_rows"][0]["raw_text"] = ["secret"]
    with pytest.raises(
        ProjectionError, match="projection_sensitive_field_rejected"
    ):
        validate_projection(sensitive)


def test_strings_and_lists_are_bounded_without_truncating_resume_identity():
    evidence = _evidence("resume-a.pdf")
    evidence.skills = [f"skill-{index}-" + ("x" * 800) for index in range(80)]
    payload = build_candidate_projection([evidence])
    skills = payload["resumes"][0]["evidence_rows"][0]["skills"]

    assert len(skills) == MAX_LIST_ITEMS
    assert all(len(value) <= MAX_STRING_LENGTH for value in skills)
    assert payload["resumes"][0]["resume_id"] == "resume-a.pdf"


def test_total_serialized_size_limit_is_fail_closed():
    payload = {
        "contract_version": PROJECTION_CONTRACT_VERSION,
        "resumes": [],
    }
    for resume_index in range(MAX_SELECTED_RESUMES):
        resume_id = f"resume-{resume_index}.pdf"
        payload["resumes"].append(
            {
                "resume_id": resume_id,
                "evidence_rows": [
                    {
                        "resume_id": resume_id,
                        "resume_name": resume_id,
                        "skills": [
                            f"{resume_index}-{item}-" + ("x" * MAX_STRING_LENGTH)
                            for item in range(MAX_LIST_ITEMS)
                        ],
                        "bullets": [
                            f"{resume_index}-{item}-" + ("y" * MAX_STRING_LENGTH)
                            for item in range(MAX_LIST_ITEMS)
                        ],
                    }
                ],
            }
        )

    assert len(json.dumps(payload).encode("utf-8")) > MAX_SERIALIZED_BYTES
    with pytest.raises(ProjectionError, match="projection_limit_exceeded"):
        validate_projection(payload)


def test_manifest_packet_resume_is_the_only_selection_authority():
    candidate = _candidate("best.pdf", "queue.pdf", "packet.pdf")
    manifest = _manifest(("job-1", "packet.pdf"))
    final = filter_projection_by_packet_manifest(candidate, manifest)

    assert [entry["resume_id"] for entry in final["resumes"]] == ["packet.pdf"]
    assert "best.pdf" not in json.dumps(final)
    assert "queue.pdf" not in json.dumps(final)


def test_duplicate_selected_resume_collapses_but_conflicting_job_rows_fail():
    candidate = _candidate("selected.pdf", "other.pdf")
    final = filter_projection_by_packet_manifest(
        candidate,
        _manifest(("job-1", "selected.pdf"), ("job-2", "selected.pdf")),
    )
    assert [entry["resume_id"] for entry in final["resumes"]] == ["selected.pdf"]

    with pytest.raises(ProjectionError, match="projection_malformed"):
        filter_projection_by_packet_manifest(
            candidate,
            _manifest(("job-1", "selected.pdf"), ("job-1", "other.pdf")),
        )


def test_missing_selected_evidence_fails_without_silent_identity_truncation():
    with pytest.raises(
        ProjectionError, match="selected_resume_evidence_missing"
    ):
        filter_projection_by_packet_manifest(
            _candidate("available.pdf"),
            _manifest(("job-1", "missing.pdf")),
        )


def test_restrictive_atomic_output_and_load_round_trip(tmp_path):
    output = tmp_path / "final.json"
    output.write_text("old", encoding="utf-8")
    output.chmod(0o644)

    write_projection_atomic(output, _candidate("resume-a.pdf"))

    assert load_projection(output) == _candidate("resume-a.pdf")
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    assert not list(tmp_path.glob(f".{output.name}.*.tmp"))


def test_unsafe_symlink_and_directory_outputs_fail_closed(tmp_path):
    real = tmp_path / "real.json"
    real.write_text("untouched", encoding="utf-8")
    symlink = tmp_path / "link.json"
    symlink.symlink_to(real)
    with pytest.raises(ProjectionError, match="projection_malformed"):
        write_projection_atomic(symlink, _candidate("resume-a.pdf"))
    assert real.read_text(encoding="utf-8") == "untouched"

    directory = tmp_path / "directory"
    directory.mkdir()
    with pytest.raises(ProjectionError, match="projection_malformed"):
        write_projection_atomic(directory, _candidate("resume-a.pdf"))


def test_temporary_candidate_workspace_is_0700_and_always_cleaned():
    with temporary_candidate_projection_path() as candidate_path:
        directory = candidate_path.parent
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
        candidate_path.write_text("synthetic", encoding="utf-8")
    assert not directory.exists()


def test_batch_selector_absent_option_is_a_noop_and_explicit_uses_supplied_objects(
    tmp_path, monkeypatch
):
    evidence_objects = [_evidence("resume-a.pdf")]
    parse_calls = []
    monkeypatch.setattr(
        selector,
        "load_resume_documents",
        lambda: parse_calls.append("unexpected"),
    )

    assert selector._write_requested_shadow_resume_evidence_candidate(
        "", evidence_objects
    ) is False
    assert list(tmp_path.iterdir()) == []

    output = tmp_path / "candidate.json"
    assert selector._write_requested_shadow_resume_evidence_candidate(
        str(output), evidence_objects
    ) is True
    assert load_projection(output)["resumes"][0]["resume_id"] == "resume-a.pdf"
    assert parse_calls == []


def test_batch_projection_failure_leaves_no_partial_and_does_not_modify_authority(
    tmp_path,
):
    authoritative = tmp_path / "best_resume_variant_by_job.csv"
    authoritative.write_text("job_doc_id,winner_resume\njob-1,resume-a.pdf\n")
    digest_before = _digest(authoritative)
    output = tmp_path / "candidate.json"

    with pytest.raises(ProjectionError, match="duplicate_resume_identity"):
        selector._write_requested_shadow_resume_evidence_candidate(
            str(output),
            [_evidence("same.pdf"), _evidence("same.pdf")],
        )

    assert not output.exists()
    assert _digest(authoritative) == digest_before


def test_planning_absent_option_creates_no_candidate_workspace(monkeypatch):
    captured = []
    monkeypatch.setattr(sys, "argv", ["run_application_planning.py"])
    monkeypatch.setattr(
        planning,
        "_main",
        lambda candidate_path=None: captured.append(candidate_path),
    )

    planning.main()

    assert captured == [None]


def test_planning_explicit_option_owns_and_cleans_restrictive_workspace(
    monkeypatch, tmp_path
):
    final_output = tmp_path / "final.json"
    observed = {}
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_application_planning.py",
            "--shadow-resume-evidence-output",
            str(final_output),
        ],
    )

    def fake_main(candidate_path=None):
        observed["candidate"] = candidate_path
        observed["directory"] = candidate_path.parent
        observed["mode"] = stat.S_IMODE(candidate_path.parent.stat().st_mode)
        candidate_path.write_text("synthetic", encoding="utf-8")

    monkeypatch.setattr(planning, "_main", fake_main)
    planning.main()

    assert observed["candidate"].name == "candidate_projection.json"
    assert observed["mode"] == 0o700
    assert not observed["directory"].exists()


def test_planning_failure_removes_final_output_and_candidate(monkeypatch, tmp_path):
    final_output = tmp_path / "final.json"
    final_output.write_text("stale", encoding="utf-8")
    observed = {}
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_application_planning.py",
            f"--shadow-resume-evidence-output={final_output}",
        ],
    )

    def failing_main(candidate_path=None):
        observed["directory"] = candidate_path.parent
        candidate_path.write_text("partial candidate", encoding="utf-8")
        raise RuntimeError("synthetic_planning_failure")

    monkeypatch.setattr(planning, "_main", failing_main)
    with pytest.raises(RuntimeError, match="synthetic_planning_failure"):
        planning.main()

    assert not final_output.exists()
    assert not observed["directory"].exists()


def test_planning_final_filter_is_step3_compatible_and_cleans_candidate(tmp_path):
    candidate_path = tmp_path / "candidate.json"
    final_path = tmp_path / "final.json"
    write_projection_atomic(
        candidate_path,
        _candidate("nonselected.pdf", "selected.pdf"),
    )
    authoritative = tmp_path / "job_packet_manifest.csv"
    authoritative.write_text(
        "job_doc_id,packet_resume\njob-1,selected.pdf\n",
        encoding="utf-8",
    )
    digest_before = _digest(authoritative)

    planning._write_final_shadow_resume_evidence_projection(
        candidate_path=candidate_path,
        manifest_rows=_manifest(("job-1", "selected.pdf")),
        output_path=final_path,
    )
    loaded = json.loads(final_path.read_text(encoding="utf-8"))
    accepted = _resume_evidence(loaded)

    assert set(accepted) == {"selected.pdf"}
    assert "nonselected.pdf" not in json.dumps(loaded)
    assert stat.S_IMODE(final_path.stat().st_mode) == 0o600
    assert _digest(authoritative) == digest_before
    remove_projection_output(candidate_path)
    assert not candidate_path.exists()


def test_projection_diagnostics_are_codes_only_and_do_not_leak_evidence():
    secret = "highly-sensitive-evidence-marker"
    malformed = _candidate("resume-a.pdf")
    malformed["resumes"][0]["evidence_rows"][0]["raw_text"] = [secret]

    with pytest.raises(ProjectionError) as captured:
        validate_projection(malformed)

    assert str(captured.value) == "projection_sensitive_field_rejected"
    assert secret not in str(captured.value)


def test_step5a_modules_do_not_wire_runtime_graph_actions_or_main():
    projection_source = Path(
        "src/pipeline/shadow_resume_evidence_projection.py"
    ).read_text(encoding="utf-8")
    selector_source = Path("batch_select_best_resume_variant.py").read_text(
        encoding="utf-8"
    )
    planning_source = Path("run_application_planning.py").read_text(
        encoding="utf-8"
    )
    combined = "\n".join((projection_source, selector_source, planning_source))

    for forbidden in (
        "run_evidence_chain_shadow",
        "evidence_chain_shadow_execution",
        "PostgresSaver",
        "durable_orchestration",
        "submit_application",
        "create_application_action",
        "import main",
        "from main",
    ):
        assert forbidden not in combined
    assert "APPLYLENS_DURABLE_EVIDENCE_CHAIN_SHADOW_ENABLED" not in combined
