from __future__ import annotations

from copy import deepcopy
import inspect
import sys
import types

import pytest

import generate_tailoring_suggestions as caller
from src.agents import tailoring_generation_authoritative_graph as graph_owner


GRAPH_MODULE = "src.agents.tailoring_generation_authoritative_graph"
GATE = "APPLYLENS_AUTHORITATIVE_TAILORING_GENERATION_LANGGRAPH_ENABLED"


def _packet() -> dict:
    return {
        "job_doc_id": "job-phase17c",
        "selected_resume": "resume.pdf",
        "job": {"company": "ExampleCo", "title": "Analytics Engineer"},
    }


def _payload() -> dict:
    return {
        "job": {"company": "ExampleCo", "title": "Analytics Engineer"},
        "selection": {"selected_resume": "resume.pdf"},
        "live_rewrite_prompt": "bounded synthetic prompt",
        "evidence_layers": {"anchors": [], "supports": [], "context": []},
    }


def _result(**overrides) -> dict:
    result = {
        "parse_ok": True,
        "parse_error": "",
        "retry_used": False,
        "cache_hit": False,
        "requested_provider": "groq",
        "requested_model": "test-model",
        "resolved_provider": "groq",
        "resolved_model": "test-model",
        "fallback_used": False,
        "raw_response": '{"rewrite_directions":[]}',
        "retry_raw_response": "",
        "parsed": {
            "rewrite_directions": [],
            "invalid_concrete_replacement_candidates": [],
        },
        "concrete_replacement_candidates_requested": False,
    }
    result.update(overrides)
    return result


def _owner_result(result: dict | None = None, calls: list | None = None):
    expected = deepcopy(result if result is not None else _result())

    def owner(**kwargs):
        if calls is not None:
            calls.append(deepcopy(kwargs))
        return deepcopy(expected)

    return owner


def _execute(*, owner=None, packet=None, payload=None, **kwargs) -> dict:
    return graph_owner.execute_authoritative_tailoring_generation_graph(
        packet=packet if packet is not None else _packet(),
        payload=payload if payload is not None else _payload(),
        run_tailoring_func=owner or _owner_result(),
        pipeline_run_id="run-phase17c",
        owner_user_id="owner-phase17c",
        context_id="context-phase17c",
        **kwargs,
    )


def test_exact_graph_and_state_versions():
    assert (
        graph_owner.AUTHORITATIVE_TAILORING_GENERATION_GRAPH_VERSION
        == "authoritative-tailoring-generation-graph-v1"
    )
    assert (
        graph_owner.AUTHORITATIVE_TAILORING_GENERATION_STATE_VERSION
        == "authoritative-tailoring-generation-state-v1"
    )


def test_real_state_graph_has_exactly_one_production_node():
    graph = graph_owner.build_authoritative_tailoring_generation_graph(
        run_tailoring_func=_owner_result()
    )

    assert type(graph).__name__ == "StateGraph"
    assert set(graph.nodes) == {"tailoring_generation"}
    assert (
        graph_owner.AUTHORITATIVE_TAILORING_GENERATION_PRODUCTION_NODE_COUNT
        == 1
    )


def test_graph_order_is_start_tailoring_generation_end():
    graph = graph_owner.build_authoritative_tailoring_generation_graph(
        run_tailoring_func=_owner_result()
    )

    assert graph.edges == {
        ("__start__", "tailoring_generation"),
        ("tailoring_generation", "__end__"),
    }


def test_activation_gate_defaults_off():
    for value in (None, "", "0", "false", "FALSE", "no", "off"):
        env = {} if value is None else {GATE: value}
        assert (
            caller._authoritative_tailoring_generation_langgraph_enabled(env)
            is False
        )


def test_activation_gate_uses_existing_truthy_convention():
    for value in ("1", "true", "TRUE", "yes", "on"):
        assert (
            caller._authoritative_tailoring_generation_langgraph_enabled(
                {GATE: value}
            )
            is True
        )


