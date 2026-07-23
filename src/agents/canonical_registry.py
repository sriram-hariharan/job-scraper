from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True)
class CanonicalAgentDefinition:
    key: str
    display_name: str
    owner_module: str
    responsibility: str
    deterministic_core: bool
    llm_capable: bool
    optional_controlled_llm_guardrail: bool
    advisory_only: bool
    human_approval_required: bool
    score_mutation: bool
    rank_mutation: bool
    queue_mutation: bool
    resume_text_mutation: bool
    operator_state_persistence: bool
    application_action_capability: bool


CANONICAL_AGENT_DEFINITIONS = (
    CanonicalAgentDefinition(
        key="critic",
        display_name="Critic Agent",
        owner_module="src.agents.critic_agent",
        responsibility=(
            "Evaluate existing resume-match and JD evidence for unsupported claims, "
            "contradictions, and review risk."
        ),
        deterministic_core=True,
        llm_capable=True,
        optional_controlled_llm_guardrail=True,
        advisory_only=True,
        human_approval_required=False,
        score_mutation=False,
        rank_mutation=False,
        queue_mutation=False,
        resume_text_mutation=False,
        operator_state_persistence=False,
        application_action_capability=False,
    ),
    CanonicalAgentDefinition(
        key="job_prioritization",
        display_name="Job Prioritization Agent",
        owner_module="src.agents.job_prioritization_agent",
        responsibility=(
            "Recommend an advisory job-priority posture from existing critic, "
            "resume-match, and JD evidence."
        ),
        deterministic_core=True,
        llm_capable=False,
        optional_controlled_llm_guardrail=False,
        advisory_only=True,
        human_approval_required=False,
        score_mutation=False,
        rank_mutation=False,
        queue_mutation=False,
        resume_text_mutation=False,
        operator_state_persistence=False,
        application_action_capability=False,
    ),
    CanonicalAgentDefinition(
        key="tailoring_decision",
        display_name="Tailoring Decision Agent",
        owner_module="src.agents.tailoring_decision_agent",
        responsibility=(
            "Recommend whether and how strongly to tailor from existing priority "
            "and evidence artifacts."
        ),
        deterministic_core=True,
        llm_capable=False,
        optional_controlled_llm_guardrail=False,
        advisory_only=True,
        human_approval_required=False,
        score_mutation=False,
        rank_mutation=False,
        queue_mutation=False,
        resume_text_mutation=False,
        operator_state_persistence=False,
        application_action_capability=False,
    ),
    CanonicalAgentDefinition(
        key="operator_review",
        display_name="Operator Review Agent",
        owner_module="src.agents.operator_review_agent",
        responsibility=(
            "Assign a human-review lane from the existing tailoring decision and "
            "its upstream evidence."
        ),
        deterministic_core=True,
        llm_capable=False,
        optional_controlled_llm_guardrail=False,
        advisory_only=True,
        human_approval_required=True,
        score_mutation=False,
        rank_mutation=False,
        queue_mutation=False,
        resume_text_mutation=False,
        operator_state_persistence=False,
        application_action_capability=False,
    ),
)

CANONICAL_AGENT_KEYS = tuple(
    definition.key for definition in CANONICAL_AGENT_DEFINITIONS
)

CANONICAL_AGENT_DEFINITIONS_BY_KEY: Mapping[str, CanonicalAgentDefinition] = (
    MappingProxyType(
        {
            definition.key: definition
            for definition in CANONICAL_AGENT_DEFINITIONS
        }
    )
)


def list_canonical_agent_definitions() -> tuple[CanonicalAgentDefinition, ...]:
    return CANONICAL_AGENT_DEFINITIONS


def get_canonical_agent_definition(agent_key: str) -> CanonicalAgentDefinition:
    key = str(agent_key or "").strip()
    try:
        return CANONICAL_AGENT_DEFINITIONS_BY_KEY[key]
    except KeyError as exc:
        raise KeyError(f"Unknown canonical agent key: {agent_key}") from exc
