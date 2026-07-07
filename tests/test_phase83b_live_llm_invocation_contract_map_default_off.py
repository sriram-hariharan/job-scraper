from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


LLM_PATH_CLASSIFICATION = {
    "collector_skill_extraction": {
        "bucket": "live_pipeline_automatic_cache_first",
        "owner": "JD Intelligence Agent",
        "call_chain": [
            "src/pipeline/collector.py::build_job_intelligence",
            "src/intelligence/job_intelligence.py::enrich_skills_with_llm",
            "src/ai/skill_llm_enricher.py::run_chat_completion",
        ],
        "cache_gate": "SKILL_EXTRACTION_MODE",
        "must_reuse_existing_outputs": True,
        "duplicate_provider_call_allowed_by_default": False,
    },
    "collector_ai_job_fit_evaluation": {
        "bucket": "live_pipeline_automatic_cache_first",
        "owner": "Resume Match Agent",
        "call_chain": [
            "src/pipeline/collector.py::evaluate_jobs",
            "src/ai/job_fit_evaluator.py::evaluate_batch",
            "src/ai/job_fit_evaluator.py::run_chat_completion",
        ],
        "cache_gate": "EVAL_MODE",
        "must_reuse_existing_outputs": True,
        "duplicate_provider_call_allowed_by_default": False,
    },
    "rag_answerer": {
        "bucket": "rag_user_query_only",
        "owner": "Operator Review Agent",
        "hidden_scoring_or_ranking_call_allowed": False,
    },
    "tailoring_live_llm": {
        "bucket": "manual_api_tooling_triggered_tailoring",
        "owner": "Tailoring Decision Agent",
        "duplicate_provider_call_allowed_by_default": False,
        "tailoring_auto_apply_allowed": False,
    },
    "jd_default_off_provider_adapters": {
        "bucket": "dry_run_default_off_canary_or_injected_provider",
        "owner": "JD Intelligence Agent",
        "default_off": True,
        "requires_provider_injection_or_explicit_enable": True,
    },
    "phase79_82_advisory_chain": {
        "bucket": "default_off_read_only_advisory_chain",
        "owner": "Operator Review Agent",
        "llm_provider_call_allowed": False,
        "live_provider_allowed": False,
        "provider_runtime_not_invoked": True,
    },
}


FUTURE_AGENT_OWNERSHIP_CONTRACT = {
    "JD Intelligence Agent": {
        "owns_or_consumes": [
            "existing JD intelligence",
            "skills",
            "role family",
            "visa signals",
        ],
        "reuse_existing_skill_extraction_cache_first": True,
        "new_provider_call_allowed_by_default": False,
    },
    "Relevance/Prefilter Agent": {
        "owns_or_consumes": [
            "deterministic filters",
            "vector relevance",
            "JD intelligence",
        ],
        "new_provider_call_allowed_by_default": False,
    },
    "Resume Match Agent": {
        "owns_or_consumes": [
            "resume/job match evidence",
            "existing AI fit fields",
        ],
        "duplicate_llm_evaluation_allowed_by_default": False,
    },
    "Critic Agent": {
        "owns_or_consumes": [
            "existing evaluation reasons",
            "fit scores",
            "tailoring evidence",
            "trace metadata",
        ],
        "future_llm_critic_requires_separate_default_off_gate": True,
    },
    "Job Prioritization Agent": {
        "owns_or_consumes": [
            "existing ranking",
            "priority",
            "evaluation fields",
        ],
        "may_mutate_scoring_or_ranking_in_phase83b": False,
    },
    "Tailoring Decision Agent": {
        "owns_or_consumes": [
            "tailoring packets",
            "previews",
            "live tailoring outputs only if already produced",
        ],
        "duplicate_rewrite_call_allowed_by_default": False,
        "tailoring_auto_apply_allowed": False,
    },
    "Operator Review Agent": {
        "owns_or_consumes": [
            "recommendation",
            "action",
            "status fields",
            "trace readback",
        ],
        "provider_call_allowed": False,
        "application_submission_allowed": False,
    },
}


