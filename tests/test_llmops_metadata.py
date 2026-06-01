from src.agents import llmops


def test_llmops_metadata_returns_stable_required_keys():
    metadata = llmops.build_llmops_metadata(
        model_provider="openai",
        model_name="gpt-test",
        prompt_version="prompt_v1",
        agent_name="Test Agent",
        agent_version="v1",
        input_token_count=10,
        output_token_count=15,
        latency_ms=123,
        retry_count=1,
        fallback_used=True,
        schema_validation_status="passed",
    )

    assert list(metadata.keys()) == llmops.LLMOPS_METADATA_KEYS
    assert metadata["metadata_version"] == "llmops_metadata_v1"
    assert metadata["total_token_count"] == 25
    assert metadata["estimated_cost"] == 0
    assert metadata["cost_currency"] == ""
    assert metadata["cost_reason"] == "no_rate_table_configured"


def test_llmops_metadata_missing_values_default_safely():
    metadata = llmops.build_llmops_metadata()

    assert metadata["model_provider"] == ""
    assert metadata["model_name"] == ""
    assert metadata["input_token_count"] == 0
    assert metadata["output_token_count"] == 0
    assert metadata["total_token_count"] == 0
    assert metadata["latency_ms"] is None
    assert metadata["fallback_used"] is False


def test_llmops_merge_populates_agent_step_kwargs():
    metadata = llmops.build_llmops_metadata(
        model_provider="groq",
        model_name="llama-test",
        input_token_count=100,
        output_token_count=40,
        latency_ms=250,
    )
    merged = llmops.merge_llmops_into_agent_step_kwargs(
        {"agent_name": "Example Agent", "status": "running"},
        metadata,
    )

    assert merged["agent_name"] == "Example Agent"
    assert merged["model_provider"] == "groq"
    assert merged["model_name"] == "llama-test"
    assert merged["latency_ms"] == 250
    assert merged["token_usage_json"] == {
        "metadata_version": "llmops_metadata_v1",
        "input_token_count": 100,
        "output_token_count": 40,
        "total_token_count": 140,
    }
    assert merged["cost_json"]["estimated_cost"] == 0
    assert merged["cost_json"]["cost_reason"] == "no_rate_table_configured"


def test_llmops_summary_sums_tokens_and_counts_models():
    rows = [
        llmops.build_llmops_metadata(
            model_provider="openai",
            model_name="gpt-a",
            input_token_count=10,
            output_token_count=5,
        ),
        {
            "model_provider": "openai",
            "model_name": "gpt-a",
            "token_usage_json": {
                "input_token_count": 7,
                "output_token_count": 3,
                "total_token_count": 10,
            },
            "cost_json": {"estimated_cost": 0},
        },
        {
            "model_provider": "groq",
            "model_name": "llama-b",
            "token_usage_json": {"prompt_tokens": 4, "completion_tokens": 6},
        },
    ]

    summary = llmops.summarize_llmops_metadata(rows)

    assert summary["row_count"] == 3
    assert summary["input_token_count"] == 21
    assert summary["output_token_count"] == 14
    assert summary["total_token_count"] == 35
    assert summary["estimated_cost"] == 0
    assert summary["provider_counts"] == {"groq": 1, "openai": 2}
    assert summary["model_counts"] == {"gpt-a": 2, "llama-b": 1}


def test_llmops_schema_readiness_payload():
    payload = llmops.llmops_schema_readiness_payload()

    assert payload["metadata_version"] == "llmops_metadata_v1"
    assert payload["required_keys_present"] is True
    assert "model_provider" in payload["required_keys"]
    assert "total_token_count" in payload["required_keys"]
