from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import pytest

import batch_select_best_resume_variant as selector
from src.resume import document_store


def _result(name: str, score: float = 0.4):
    return SimpleNamespace(
        pair=SimpleNamespace(resume_name=name),
        prefilter=SimpleNamespace(
            missing_requirements=["missing requirement"],
            matched_terms=["python"],
            passed=False,
        ),
        final_score=score,
        match_bucket="weak",
        dimension_scores=[],
    )


def _enable_owner(monkeypatch, owner: str = "owner-a") -> None:
    monkeypatch.setenv("JOB_STACK_USER_PIPELINE_MODE", "true")
    monkeypatch.setenv("JOB_STACK_OWNER_USER_ID", owner)


def _route(workload_id: str, provider: str, model: str):
    return {
        "workload_id": workload_id,
        "provider": provider,
        "model": model,
        "effective_selection_source": "user_override",
    }


def test_authenticated_fallback_uses_exact_owner_route_and_runtime(monkeypatch):
    _enable_owner(monkeypatch, "owner-fallback")
    monkeypatch.setenv("GROQ_API_KEY", "global-groq-sentinel")
    monkeypatch.setenv("OPENAI_API_KEY", "global-openai-sentinel")
    monkeypatch.setattr(selector, "_build_llm_fallback_prompt", lambda **_kwargs: "prompt")
    monkeypatch.setattr(selector, "_load_llm_fallback_cache", lambda _key: None)
    monkeypatch.setattr(selector, "_write_llm_fallback_cache", lambda *_args: None)

    resolved = []
    executed = []

    def resolve(owner_user_id, workload_id):
        resolved.append((owner_user_id, workload_id))
        return _route(workload_id, "openai", "gpt-5-mini")

    def execute(**kwargs):
        executed.append(kwargs)
        return {
            "content": {
                "best_resume": "resume-a.pdf",
                "best_score": 0.4,
                "backup_resume": "",
                "backup_score": 0,
                "confidence": "low",
                "reason": "Best available option with missing requirement.",
            },
            "provider": "openai",
            "model": "gpt-5-mini",
            "fallback_used": False,
        }

    monkeypatch.setattr(
        selector,
        "_resolve_selector_effective_user_provider_route",
        resolve,
    )
    monkeypatch.setattr(
        selector,
        "_run_effective_selector_user_chat_completion_with_metadata",
        execute,
    )
    monkeypatch.setattr(
        selector,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("shared provider client must not be called"),
    )

    result = selector._run_llm_fallback_ranking(
        {},
        [_result("resume-a.pdf")],
        [],
    )

    assert resolved == [
        ("owner-fallback", selector.RESUME_FALLBACK_RANKING_WORKLOAD_ID)
    ]
    assert executed[0]["owner_user_id"] == "owner-fallback"
    assert executed[0]["workload_id"] == "resume_fallback_ranking"
    assert "provider" not in executed[0]
    assert "model" not in executed[0]
    assert "global-groq-sentinel" not in repr(executed)
    assert "global-openai-sentinel" not in repr(executed)
    assert result["provider"] == "openai"
    assert result["model"] == "gpt-5-mini"
    assert result["status"] == "generated"
    assert selector.os.environ["GROQ_API_KEY"] == "global-groq-sentinel"
    assert selector.os.environ["OPENAI_API_KEY"] == "global-openai-sentinel"


def test_authenticated_adjudication_uses_exact_owner_route_and_runtime(monkeypatch):
    _enable_owner(monkeypatch, "owner-adjudication")
    monkeypatch.setattr(selector, "_build_llm_adjudication_prompt", lambda **_kwargs: "prompt")
    monkeypatch.setattr(selector, "_load_llm_adjudication_cache", lambda _key: None)
    monkeypatch.setattr(selector, "_write_llm_adjudication_cache", lambda *_args: None)

    resolved = []
    executed = []

    def resolve(owner_user_id, workload_id):
        resolved.append((owner_user_id, workload_id))
        return _route(workload_id, "groq", "openai/gpt-oss-20b")

    def execute(**kwargs):
        executed.append(kwargs)
        return {
            "content": {
                "adjudicated_resume": "resume-b.pdf",
                "confidence": "medium",
                "reason": "Better supported evidence.",
            },
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
            "fallback_used": False,
        }

    monkeypatch.setattr(
        selector,
        "_resolve_selector_effective_user_provider_route",
        resolve,
    )
    monkeypatch.setattr(
        selector,
        "_run_effective_selector_user_chat_completion_with_metadata",
        execute,
    )
    monkeypatch.setattr(
        selector,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("shared provider client must not be called"),
    )

    result = selector._run_llm_adjudication(
        {},
        _result("resume-a.pdf", 0.5),
        _result("resume-b.pdf", 0.49),
        [],
    )

    assert resolved == [
        (
            "owner-adjudication",
            selector.AMBIGUOUS_RESUME_ADJUDICATION_WORKLOAD_ID,
        )
    ]
    assert executed[0]["owner_user_id"] == "owner-adjudication"
    assert executed[0]["workload_id"] == "ambiguous_resume_adjudication"
    assert result["provider"] == "groq"
    assert result["model"] == "openai/gpt-oss-20b"
    assert result["adjudicated_resume"] == "resume-b.pdf"