SAFETY_INVARIANTS = {
    "auto_apply_allowed": False,
    "ats_submission_allowed": False,
    "apply_click_allowed": False,
    "recruiter_messaging_allowed": False,
    "mark_as_applied_allowed": False,
    "workflow_runner_live_execution_allowed": False,
    "scoring_mutation_allowed": False,
    "ranking_mutation_allowed": False,
    "filtering_mutation_allowed": False,
    "queue_mutation_allowed": False,
    "scheduler_mutation_allowed": False,
    "source_resume_mutation_allowed": False,
    "tailoring_auto_apply_allowed": False,
}


def test_central_llm_client_owns_direct_provider_sdk_boundaries():
    llm_client = _read("src/ai/llm_client.py")
    direct_provider_tokens = [
        "from groq import Groq",
        "from openai import OpenAI",
        "from google import genai",
        "Groq(api_key=groq_api_key)",
        "OpenAI(api_key=openai_api_key)",
        "genai.Client(api_key=gemini_api_key)",
        "client.chat.completions.create(",
        "client.models.generate_content(",
        "def run_chat_completion_with_metadata(",
        "def run_chat_completion(",
    ]
    for token in direct_provider_tokens:
        assert token in llm_client

    direct_sdk_imports = [
        "from groq import Groq",
        "from openai import OpenAI",
        "from google import genai",
        "Groq(",
        "OpenAI(",
        "genai.Client(",
    ]
    for path in [
        "src/ai/skill_llm_enricher.py",
        "src/ai/job_fit_evaluator.py",
        "src/rag/rag_answerer.py",
        "src/tailoring/llm.py",
        "src/pipeline/collector.py",
    ]:
        text = _read(path)
        for token in direct_sdk_imports:
            assert token not in text


def test_collector_automatic_llm_capable_paths_are_cache_first_contracts():
    collector = _read("src/pipeline/collector.py")
    job_intelligence = _read("src/intelligence/job_intelligence.py")
    skill_enricher = _read("src/ai/skill_llm_enricher.py")
    job_fit = _read("src/ai/job_fit_evaluator.py")

    assert "from src.ai.skill_llm_enricher import enrich_skills_with_llm" in job_intelligence
    assert "llm_result = enrich_skills_with_llm(description)" in job_intelligence
    assert "from src.ai.llm_client import run_chat_completion" in skill_enricher
    assert "response = run_chat_completion(" in skill_enricher
    assert "retry_response = run_chat_completion(" in skill_enricher
    assert 'SKILL_EXTRACTION_MODE = os.getenv("SKILL_EXTRACTION_MODE", "cache_prefer_live")' in skill_enricher
    assert 'VALID_EXTRACTION_MODES = {"cache_prefer_live", "cache_only", "live_only"}' in skill_enricher

    assert "from src.ai.llm_client import run_chat_completion, get_default_model" in job_fit
    assert "response = run_chat_completion(" in job_fit
    assert 'EVAL_MODE = os.getenv("EVAL_MODE", "cache_prefer_live")' in job_fit
    assert 'VALID_EVAL_MODES = {"cache_prefer_live", "cache_only", "live_only"}' in job_fit

    assert "build_job_intelligence," in collector
    assert "intelligent_jobs = [build_job_intelligence(job) for job in detailed_jobs]" in collector
    assert "from src.ai.job_fit_evaluator import evaluate_jobs" in collector
    assert "ai_jobs = evaluate_jobs(evaluable_jobs)" in collector

    assert (
        LLM_PATH_CLASSIFICATION["collector_skill_extraction"]["bucket"]
        == "live_pipeline_automatic_cache_first"
    )
    assert (
        LLM_PATH_CLASSIFICATION["collector_ai_job_fit_evaluation"]["bucket"]
        == "live_pipeline_automatic_cache_first"
    )
    assert LLM_PATH_CLASSIFICATION["collector_skill_extraction"]["cache_gate"] == "SKILL_EXTRACTION_MODE"
    assert LLM_PATH_CLASSIFICATION["collector_ai_job_fit_evaluation"]["cache_gate"] == "EVAL_MODE"


