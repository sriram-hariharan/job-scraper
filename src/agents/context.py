from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


def _dict_or_empty(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_or_empty(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


@dataclass
class JobApplicationContext:
    context_id: str
    owner_user_id: str
    run_id: str
    job: Dict[str, Any] = field(default_factory=dict)
    prefilter: Dict[str, Any] = field(default_factory=dict)
    jd_intelligence: Dict[str, Any] = field(default_factory=dict)
    resume_match: Dict[str, Any] = field(default_factory=dict)
    tailoring: Dict[str, Any] = field(default_factory=dict)
    critic: Dict[str, Any] = field(default_factory=dict)
    strategy: Dict[str, Any] = field(default_factory=dict)
    trace: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": str(self.context_id or "").strip(),
            "owner_user_id": str(self.owner_user_id or "").strip(),
            "run_id": str(self.run_id or "").strip(),
            "job": dict(self.job or {}),
            "prefilter": dict(self.prefilter or {}),
            "jd_intelligence": dict(self.jd_intelligence or {}),
            "resume_match": dict(self.resume_match or {}),
            "tailoring": dict(self.tailoring or {}),
            "critic": dict(self.critic or {}),
            "strategy": dict(self.strategy or {}),
            "trace": list(self.trace or []),
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "JobApplicationContext":
        if not isinstance(payload, dict):
            raise ValueError("JobApplicationContext payload must be a dictionary.")

        return cls(
            context_id=str(payload.get("context_id", "") or "").strip(),
            owner_user_id=str(payload.get("owner_user_id", "") or "").strip(),
            run_id=str(payload.get("run_id", "") or "").strip(),
            job=_dict_or_empty(payload.get("job")),
            prefilter=_dict_or_empty(payload.get("prefilter")),
            jd_intelligence=_dict_or_empty(payload.get("jd_intelligence")),
            resume_match=_dict_or_empty(payload.get("resume_match")),
            tailoring=_dict_or_empty(payload.get("tailoring")),
            critic=_dict_or_empty(payload.get("critic")),
            strategy=_dict_or_empty(payload.get("strategy")),
            trace=_list_or_empty(payload.get("trace")),
        )


def job_application_context_payload(**kwargs: Any) -> Dict[str, Any]:
    return JobApplicationContext(**kwargs).to_dict()