def test_authenticated_missing_owner_fails_closed_before_route_cache_or_provider(
    monkeypatch,
):
    monkeypatch.setenv("JOB_STACK_USER_PIPELINE_MODE", "true")
    monkeypatch.delenv("JOB_STACK_OWNER_USER_ID", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "global-groq-sentinel")
    monkeypatch.setenv("OPENAI_API_KEY", "global-openai-sentinel")
    monkeypatch.setattr(selector, "_build_llm_fallback_prompt", lambda **_kwargs: "prompt")
    monkeypatch.setattr(
        selector,
        "_resolve_selector_effective_user_provider_route",
        lambda *_args: pytest.fail("route lookup must require owner first"),
    )
    monkeypatch.setattr(
        selector,
        "_load_llm_fallback_cache",
        lambda _key: pytest.fail("cache lookup must require owner first"),
    )
    monkeypatch.setattr(
        selector,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("shared provider client must not be called"),
    )

    result = selector._run_llm_fallback_ranking(
        {},
        [_result("resume-a.pdf")],
        [],
    )

    assert result["status"] == "error"
    assert result["parse_ok"] is False
    assert result["provider"] == ""
    assert result["model"] == ""
    assert result["best_resume"] == ""
    assert "selector_owner_context_unavailable" in result["error_type"]
    assert selector.os.environ["GROQ_API_KEY"] == "global-groq-sentinel"
    assert selector.os.environ["OPENAI_API_KEY"] == "global-openai-sentinel"


@pytest.mark.parametrize("failure_stage", ("route", "credential"))
def test_authenticated_route_or_credential_failure_preserves_deterministic_authority(
    monkeypatch,
    failure_stage,
):
    _enable_owner(monkeypatch)
    monkeypatch.setattr(selector, "_build_llm_fallback_prompt", lambda **_kwargs: "prompt")
    monkeypatch.setattr(selector, "_load_llm_fallback_cache", lambda _key: None)
    monkeypatch.setattr(
        selector,
        "run_chat_completion",
        lambda **_kwargs: pytest.fail("shared provider client must not be called"),
    )
    if failure_stage == "route":
        monkeypatch.setattr(
            selector,
            "_resolve_selector_effective_user_provider_route",
            lambda *_args: (_ for _ in ()).throw(RuntimeError("route unavailable")),
        )
    else:
        monkeypatch.setattr(
            selector,
            "_resolve_selector_effective_user_provider_route",
            lambda _owner, workload: _route(workload, "groq", "qualified-model"),
        )
        monkeypatch.setattr(
            selector,
            "_run_effective_selector_user_chat_completion_with_metadata",
            lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("credential unavailable")),
        )

    llm_result = selector._run_llm_fallback_ranking(
        {},
        [_result("resume-a.pdf")],
        [],
    )
    projection = selector._resolved_selection_projection(
        results=[_result("resume-a.pdf")],
        selection_signal="no_credible_match",
        winner=None,
        runner_up=None,
        llm_fallback=llm_result,
        llm_adjudication={},
    )

    assert llm_result["status"] == "error"
    assert llm_result["best_resume"] == ""
    assert projection["resolved_selection_status"] == "unresolved"
    assert projection["resolved_resume"] == ""