def test_non_collector_paths_are_classified_as_manual_or_user_query_only():
    rag_answerer = _read("src/rag/rag_answerer.py")
    tailoring_llm = _read("src/tailoring/llm.py")
    collector = _read("src/pipeline/collector.py")

    assert "from src.ai.llm_client import run_chat_completion_with_metadata" in rag_answerer
    assert "run_chat_completion_with_metadata," in rag_answerer
    assert "_run_chat_completion_with_timeout(" in rag_answerer
    assert LLM_PATH_CLASSIFICATION["rag_answerer"]["bucket"] == "rag_user_query_only"
    assert (
        LLM_PATH_CLASSIFICATION["rag_answerer"]["hidden_scoring_or_ranking_call_allowed"]
        is False
    )

    assert "run_chat_completion_with_metadata" in tailoring_llm
    assert "def _run_live_llm_tailoring(" in tailoring_llm
    assert LLM_PATH_CLASSIFICATION["tailoring_live_llm"]["bucket"] == (
        "manual_api_tooling_triggered_tailoring"
    )
    assert (
        LLM_PATH_CLASSIFICATION["tailoring_live_llm"]["tailoring_auto_apply_allowed"]
        is False
    )

    assert "rag_answerer" not in collector
    assert "answer_job_query" not in collector
    assert "_run_live_llm_tailoring" not in collector


def test_default_off_or_injected_provider_paths_remain_explicitly_gated():
    jd_extractor = _read("src/agents/jd_intelligence_llm_signal_extractor_default_off.py")
    jd_enricher = _read("src/agents/jd_intelligence_planning_artifact_enricher_default_off.py")
    canary = _read("src/agents/jd_live_provider_canary.py")
    external_adapter = _read("src/agents/jd_live_provider_external_adapter.py")
    runtime_adapter = _read("src/agents/provider_runtime_adapter.py")

    assert "enable_llm: bool = False" in jd_extractor
    assert "provider_callable: Any = None" in jd_extractor
    assert "elif provider_callable_present:" in jd_extractor
    assert '"llm_enabled": llm_enabled' in jd_extractor
    assert '"provider_callable_invoked": provider_callable_invoked' in jd_extractor

    assert "enable_llm: bool = False" in jd_enricher
    assert "provider_callable: Any = None" in jd_enricher
    assert "enable_llm=llm_enabled" in jd_enricher

    assert "def run_jd_live_provider_canary(" in canary
    assert "enabled: bool = False" in canary
    assert "provider_adapter: Callable[[dict[str, Any]], Any] | None = None" in canary
    assert "evaluate_provider_live_config_gate(" in canary

    assert "def invoke_jd_live_provider_external_adapter(" in external_adapter
    assert "enabled: bool = False" in external_adapter
    assert "external_adapter: Callable[[dict[str, Any]], Any] | None = None" in external_adapter
    assert '"external_adapter_invoked": False' in external_adapter

    assert "def run_provider_runtime_adapter(" in runtime_adapter
    assert "enabled: bool = False" in runtime_adapter
    assert "provider_callable: Callable[[dict[str, Any]], Any] | None = None" in runtime_adapter
    assert '"provider_call_attempted": False' in runtime_adapter

    contract = LLM_PATH_CLASSIFICATION["jd_default_off_provider_adapters"]
    assert contract["default_off"] is True
    assert contract["requires_provider_injection_or_explicit_enable"] is True


