from __future__ import annotations

import csv
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

import run_evidence_chain_shadow as command


ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "run_evidence_chain_shadow.py"


def _fixtures(tmp_path: Path):
    corpus = {
        "doc_id": "job-command",
        "title": "Synthetic Engineer",
        "company": "Synthetic Co",
        "intelligence": {
            "skills": {
                "required": ["Python"],
                "preferred": [],
                "all": ["Python"],
            }
        },
        "ai_fit_score": 7,
        "priority_score": 9,
    }
    rows_by_name = {
        "best": [{"job_doc_id": "job-command", "winner_resume": "resume-command"}],
        "queue": [{
            "job_doc_id": "job-command",
            "winner_resume": "resume-command",
            "resolved_resume": "resume-command",
            "action": "REVIEW",
        }],
        "manifest": [{
            "job_doc_id": "job-command",
            "packet_resume": "resume-command",
        }],
    }
    corpus_path = tmp_path / "corpus.jsonl"
    corpus_path.write_text(json.dumps(corpus) + "\n", encoding="utf-8")
    paths = {"corpus": corpus_path}
    for name, rows in rows_by_name.items():
        path = tmp_path / f"{name}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        paths[name] = path
    evidence = tmp_path / "evidence.json"
    evidence.write_text(json.dumps({
        "resumes": [{
            "resume_id": "resume-command",
            "evidence_rows": [{
                "resume_id": "resume-command",
                "skills": ["Python"],
                "raw_text": "Synthetic evidence.",
            }],
        }]
    }), encoding="utf-8")
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({
        "jobs": [{
            "job_id": "job-command",
            "comparisons": [
                {"field": "job_id", "mode": "exact",
                 "authoritative_value": "job-command"},
                {"field": "pending_node", "mode": "exact",
                 "authoritative_value": "finalize"},
            ],
        }]
    }), encoding="utf-8")
    paths.update({"evidence": evidence, "facts": facts})
    return paths


def _args(paths, *, acknowledgement=True):
    args = []
    if acknowledgement:
        args.append("--execute-shadow")
    args.extend([
        "--job-corpus", str(paths["corpus"]),
        "--best-resume", str(paths["best"]),
        "--execution-queue", str(paths["queue"]),
        "--packet-manifest", str(paths["manifest"]),
        "--resume-evidence", str(paths["evidence"]),
        "--authoritative-facts", str(paths["facts"]),
        "--owner-id", "owner-command",
        "--pipeline-run-id", "run-command",
        "--context-id", "context-command",
    ])
    return args


def _run(args, timeout=15):
    return subprocess.run(
        [sys.executable, str(COMMAND), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        shell=False,
        timeout=timeout,
        check=False,
    )


def test_import_executes_nothing(monkeypatch):
    monkeypatch.setattr(sys, "argv", [str(COMMAND), "--execute-shadow"])
    assert importlib.reload(command).main is not None


def test_missing_acknowledgement_rejects_before_artifact_reads(tmp_path, monkeypatch):
    paths = _fixtures(tmp_path)
    monkeypatch.setattr(Path, "read_text", lambda *_a, **_k: pytest.fail("artifact read"))
    with pytest.raises(command.CommandInputError, match="acknowledgement"):
        command.main(_args(paths, acknowledgement=False))


@pytest.mark.parametrize(
    ("flag", "failure"),
    [
        ("--owner-id", "owner_identity_missing"),
        ("--pipeline-run-id", "pipeline_identity_missing"),
        ("--context-id", "context_identity_missing"),
        ("--resume-evidence", "resume_evidence_missing"),
    ],
)
def test_missing_required_identity_or_evidence(tmp_path, flag, failure):
    paths = _fixtures(tmp_path)
    args = _args(paths)
    index = args.index(flag)
    del args[index:index + 2]
    result = _run(args)
    assert result.returncode == 2
    assert json.loads(result.stderr)["failure_code"] == failure
    assert result.stdout == ""


def test_malformed_and_duplicate_evidence_reject(tmp_path):
    paths = _fixtures(tmp_path)
    paths["evidence"].write_text("{bad", encoding="utf-8")
    assert json.loads(_run(_args(paths)).stderr)["failure_code"] == (
        "resume_evidence_malformed"
    )
    paths["evidence"].write_text(json.dumps({"resumes": [
        {"resume_id": "r", "evidence_rows": [{"resume_id": "r"}]},
        {"resume_id": "r", "evidence_rows": [{"resume_id": "r"}]},
    ]}), encoding="utf-8")
    assert json.loads(_run(_args(paths)).stderr)["failure_code"] == (
        "resume_identity_duplicate"
    )


def test_excessively_large_evidence_is_rejected(tmp_path):
    paths = _fixtures(tmp_path)
    paths["evidence"].write_bytes(b" " * (command.MAX_INPUT_BYTES + 1))
    result = _run(_args(paths))
    assert result.returncode == 2
    assert json.loads(result.stderr)["failure_code"] == "resume_evidence_too_large"


def test_unknown_argument_is_rejected(tmp_path):
    result = _run([*_args(_fixtures(tmp_path)), "--unknown"])
    assert result.returncode == 2
    assert result.stdout == ""
    assert len(result.stderr) < 4000


def test_valid_command_emits_one_bounded_json_and_changes_nothing(tmp_path):
    paths = _fixtures(tmp_path)
    before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths.values()
    }
    result = _run(_args(paths))
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    assert len(result.stdout) < 20_000
    payload = json.loads(result.stdout)
    job = payload["results"][0]
    assert job["status"] == "parity_completed"
    assert job["execution_status"] == "completed_at_operator_review"
    assert job["shadow_facts"]["completed_node_order"][-1] == "operator_review"
    assert job["shadow_facts"]["pending_node"] == "finalize"
    assert job["shadow_facts"]["finalization_executed"] is False
    assert payload["artifacts_unchanged"] is True
    assert {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths.values()
    } == before
    rendered = result.stdout.lower()
    for forbidden in (
        "synthetic evidence.",
        "graph state",
        "checkpoint",
        "database_url",
        "authorization",
    ):
        assert forbidden not in rendered


def test_command_has_no_production_import_or_database_argument():
    source = COMMAND.read_text(encoding="utf-8")
    for forbidden in (
        "main.py",
        "run_application_planning",
        "src.pipeline.collector",
        "DATABASE_URL",
        "durable",
        "notification",
        "application_action",
        "load_dotenv",
    ):
        assert forbidden not in source