def test_authenticated_cache_identity_is_owner_partitioned_without_raw_owner_ids(
    monkeypatch,
):
    _enable_owner(monkeypatch, "owner-a@example.test")
    monkeypatch.setattr(
        selector,
        "_resolve_selector_effective_user_provider_route",
        lambda _owner, workload: _route(workload, "groq", "qualified-model"),
    )
    context_a = selector._selector_llm_execution_context(
        workload_id=selector.RESUME_FALLBACK_RANKING_WORKLOAD_ID,
        legacy_provider="legacy",
        legacy_model="legacy-model",
    )
    monkeypatch.setenv("JOB_STACK_OWNER_USER_ID", "owner-b@example.test")
    context_b = selector._selector_llm_execution_context(
        workload_id=selector.RESUME_FALLBACK_RANKING_WORKLOAD_ID,
        legacy_provider="legacy",
        legacy_model="legacy-model",
    )

    fallback_a = selector._llm_fallback_cache_redis_key(
        selector._llm_fallback_cache_key(
            "groq", "qualified-model", "system", "prompt",
            owner_partition=context_a["cache_partition"],
        )
    )
    fallback_b = selector._llm_fallback_cache_redis_key(
        selector._llm_fallback_cache_key(
            "groq", "qualified-model", "system", "prompt",
            owner_partition=context_b["cache_partition"],
        )
    )
    adjudication_a = selector._llm_adjudication_cache_redis_key(
        selector._llm_adjudication_cache_key(
            "groq", "qualified-model", "system", "prompt",
            owner_partition=context_a["cache_partition"],
        )
    )
    adjudication_b = selector._llm_adjudication_cache_redis_key(
        selector._llm_adjudication_cache_key(
            "groq", "qualified-model", "system", "prompt",
            owner_partition=context_b["cache_partition"],
        )
    )

    assert fallback_a != fallback_b
    assert adjudication_a != adjudication_b
    for key in (fallback_a, fallback_b, adjudication_a, adjudication_b):
        assert "owner-a@example.test" not in key
        assert "owner-b@example.test" not in key


def test_legacy_selector_keeps_shared_client_failover_and_cache_identity(monkeypatch):
    monkeypatch.delenv("JOB_STACK_USER_PIPELINE_MODE", raising=False)
    monkeypatch.delenv("JOB_STACK_OWNER_USER_ID", raising=False)
    monkeypatch.setattr(selector, "_build_llm_fallback_prompt", lambda **_kwargs: "prompt")
    monkeypatch.setattr(selector, "_load_llm_fallback_cache", lambda _key: None)
    monkeypatch.setattr(selector, "_write_llm_fallback_cache", lambda *_args: None)
    monkeypatch.setattr(
        selector,
        "_resolve_selector_effective_user_provider_route",
        lambda *_args: pytest.fail("legacy execution must not resolve an owner route"),
    )
    monkeypatch.setattr(
        selector,
        "_selector_provider_failover_kwargs",
        lambda _provider: {
            "fallback_enabled": True,
            "fallback_provider": "openai",
            "fallback_model": "legacy-fallback-model",
        },
    )
    observed = {}

    def shared_completion(**kwargs):
        observed.update(kwargs)
        return {
            "best_resume": "resume-a.pdf",
            "best_score": 0.4,
            "backup_resume": "",
            "backup_score": 0,
            "confidence": "low",
            "reason": "Best available option.",
        }

    monkeypatch.setattr(selector, "run_chat_completion", shared_completion)
    result = selector._run_llm_fallback_ranking(
        {},
        [_result("resume-a.pdf")],
        [],
    )

    expected_legacy_payload = {
        "prompt_version": selector.LLM_FALLBACK_PROMPT_VERSION,
        "provider": selector.LLM_FALLBACK_PROVIDER,
        "model": selector.LLM_FALLBACK_MODEL,
        "system_prompt": selector.LLM_FALLBACK_SYSTEM_PROMPT,
        "prompt": "prompt",
    }
    expected_legacy_key = hashlib.sha256(
        json.dumps(
            expected_legacy_payload,
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()

    assert result["status"] == "generated"
    assert observed["provider"] == selector.LLM_FALLBACK_PROVIDER
    assert observed["model"] == selector.LLM_FALLBACK_MODEL
    assert observed["fallback_enabled"] is True
    assert selector._llm_fallback_cache_key(
        selector.LLM_FALLBACK_PROVIDER,
        selector.LLM_FALLBACK_MODEL,
        selector.LLM_FALLBACK_SYSTEM_PROMPT,
        "prompt",
    ) == expected_legacy_key


def test_authenticated_resume_loading_remains_owner_postgres_scoped(monkeypatch):
    _enable_owner(monkeypatch, "owner-resume")
    monkeypatch.setattr(
        document_store,
        "load_resumes",
        lambda: pytest.fail("legacy filesystem resumes must not be loaded"),
    )
    observed = []

    def owner_records(*, names=None):
        observed.append((document_store._owner_user_id_from_env(), names))
        return [
            {
                "resume_name": "owner-resume.pdf",
                "path": "",
                "raw_text": "Owner resume",
                "normalized_text": "Owner resume",
            }
        ]

    monkeypatch.setattr(
        document_store,
        "_load_profile_resume_records_from_postgres",
        owner_records,
    )

    documents = document_store.load_resume_documents()

    assert observed == [("owner-resume", None)]
    assert [document.resume_name for document in documents] == [
        "owner-resume.pdf"
    ]