def test_gate_off_uses_direct_owner_once_without_graph_import(monkeypatch):
    monkeypatch.delitem(sys.modules, GRAPH_MODULE, raising=False)
    calls = []
    owner = _owner_result(calls=calls)
    graph_result = (
        caller._maybe_execute_authoritative_tailoring_generation_graph(
            packet=_packet(),
            payload=_payload(),
            run_tailoring_func=owner,
            env={},
        )
    )
    output = owner(packet=_packet(), payload=_payload()) if graph_result is None else None

    assert output == _result()
    assert len(calls) == 1
    assert GRAPH_MODULE not in sys.modules


def test_gate_on_lazily_invokes_graph_and_owner_once(monkeypatch):
    graph_calls = []
    owner_calls = []

    def execute(**kwargs):
        graph_calls.append(deepcopy(kwargs))
        output = kwargs["run_tailoring_func"](
            packet=kwargs["packet"],
            payload=kwargs["payload"],
        )
        return {
            "tailoring_result": output,
            "execution_metadata": {
                "execution_mode": "langgraph",
                "production_node_count": 1,
                "node_invocation_count": 1,
                "tailoring_owner_invocation_count": 1,
                "critic_invocation_count": 0,
                "status": "completed",
            },
        }

    monkeypatch.setitem(
        sys.modules,
        GRAPH_MODULE,
        types.SimpleNamespace(
            execute_authoritative_tailoring_generation_graph=execute
        ),
    )
    result = caller._maybe_execute_authoritative_tailoring_generation_graph(
        packet=_packet(),
        payload=_payload(),
        run_tailoring_func=_owner_result(calls=owner_calls),
        env={
            GATE: "1",
            "JOB_APP_PIPELINE_RUN_ID": "run-17c",
            "JOB_STACK_OWNER_USER_ID": "owner-17c",
        },
    )

    assert result["tailoring_result"] == _result()
    assert len(graph_calls) == 1
    assert len(owner_calls) == 1
    assert graph_calls[0]["context_id"] == "tailoring_generation:run-17c"


def test_llm_disabled_main_performs_no_graph_or_owner_work(monkeypatch):
    payload = {
        **_payload(),
        "recruiter_summary": "",
        "keep_emphasize": [],
        "tailoring_actions": [],
        "do_not_claim": [],
    }
    calls = []
    monkeypatch.setattr(sys, "argv", ["generate", "--packet-json", "packet.json"])
    monkeypatch.setattr(caller, "_load_packet", lambda _path: _packet())
    monkeypatch.setattr(
        caller,
        "_build_payload",
        lambda _packet_value, include_llm_prompts: deepcopy(payload),
    )
    monkeypatch.setattr(
        caller,
        "_build_operator_markdown_payload",
        lambda value, _llm, **_kwargs: deepcopy(value),
    )
    monkeypatch.setattr(caller, "_markdown_from_payload", lambda _value: "")
    monkeypatch.setattr(caller, "_print_rewrite_ideas_console", lambda _value: None)
    monkeypatch.setitem(
        sys.modules,
        "src.tailoring.llm",
        types.SimpleNamespace(
            _run_live_llm_tailoring=lambda **_kwargs: calls.append("owner")
        ),
    )
    monkeypatch.setenv(GATE, "1")

    caller.main()

    assert calls == []


def test_graph_invokes_production_owner_exactly_once():
    calls = []
    result = _execute(owner=_owner_result(calls=calls))

    assert len(calls) == 1
    assert result["execution_metadata"]["node_invocation_count"] == 1
    assert result["execution_metadata"]["tailoring_owner_invocation_count"] == 1


def test_direct_and_graph_outputs_are_identical():
    direct = _owner_result()(
        packet=_packet(),
        payload=_payload(),
        output_llm_json="",
        refresh_llm_cache=False,
        enable_safe_app_ready_rewrite_promotion=False,
    )
    graph = _execute()["tailoring_result"]

    assert graph == direct


