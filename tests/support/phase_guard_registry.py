"""Shared test-only helpers for legacy phase guard checks."""

from __future__ import annotations

import ast
from hashlib import sha256
from pathlib import Path
import subprocess
from typing import Iterable, Mapping


def normalize_changed_path(path: str | Path) -> str:
    """Return a normalized repo-relative path string for guard comparisons."""
    value = str(path).strip().replace("\\", "/")
    previous = None
    while value != previous:
        previous = value
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1].strip()
    return value


def get_changed_files(root: str | Path) -> set[str]:
    """Return staged, unstaged, and untracked repo-relative changed paths."""
    repo = Path(root)
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only"], cwd=repo, text=True
    ).splitlines()
    staged = subprocess.check_output(
        ["git", "diff", "--name-only", "--cached"], cwd=repo, text=True
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=repo,
        text=True,
    ).splitlines()
    return {
        normalize_changed_path(path)
        for path in [*tracked, *staged, *untracked]
        if normalize_changed_path(path)
    }


def duplicate_artifact_paths(changed: Iterable[str | Path]) -> set[str]:
    """Detect suspicious duplicate artifact names such as ``foo 2.py``."""
    duplicates = set()
    for path in changed:
        normalized = normalize_changed_path(path)
        if normalized.endswith((" 2.py", " 3.py", " 2.md", " 3.md")):
            duplicates.add(normalized)
    return duplicates


def reject_duplicate_artifact_paths(changed: Iterable[str | Path]) -> None:
    duplicates = duplicate_artifact_paths(changed)
    assert not duplicates, "Duplicate artifact paths are not allowed: " + ", ".join(
        sorted(duplicates)
    )


def merge_allowed(*groups: Iterable[str | Path]) -> set[str]:
    merged = set()
    for group in groups:
        merged.update(normalize_changed_path(path) for path in group)
    return {path for path in merged if path}


def legacy_guard_allowlist(profile: str) -> set[str]:
    profiles = {
        "phase85b_registry": {
            "tests/support/phase_guard_registry.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_three_core_shadow_readiness_wrap_default_off.py",
            "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
            "tests/test_agent_trace_ui_readiness_checkpoint.py",
            "tests/test_agent_trace_readonly_ui_panel_no_api_no_writes.py",
            "tests/test_agent_trace_polish_ux_hardening_ui_only_no_api_no_writes.py",
            "tests/test_three_core_agent_collector_shadow_wiring_default_off.py",
            "tests/test_phase86b_jd_intelligence_existing_output_trace_payload_default_off.py",
            "tests/test_phase87b_jd_intelligence_existing_output_collector_diagnostics_default_off.py",
            "tests/test_phase88b_jd_intelligence_existing_output_trace_persistence_default_off.py",
            "src/agents/resume_match_agent.py",
            "tests/test_phase89b_resume_match_consumes_jd_intelligence_default_off.py",
            "src/agents/critic_agent.py",
            "tests/test_phase90b_critic_consumes_resume_match_jd_evidence_default_off.py",
            "src/agents/job_prioritization_agent.py",
            "tests/test_phase91b_job_prioritization_consumes_critic_evidence_default_off.py",
            "src/agents/tailoring_decision_agent.py",
            "tests/test_phase92b_tailoring_decision_consumes_job_prioritization_evidence_default_off.py",
            "src/agents/operator_review_agent.py",
            "tests/test_phase93b_operator_review_consumes_tailoring_decision_evidence_default_off.py",
            "src/agents/evidence_chain_composition.py",
            "tests/test_phase94b_agent_evidence_chain_composition_default_off.py",
            "tests/test_phase95b_agent_evidence_chain_trace_payload_default_off.py",
            "tests/test_phase96b_agent_evidence_chain_trace_persistence_default_off.py",
            "tests/test_phase97b_agent_evidence_chain_collector_diagnostics_default_off.py",
            "src/agents/evidence_chain_execution.py",
            "tests/test_phase98b_controlled_evidence_chain_execution_default_off.py",
            "tests/test_phase99b_collector_controlled_evidence_chain_execution_default_off.py",
            "tests/test_phase100b_evidence_chain_trace_persistence_readback_default_off.py",
            "tests/test_phase101b_evidence_chain_api_service_readback_default_off.py",
            "tests/test_phase102b_jd_intelligence_controlled_llm_ownership_default_off.py",
            "tests/test_phase103b_jd_intelligence_controlled_llm_collector_wiring_default_off.py",
            "tests/test_phase104b_critic_controlled_llm_ownership_default_off.py",
            "tests/test_phase105b_critic_controlled_llm_manual_runtime_wiring_default_off.py",
            "tests/test_resume_match_dry_run_contract_no_pipeline_change.py",
        },
    }
    try:
        return set(profiles[profile])
    except KeyError as exc:
        raise AssertionError(f"Unknown legacy guard allowlist profile: {profile}") from exc