def test_advisory_chain_sidecar_does_not_introduce_llm_or_provider_calls():
    harness = _read("src/agents/orchestrator_adapter_harness.py")
    collector = _read("src/pipeline/collector.py")
    advisory_modules = [
        "src/agents/orchestrator_adapter_harness.py",
        "src/agents/orchestrator_adapters.py",
        "src/agents/read_only_adapter_chain.py",
    ]

    for path in advisory_modules:
        text = _read(path)
        assert "run_chat_completion(" not in text
        assert "run_chat_completion_with_metadata(" not in text
        assert "from groq import Groq" not in text
        assert "from openai import OpenAI" not in text
        assert "from google import genai" not in text

    assert "ADVISORY_CHAIN_FALSE_FLAGS" in harness
    assert '"llm_provider_call_allowed"' in harness
    assert '"live_provider_allowed"' in harness
    assert '"workflow_runner_live_execution_allowed"' in harness
    assert '"did_call_llm": False' in harness
    assert '"did_call_live_provider": False' in harness
    assert '"did_call_workflow_runner": False' in harness

    sidecar_region = collector[
        collector.index("def _maybe_invoke_advisory_chain_diagnostics_after_application_priority"):
        collector.index("def log_market_insights")
    ]
    assert "run_chat_completion" not in sidecar_region
    assert "invoke_read_only_advisory_chain_from_pipeline_boundary" in sidecar_region
    assert "persist_read_only_advisory_chain_trace" in sidecar_region

    contract = LLM_PATH_CLASSIFICATION["phase79_82_advisory_chain"]
    assert contract["llm_provider_call_allowed"] is False
    assert contract["live_provider_allowed"] is False
    assert contract["provider_runtime_not_invoked"] is True


def test_future_agent_contract_map_prevents_duplicate_default_provider_calls():
    assert FUTURE_AGENT_OWNERSHIP_CONTRACT["JD Intelligence Agent"][
        "reuse_existing_skill_extraction_cache_first"
    ] is True
    assert FUTURE_AGENT_OWNERSHIP_CONTRACT["JD Intelligence Agent"][
        "new_provider_call_allowed_by_default"
    ] is False
    assert FUTURE_AGENT_OWNERSHIP_CONTRACT["Resume Match Agent"][
        "duplicate_llm_evaluation_allowed_by_default"
    ] is False
    assert FUTURE_AGENT_OWNERSHIP_CONTRACT["Critic Agent"][
        "future_llm_critic_requires_separate_default_off_gate"
    ] is True
    assert FUTURE_AGENT_OWNERSHIP_CONTRACT["Job Prioritization Agent"][
        "may_mutate_scoring_or_ranking_in_phase83b"
    ] is False
    assert FUTURE_AGENT_OWNERSHIP_CONTRACT["Tailoring Decision Agent"][
        "duplicate_rewrite_call_allowed_by_default"
    ] is False
    assert FUTURE_AGENT_OWNERSHIP_CONTRACT["Operator Review Agent"][
        "application_submission_allowed"
    ] is False

    for agent_contract in FUTURE_AGENT_OWNERSHIP_CONTRACT.values():
        assert agent_contract["owns_or_consumes"]


def test_duplicate_call_risk_rules_and_safety_invariants_are_encoded():
    assert LLM_PATH_CLASSIFICATION["collector_skill_extraction"][
        "duplicate_provider_call_allowed_by_default"
    ] is False
    assert LLM_PATH_CLASSIFICATION["collector_ai_job_fit_evaluation"][
        "duplicate_provider_call_allowed_by_default"
    ] is False
    assert LLM_PATH_CLASSIFICATION["tailoring_live_llm"][
        "duplicate_provider_call_allowed_by_default"
    ] is False
    assert LLM_PATH_CLASSIFICATION["rag_answerer"][
        "hidden_scoring_or_ranking_call_allowed"
    ] is False

    assert all(value is False for value in SAFETY_INVARIANTS.values())