def test_graph_deep_copies_and_preserves_caller_inputs():
    packet = _packet()
    payload = _payload()
    packet_before = deepcopy(packet)
    payload_before = deepcopy(payload)

    def mutating_owner(**kwargs):
        kwargs["packet"]["job_doc_id"] = "mutated"
        kwargs["payload"]["live_rewrite_prompt"] = "mutated"
        return _result()

    _execute(owner=mutating_owner, packet=packet, payload=payload)

    assert packet == packet_before
    assert payload == payload_before


def test_raw_provider_responses_and_generated_content_are_not_metadata():
    metadata = _execute()["execution_metadata"]

    assert "raw_response" not in metadata
    assert "retry_raw_response" not in metadata
    assert "parsed" not in metadata
    assert metadata["generated_content_retained_in_state"] is False
    assert metadata["raw_provider_response_retained_in_state"] is False


def test_graph_state_retains_no_owner_result():
    holder = {}
    graph = graph_owner.build_authoritative_tailoring_generation_graph(
        run_tailoring_func=_owner_result(),
        result_holder=holder,
    )
    final_state = graph.compile().invoke(
        {
            "tailoring_packet": _packet(),
            "tailoring_payload": _payload(),
        }
    )

    assert holder["tailoring_result"] == _result()
    assert "tailoring_result" not in final_state
    assert "raw_response" not in final_state
    assert "parsed" not in final_state


def test_provider_and_model_metadata_are_bounded():
    long_value = "provider\n" + ("x" * 200)
    metadata = _execute(
        owner=_owner_result(
            _result(
                requested_provider=long_value,
                requested_model=long_value,
                resolved_provider=long_value,
                resolved_model=long_value,
            )
        )
    )["execution_metadata"]

    for key in (
        "requested_provider",
        "requested_model",
        "resolved_provider",
        "resolved_model",
    ):
        assert "\n" not in metadata[key]
        assert len(metadata[key]) <= 128


def test_cache_hit_metadata_preserves_owner_result():
    result = _execute(owner=_owner_result(_result(cache_hit=True)))

    assert result["tailoring_result"]["cache_hit"] is True
    assert result["execution_metadata"]["cache_hit"] is True
    assert result["execution_metadata"]["owner_managed_cache_first"] is True


def test_cache_miss_metadata_preserves_owner_result():
    result = _execute(owner=_owner_result(_result(cache_hit=False)))

    assert result["tailoring_result"]["cache_hit"] is False
    assert result["execution_metadata"]["cache_hit"] is False


def test_cache_and_exact_change_arguments_reach_owner_unchanged():
    calls = []
    _execute(
        owner=_owner_result(calls=calls),
        output_llm_json="/tmp/synthetic-tailoring-cache.json",
        refresh_llm_cache=True,
        enable_safe_app_ready_rewrite_promotion=True,
    )

    assert calls[0]["output_llm_json"] == "/tmp/synthetic-tailoring-cache.json"
    assert calls[0]["refresh_llm_cache"] is True
    assert calls[0]["enable_safe_app_ready_rewrite_promotion"] is True


def test_cache_path_is_not_retained_in_execution_metadata():
    metadata = _execute(
        output_llm_json="/tmp/private/synthetic-tailoring-cache.json"
    )["execution_metadata"]

    assert "/tmp/" not in repr(metadata)
    assert "output_llm_json" not in metadata


def test_provider_failure_preserves_output_and_is_bounded():
    owner_output = _result(
        parse_ok=False,
        parse_error="Primary LLM call failed: synthetic timeout detail",
        parsed={},
    )
    result = _execute(owner=_owner_result(owner_output))

    assert result["tailoring_result"] == owner_output
    assert result["execution_metadata"]["failure_classification"] == "provider_failure"