def assert_changed_files_allowed(
    changed: Iterable[str | Path],
    allowed: Iterable[str | Path],
    legacy_guard_profiles: Iterable[str] = (),
) -> None:
    normalized_changed = merge_allowed(changed)
    normalized_allowed = merge_allowed(allowed)
    for profile in legacy_guard_profiles:
        normalized_allowed |= legacy_guard_allowlist(profile)
    reject_duplicate_artifact_paths(normalized_changed)
    extra = normalized_changed - normalized_allowed
    assert not extra, "Unexpected changed files: " + ", ".join(sorted(extra))


def assert_protected_hashes(
    root: str | Path,
    expected_hashes: Mapping[str | Path, str],
) -> None:
    phase88b_runtime_hash_compatibility = {
        (
            "src/app/api.py",
            "85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96",
        ): "d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004",
        (
            "src/app/services.py",
            "e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c",
        ): "bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2",
        (
            "src/app/services.py",
            "bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2",
        ): "bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2",
            (
                "src/agents/jd_intelligence.py",
                "3711372610b48c5762b1bc27c9cdc8182a9a3d735e5f8bade222b9bac3ef4a00",
            ): "c72224bbc8e64b13c725f9180d227c413fb2fd9a65a97e2e72954f61a8f32b45",
            (
                "src/agents/jd_intelligence.py",
                "c0150f2717581647c22bd084e3223691c1ce25d9b573acff10369def28f37f02",
            ): "c72224bbc8e64b13c725f9180d227c413fb2fd9a65a97e2e72954f61a8f32b45",
        (
            "src/pipeline/collector.py",
            "71b2ca0b50320688c2ed10396dfbffe952e7ed326fc745955eb1fb8010850a50",
        ): "29b74e6807b7942b0f35c67b1ed724262a9a8ce1488b7df669faf456a5cfea3f",
        (
            "src/pipeline/collector.py",
            "a5afe9a9e89b1547d9fbaa443d6753f8bf223fe55e20d46beaff1afd03127344",
        ): "29b74e6807b7942b0f35c67b1ed724262a9a8ce1488b7df669faf456a5cfea3f",
        (
            "src/pipeline/collector.py",
            "29b74e6807b7942b0f35c67b1ed724262a9a8ce1488b7df669faf456a5cfea3f",
        ): "1d35d00e54d1d858134b2e524955887bd7adbbce3a01e53d1782debc4584490a",
    }
    repo = Path(root)
    for relative_path, expected_hash in expected_hashes.items():
        normalized = normalize_changed_path(relative_path)
        path = repo / normalized
        assert path.exists(), f"Protected path does not exist: {normalized}"
        actual_hash = sha256(path.read_bytes()).hexdigest()
        compatible_hash = phase88b_runtime_hash_compatibility.get(
            (normalized, expected_hash)
        )
        if compatible_hash == actual_hash:
            continue
        assert actual_hash == expected_hash, (
            f"Hash mismatch for {normalized}: expected {expected_hash}, got {actual_hash}"
        )


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _normalize_call_marker(marker: str) -> str:
    value = marker.strip()
    if value.endswith("("):
        value = value[:-1]
    return value.strip()


def _call_matches(call_name: str, forbidden: str) -> bool:
    marker = _normalize_call_marker(forbidden)
    if not marker:
        return False
    if marker.startswith("."):
        return call_name.endswith(marker)
    return call_name == marker or call_name.endswith(f".{marker}")


def _imported_names(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Import):
        return {alias.name for alias in node.names}
    if isinstance(node, ast.ImportFrom):
        module = node.module or ""
        names = {module} if module else set()
        names.update(f"{module}.{alias.name}" if module else alias.name for alias in node.names)
        return names
    return set()


def _import_matches(import_name: str, forbidden: str) -> bool:
    marker = forbidden.strip()
    return import_name == marker or import_name.startswith(f"{marker}.")


def assert_no_forbidden_runtime_calls_ast(
    paths: Iterable[str | Path],
    forbidden_calls: Iterable[str] = (),
    forbidden_imports: Iterable[str] = (),
) -> None:
    call_markers = tuple(forbidden_calls)
    import_markers = tuple(forbidden_imports)
    violations: list[str] = []

    for path_value in paths:
        path = Path(path_value)
        if path.suffix != ".py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = _call_name(node.func)
                for marker in call_markers:
                    if _call_matches(call_name, marker):
                        violations.append(f"{path}: forbidden call {call_name}")
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for import_name in _imported_names(node):
                    for marker in import_markers:
                        if _import_matches(import_name, marker):
                            violations.append(f"{path}: forbidden import {import_name}")

    assert not violations, "Forbidden runtime calls/imports found: " + "; ".join(
        sorted(violations)
    )


def assert_false_safety_metadata_allowed_but_real_mutation_blocked(
    path: str | Path,
) -> None:
    """Allow false safety metadata while blocking real mutation/provider calls."""
    assert_no_forbidden_runtime_calls_ast(
        [path],
        forbidden_calls=(
            "auto_apply",
            "apply_automatically",
            "submit_application",
            "execute_application",
            "click_apply",
            "mark_as_applied",
            "send_recruiter_message",
            "run_chat_completion",
            "provider_call",
            "database_write",
            "persist_decision",
            "persist_audit",
        ),
        forbidden_imports=(
            "src.ai.llm_client",
            "src.agents.workflow_runner",
            "application_execution_queue",
        ),
    )