def test_structured_validation_failure_preserves_output_and_is_bounded():
    owner_output = _result(
        parse_ok=False,
        parse_error="Primary parse failed; retry parse failed",
        retry_used=True,
        parsed={},
    )
    result = _execute(owner=_owner_result(owner_output))

    assert result["tailoring_result"] == owner_output
    assert (
        result["execution_metadata"]["failure_classification"]
        == "structured_validation_failure"
    )


def test_retry_state_is_observed_without_graph_retry():
    calls = []
    metadata = _execute(
        owner=_owner_result(_result(retry_used=True), calls=calls)
    )["execution_metadata"]

    assert metadata["retry_used"] is True
    assert len(calls) == 1


def test_exact_change_remains_embedded_and_has_no_separate_invocation():
    metadata = _execute(
        owner=_owner_result(
            _result(concrete_replacement_candidates_requested=True)
        )
    )["execution_metadata"]

    assert metadata["exact_change_embedded_in_tailoring_stage"] is True
    assert metadata["exact_change_owner_invocation_count"] == 0


def test_deterministic_critic_is_not_a_graph_node_or_invocation():
    graph = graph_owner.build_authoritative_tailoring_generation_graph(
        run_tailoring_func=_owner_result()
    )
    metadata = _execute()["execution_metadata"]

    assert set(graph.nodes) == {"tailoring_generation"}
    assert metadata["critic_invocation_count"] == 0
    source = inspect.getsource(graph_owner)
    assert "critic_agent" not in source
    assert "evaluate_critic_suggestion" not in source


def test_graph_declares_no_mutation_application_ats_or_persistence_authority():
    metadata = _execute()["execution_metadata"]

    assert metadata["graph_persistence_authority"] is False
    assert metadata["mutation_authority"] is False
    assert metadata["application_authority"] is False
    assert metadata["ats_authority"] is False


def test_unsupported_claim_rejection_output_is_unchanged():
    owner_output = _result(
        parsed={
            "rewrite_directions": [],
            "concrete_replacement_candidates": [],
            "invalid_concrete_replacement_candidates": [
                {
                    "source_bullet_id": "bullet-1",
                    "validation_reason": "unsupported_claim",
                }
            ],
        }
    )

    assert _execute(owner=_owner_result(owner_output))["tailoring_result"] == owner_output


def test_graph_failure_does_not_trigger_direct_fallback(monkeypatch):
    owner_calls = []

    def execute(**_kwargs):
        raise RuntimeError("synthetic_graph_failure")

    monkeypatch.setitem(
        sys.modules,
        GRAPH_MODULE,
        types.SimpleNamespace(
            execute_authoritative_tailoring_generation_graph=execute
        ),
    )
    with pytest.raises(RuntimeError, match="synthetic_graph_failure"):
        caller._maybe_execute_authoritative_tailoring_generation_graph(
            packet=_packet(),
            payload=_payload(),
            run_tailoring_func=_owner_result(calls=owner_calls),
            env={GATE: "1"},
        )

    assert owner_calls == []


def test_invalid_owner_output_fails_closed():
    with pytest.raises(
        TypeError,
        match="owner_output_must_be_mapping",
    ):
        _execute(owner=lambda **_kwargs: [])


def test_missing_parse_contract_fails_closed():
    with pytest.raises(
        TypeError,
        match="parse_ok_must_be_bool",
    ):
        _execute(owner=lambda **_kwargs: {"cache_hit": False})


def test_operator_review_handoff_input_has_direct_graph_parity():
    owner = _owner_result()
    direct = owner(packet=_packet(), payload=_payload())
    graph = _execute(owner=owner)["tailoring_result"]

    def handoff(value):
        return deepcopy(value["parsed"])

    assert handoff(graph) == handoff(direct)


def test_graph_import_boundary_has_no_provider_cache_or_persistence_owner():
    source = inspect.getsource(graph_owner)

    assert "src.ai.llm_client" not in source
    assert "src.tailoring.llm" not in source
    assert "load_dotenv" not in source
    assert "write_text" not in source
    assert "run_chat_completion" not in source
