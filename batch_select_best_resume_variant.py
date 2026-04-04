import argparse
import csv
import json
import os
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from difflib import SequenceMatcher

from src.ai.llm_client import run_chat_completion
from src.matching.job_adapter import build_job_evidence
from src.matching.scorer import score_resume_job_match
from src.resume.document_store import load_resume_documents
from src.resume.evidence_builder import build_resume_evidence

from src.config.settings import SCORER_V2_POLICY

SELECTOR_POLICY = SCORER_V2_POLICY["selector"]

TIE_EPSILON = SELECTOR_POLICY["tie_epsilon"]
TITLE_ONLY_TIE_EPSILON = SELECTOR_POLICY["title_only_tie_epsilon"]
NON_TITLE_DELTA_EPSILON = SELECTOR_POLICY["non_title_delta_epsilon"]
CLOSE_CALL_REVIEW_EPSILON = SELECTOR_POLICY["close_call_review_epsilon"]

LLM_FALLBACK_PROVIDER = os.getenv("LLM_FALLBACK_PROVIDER", "groq").strip().lower()
LLM_FALLBACK_MODEL = os.getenv(
    "LLM_FALLBACK_MODEL",
    "llama-3.3-70b-versatile",
    ).strip()
LLM_FALLBACK_MAX_TOKENS = int(os.getenv("LLM_FALLBACK_MAX_TOKENS", "900"))
LLM_FALLBACK_TEMPERATURE = float(os.getenv("LLM_FALLBACK_TEMPERATURE", "0"))
LLM_FALLBACK_PROMPT_VERSION = "v1"
LLM_FALLBACK_CACHE_DIR = Path(
    os.getenv(
        "LLM_FALLBACK_CACHE_DIR",
        "outputs/application_planning/llm_fallback_cache",
    )
)

LLM_FALLBACK_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "best_resume": {"type": "STRING"},
        "best_score": {"type": "NUMBER"},
        "backup_resume": {"type": "STRING"},
        "backup_score": {"type": "NUMBER"},
        "confidence": {"type": "STRING"},
        "reason": {"type": "STRING"},
    },
    "required": [
        "best_resume",
        "best_score",
        "backup_resume",
        "backup_score",
        "confidence",
        "reason",
    ],
}

LLM_ADJUDICATION_PROVIDER = os.getenv(
    "LLM_ADJUDICATION_PROVIDER",
    LLM_FALLBACK_PROVIDER,
).strip().lower()
LLM_ADJUDICATION_MODEL = os.getenv(
    "LLM_ADJUDICATION_MODEL",
    LLM_FALLBACK_MODEL,
).strip()
LLM_ADJUDICATION_MAX_TOKENS = int(os.getenv("LLM_ADJUDICATION_MAX_TOKENS", "700"))
LLM_ADJUDICATION_TEMPERATURE = float(os.getenv("LLM_ADJUDICATION_TEMPERATURE", "0"))
LLM_ADJUDICATION_PROMPT_VERSION = "v1"
LLM_ADJUDICATION_CACHE_DIR = Path(
    os.getenv(
        "LLM_ADJUDICATION_CACHE_DIR",
        "outputs/application_planning/llm_adjudication_cache",
    )
)

LLM_ADJUDICATION_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "adjudicated_resume": {"type": "STRING"},
        "confidence": {"type": "STRING"},
        "reason": {"type": "STRING"},
    },
    "required": [
        "adjudicated_resume",
        "confidence",
        "reason",
    ],
}

def _load_job_records(job_corpus_path: Path, limit: int) -> List[dict]:
    if not job_corpus_path.exists():
        raise RuntimeError(f"Missing job corpus: {job_corpus_path}")

    records: List[dict] = []
    with job_corpus_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
            if limit > 0 and len(records) >= limit:
                break

    if not records:
        raise RuntimeError(f"No job records found in {job_corpus_path}")

    return records


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").lower().split()).strip()


def _job_matches_filters(record: dict, company_contains: str, title_contains: str) -> bool:
    company_ok = True
    title_ok = True

    if company_contains.strip():
        company_ok = _normalize_text(company_contains) in _normalize_text(record.get("company", ""))

    if title_contains.strip():
        title_ok = _normalize_text(title_contains) in _normalize_text(record.get("title", ""))

    return company_ok and title_ok


def _result_sort_key(result):
    return (
        -int(result.prefilter.passed),
        -result.final_score,
        result.pair.resume_name.lower(),
        result.pair.resume_id.lower(),
    )


def _dimension_snapshot(result, max_dims: int = 5) -> str:
    ordered = sorted(
        result.dimension_scores,
        key=lambda dim: (-dim.weighted_score, dim.name),
    )
    return ", ".join(
        f"{dim.name}={dim.score:.2f}/{dim.weighted_score:.3f}"
        for dim in ordered[:max_dims]
    )

def _dimension_scores_json(result) -> str:
    payload = []
    for dim in sorted(result.dimension_scores, key=lambda d: d.name):
        payload.append(
            {
                "name": dim.name,
                "score": round(float(dim.score), 6),
                "weight": round(float(dim.weight), 6),
                "weighted_score": round(float(dim.weighted_score), 6),
                "reason": dim.reason,
                "evidence": list(dim.evidence),
            }
        )
    return json.dumps(payload, ensure_ascii=False)

def _is_title_only_edge(
    winner,
    runner_up: Optional[object],
    non_title_epsilon: float = NON_TITLE_DELTA_EPSILON,
) -> bool:
    if runner_up is None:
        return False

    winner_map = {dim.name: dim for dim in winner.dimension_scores}
    runner_map = {dim.name: dim for dim in runner_up.dimension_scores}

    saw_title_delta = False

    for name, winner_dim in winner_map.items():
        runner_dim = runner_map.get(name)
        if runner_dim is None:
            continue

        delta = abs(winner_dim.weighted_score - runner_dim.weighted_score)

        if name == "title_alignment":
            if delta > 0.0:
                saw_title_delta = True
            continue

        if delta > non_title_epsilon:
            return False

    return saw_title_delta


def _is_effective_tie(winner, runner_up: Optional[object], epsilon: float = TIE_EPSILON) -> bool:
    if runner_up is None:
        return False

    score_gap = abs(winner.final_score - runner_up.final_score)

    if score_gap <= epsilon:
        return True

    return (
        score_gap <= TITLE_ONLY_TIE_EPSILON
        and _is_title_only_edge(winner, runner_up)
    )

def _score_gap(winner, runner_up: Optional[object]) -> float:
    if runner_up is None:
        return 0.0
    return abs(winner.final_score - runner_up.final_score)


def _is_close_call_manual_review(
    winner,
    runner_up: Optional[object],
    gap_epsilon: float = CLOSE_CALL_REVIEW_EPSILON,
) -> bool:
    if runner_up is None:
        return False

    if _is_effective_tie(winner, runner_up):
        return False

    return _score_gap(winner, runner_up) <= gap_epsilon


def _selection_signal(
    has_credible_match: bool,
    winner,
    runner_up: Optional[object],
    manual_review_gap_epsilon: float = CLOSE_CALL_REVIEW_EPSILON,
) -> str:
    if not has_credible_match:
        return "no_credible_match"

    if _is_effective_tie(winner, runner_up):
        return "effective_tie"

    if _is_close_call_manual_review(
        winner,
        runner_up,
        gap_epsilon=manual_review_gap_epsilon,
    ):
        return "manual_review_close_call"

    return "decisive_winner"

def _recommendation_lines(
    winner,
    runner_up: Optional[object],
    manual_review_gap_epsilon: float = CLOSE_CALL_REVIEW_EPSILON,
) -> List[str]:
    lines = []
    is_tie = _is_effective_tie(winner, runner_up)
    is_close_call_manual_review = _is_close_call_manual_review(
        winner,
        runner_up,
        gap_epsilon=manual_review_gap_epsilon,
    )

    score_gap = _score_gap(winner, runner_up)

    if is_tie:
        if score_gap <= TIE_EPSILON:
            tie_reason = f"which is within the tie threshold of {TIE_EPSILON:.3f}."
        else:
            tie_reason = (
                f"which is above the base tie threshold of {TIE_EPSILON:.3f} "
                f"but still qualifies as an effective tie because only title alignment separates the variants."
            )

        lines.append(
            f"Tie: {winner.pair.resume_name} and {runner_up.pair.resume_name} "
            f"are effectively equivalent for {winner.pair.job_company} | {winner.pair.job_title}."
        )
        lines.append(
            f"Why: score gap is only {score_gap:.3f}, {tie_reason}"
        )
        lines.append(f"Top-ranked variant by deterministic ordering: {winner.pair.resume_name}")
        lines.append(f"Equivalent backup variant: {runner_up.pair.resume_name}")

    elif is_close_call_manual_review:
        lines.append(
            f"Manual review: {winner.pair.resume_name} is the current top-ranked variant for "
            f"{winner.pair.job_company} | {winner.pair.job_title}, but the gap versus "
            f"{runner_up.pair.resume_name} is only {score_gap:.3f}, which is within the "
            f"close-call review threshold of {manual_review_gap_epsilon:.3f}."
        )
        lines.append(f"Current top-ranked variant by deterministic ordering: {winner.pair.resume_name}")
        lines.append(f"Close backup variant: {runner_up.pair.resume_name}")

    else:
        lines.append(f"Use: {winner.pair.resume_name}")
        lines.append(
            f"Why: highest deterministic match score ({winner.final_score:.3f}) "
            f"for {winner.pair.job_company} | {winner.pair.job_title}."
        )

        if runner_up is not None:
            lines.append(
                f"Best backup: {runner_up.pair.resume_name} "
                f"(score {runner_up.final_score:.3f}, gap {score_gap:.3f})."
            )

    if winner.prefilter.matched_terms:
        lines.append(
            f"Strongest matched terms: {', '.join(winner.prefilter.matched_terms[:6])}"
        )

    if winner.prefilter.missing_requirements:
        lines.append(
            f"Main remaining gaps: {', '.join(winner.prefilter.missing_requirements[:6])}"
        )
    else:
        lines.append("Main remaining gaps: none explicitly identified.")

    return lines


def _has_credible_match(passed_results: List[object]) -> bool:
    return len(passed_results) > 0


def _no_credible_match_lines(top_result) -> List[str]:
    lines = [
        f"No credible resume match: all resume variants failed deterministic prefilter for "
        f"{top_result.pair.job_company} | {top_result.pair.job_title}.",
        f"Closest diagnostic variant by deterministic ordering: "
        f"{top_result.pair.resume_name} (score {top_result.final_score:.3f}).",
    ]

    if top_result.prefilter.matched_terms:
        lines.append(
            f"Strongest matched terms: {', '.join(top_result.prefilter.matched_terms[:6])}"
        )

    if top_result.prefilter.missing_requirements:
        lines.append(
            f"Main remaining gaps: {', '.join(top_result.prefilter.missing_requirements[:6])}"
        )
    else:
        lines.append("Main remaining gaps: none explicitly identified.")

    return lines


def _truncate_text(text: str, limit: int = 220) -> str:
    cleaned = " ".join(str(text or "").split()).strip()
    return cleaned[:limit]


def _resume_titles_preview(resume_evidence, limit: int = 5) -> List[str]:
    return [str(title).strip() for title in list(resume_evidence.titles)[:limit] if str(title).strip()]


def _resume_bullet_preview(resume_evidence, limit: int = 4) -> List[str]:
    bullets: List[str] = []
    for entry in resume_evidence.experience_entries:
        for bullet in getattr(entry, "bullets", []):
            cleaned = _truncate_text(bullet, 220)
            if cleaned:
                bullets.append(cleaned)
            if len(bullets) >= limit:
                return bullets
    return bullets

def _normalized_signature_list(values: List[str]) -> List[str]:
    normalized: List[str] = []
    for value in values:
        cleaned = " ".join(str(value or "").split()).strip().lower()
        if cleaned:
            normalized.append(cleaned)
    return sorted(normalized)


def _adjudication_evidence_signature(result, resume_evidence) -> Dict[str, Any]:
    return {
        "bullet_preview": _normalized_signature_list(
            _resume_bullet_preview(resume_evidence, limit=4)
        ),
        "matched_terms": _normalized_signature_list(
            list(result.prefilter.matched_terms)
        ),
        "missing_requirements": _normalized_signature_list(
            list(result.prefilter.missing_requirements)
        ),
    }


def _text_similarity_ratio(left: str, right: str) -> float:
    left_text = " ".join(str(left or "").split()).strip().lower()
    right_text = " ".join(str(right or "").split()).strip().lower()

    if not left_text and not right_text:
        return 1.0
    if not left_text or not right_text:
        return 0.0

    return SequenceMatcher(None, left_text, right_text).ratio()


def _preview_lists_equivalent(
    left: List[str],
    right: List[str],
    min_ratio: float = 0.84,
) -> bool:
    left_items = [
        " ".join(str(value or "").split()).strip()
        for value in left
        if " ".join(str(value or "").split()).strip()
    ]
    right_remaining = [
        " ".join(str(value or "").split()).strip()
        for value in right
        if " ".join(str(value or "").split()).strip()
    ]

    if len(left_items) != len(right_remaining):
        return False

    for left_item in left_items:
        if not right_remaining:
            return False

        best_idx = -1
        best_ratio = -1.0
        for idx, right_item in enumerate(right_remaining):
            ratio = _text_similarity_ratio(left_item, right_item)
            if ratio > best_ratio:
                best_ratio = ratio
                best_idx = idx

        if best_ratio < min_ratio:
            return False

        right_remaining.pop(best_idx)

    return True


def _should_skip_llm_adjudication_for_equivalent_variants(
    winner,
    runner_up,
    resume_evidence_list: List[object],
) -> bool:
    if runner_up is None:
        return False

    evidence_by_resume_id = {
        str(evidence.document.resume_id): evidence
        for evidence in resume_evidence_list
    }

    winner_evidence = evidence_by_resume_id.get(str(winner.pair.resume_id))
    runner_up_evidence = evidence_by_resume_id.get(str(runner_up.pair.resume_id))

    if winner_evidence is None or runner_up_evidence is None:
        return False

    winner_sig = _adjudication_evidence_signature(winner, winner_evidence)
    runner_sig = _adjudication_evidence_signature(runner_up, runner_up_evidence)

    if winner_sig == runner_sig:
        return True

    matched_terms_equal = winner_sig["matched_terms"] == runner_sig["matched_terms"]
    missing_requirements_equal = (
        winner_sig["missing_requirements"] == runner_sig["missing_requirements"]
    )
    preview_equivalent = _preview_lists_equivalent(
        winner_sig["bullet_preview"],
        runner_sig["bullet_preview"],
    )

    return (
        matched_terms_equal
        and missing_requirements_equal
        and preview_equivalent
    )

def _build_llm_fallback_prompt(
    record: dict,
    strict_results: List[object],
    resume_evidence_list: List[object],
) -> str:
    evidence_by_resume_id = {
        evidence.document.resume_id: evidence
        for evidence in resume_evidence_list
    }

    lines: List[str] = []
    lines.append("You are ranking resume variants for a single job.")
    lines.append("This is a fallback ranking task because strict deterministic matching found no credible winner.")
    lines.append("You must stay grounded only in the evidence provided.")
    lines.append("Do not invent tools, skills, domains, projects, outcomes, or responsibilities.")
    lines.append("Choose the best available resume and one backup even if all options are imperfect.")
    lines.append("Use only the provided resume names. Return compact JSON only.")
    lines.append("")
    lines.append(f"Job company: {record.get('company', '')}")
    lines.append(f"Job title: {record.get('title', '')}")
    lines.append(f"Role family: {record.get('role_family', '')}")
    lines.append(f"Required skills: {record.get('required_skills', [])}")
    lines.append(f"Preferred skills: {record.get('preferred_skills', [])}")
    lines.append(f"All skills: {record.get('all_skills', [])}")
    lines.append(f"Job description preview: {_truncate_text(record.get('description', ''), 2500)}")
    lines.append("")
    lines.append("Resume evidence:")
    for idx, strict_result in enumerate(strict_results, start=1):
        resume_evidence = evidence_by_resume_id[strict_result.pair.resume_id]
        lines.append(f"{idx}. Resume: {strict_result.pair.resume_name}")
        lines.append(f"   Extracted titles: {_resume_titles_preview(resume_evidence)}")
        lines.append(f"   Strict matched terms: {list(strict_result.prefilter.matched_terms)}")
        lines.append(f"   Strict missing required: {list(strict_result.prefilter.missing_requirements)}")
        lines.append("   Resume bullets:")
        for bullet in _resume_bullet_preview(resume_evidence):
            lines.append(f"   - {bullet}")
        lines.append("")

    lines.append("Return JSON with:")
    lines.append("1. best_resume: exact resume filename from the provided list")
    lines.append("2. best_score: number from 0.0 to 1.0")
    lines.append("3. backup_resume: exact resume filename from the provided list")
    lines.append("4. backup_score: number from 0.0 to 1.0")
    lines.append("5. confidence: one of low, medium, high")
    lines.append("6. reason: short grounded explanation")
    return "\n".join(lines)

def _llm_fallback_cache_key(
    provider: str,
    model: str,
    system_prompt: str,
    prompt: str,
) -> str:
    payload = {
        "prompt_version": LLM_FALLBACK_PROMPT_VERSION,
        "provider": provider,
        "model": model,
        "system_prompt": system_prompt,
        "prompt": prompt,
    }
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _llm_fallback_cache_path(cache_key: str) -> Path:
    return LLM_FALLBACK_CACHE_DIR / f"{cache_key}.json"


def _load_llm_fallback_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    path = _llm_fallback_cache_path(cache_key)
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, dict):
        return None

    payload["status"] = "cached"
    payload["cache_hit"] = True
    return payload


def _write_llm_fallback_cache(cache_key: str, payload: Dict[str, Any]) -> None:
    LLM_FALLBACK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _llm_fallback_cache_path(cache_key)

    cached_payload = dict(payload)
    cached_payload["cache_hit"] = False

    with path.open("w", encoding="utf-8") as f:
        json.dump(cached_payload, f, indent=2, ensure_ascii=False)

def _normalize_llm_fallback_parsed(
    parsed: Dict[str, Any],
    allowed_resume_names: List[str],
) -> Dict[str, Any]:
    allowed = {name.strip() for name in allowed_resume_names if name.strip()}

    best_resume = str(parsed.get("best_resume", "")).strip()
    backup_resume = str(parsed.get("backup_resume", "")).strip()

    if best_resume not in allowed:
        raise ValueError(f"LLM fallback returned invalid best_resume: {best_resume!r}")

    if backup_resume and backup_resume not in allowed:
        raise ValueError(f"LLM fallback returned invalid backup_resume: {backup_resume!r}")

    if backup_resume == best_resume:
        backup_resume = ""

    best_score = max(0.0, min(1.0, float(parsed.get("best_score", 0.0))))
    backup_score = max(0.0, min(1.0, float(parsed.get("backup_score", 0.0))))

    confidence = str(parsed.get("confidence", "")).strip().lower()
    if confidence not in {"low", "medium", "high"}:
        confidence = "low"

    reason = str(parsed.get("reason", "")).strip()

    return {
        "best_resume": best_resume,
        "best_score": best_score,
        "backup_resume": backup_resume,
        "backup_score": backup_score if backup_resume else 0.0,
        "confidence": confidence,
        "reason": reason,
    }

def _parse_llm_fallback_response(response: Any) -> Dict[str, Any]:
    if isinstance(response, dict):
        return response

    text = str(response or "").strip()
    if not text:
        raise ValueError("Empty LLM fallback response")

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        if lines and lines[0].strip().lower() == "json":
            lines = lines[1:]

        text = "\n".join(lines).strip()

    return json.loads(text)

def _run_llm_fallback_ranking(
    record: dict,
    strict_results: List[object],
    resume_evidence_list: List[object],
) -> Dict[str, Any]:
    prompt = _build_llm_fallback_prompt(
        record=record,
        strict_results=strict_results,
        resume_evidence_list=resume_evidence_list,
    )

    allowed_resume_names = [result.pair.resume_name for result in strict_results]
    provider = str(LLM_FALLBACK_PROVIDER or "").strip().lower()
    model = str(LLM_FALLBACK_MODEL or "").strip()

    system_prompt = """
You rank resume variants for fallback use when strict deterministic matching found no credible winner.

Rules:
1. Use ONLY the evidence provided.
2. Do NOT invent skills, tools, experience, metrics, or domain exposure.
3. Pick the best available resume and one backup even if fit is weak.
4. Use exact resume filenames from the provided list.
5. Return ONLY valid JSON.
""".strip()

    cache_key = _llm_fallback_cache_key(
        provider=provider,
        model=model,
        system_prompt=system_prompt,
        prompt=prompt,
    )

    cached = _load_llm_fallback_cache(cache_key)
    if cached is not None:
        return cached

    try:
        if provider == "groq":
            response = run_chat_completion(
                provider=provider,
                model=model,
                temperature=LLM_FALLBACK_TEMPERATURE,
                max_tokens=LLM_FALLBACK_MAX_TOKENS,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            parsed = _parse_llm_fallback_response(response)
        else:
            response = run_chat_completion(
                provider=provider,
                model=model,
                temperature=LLM_FALLBACK_TEMPERATURE,
                max_tokens=LLM_FALLBACK_MAX_TOKENS,
                response_mime_type="application/json",
                response_schema=LLM_FALLBACK_RESPONSE_SCHEMA,
                return_parsed=True,
                thinking_budget=0,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            parsed = _parse_llm_fallback_response(response)

        normalized = _normalize_llm_fallback_parsed(parsed, allowed_resume_names)

        result = {
            "status": "generated",
            "parse_ok": True,
            "provider": provider,
            "model": model,
            "best_resume": normalized["best_resume"],
            "best_score": f"{normalized['best_score']:.6f}",
            "backup_resume": normalized["backup_resume"],
            "backup_score": (
                f"{normalized['backup_score']:.6f}" if normalized["backup_resume"] else ""
            ),
            "confidence": normalized["confidence"],
            "reason": normalized["reason"],
            "error_type": "",
            "cache_hit": False,
        }
        _write_llm_fallback_cache(cache_key, result)
        return result

    except Exception as exc:
        error_text = str(exc)
        error_lower = error_text.lower()

        if "resource_exhausted" in error_lower or "quota" in error_lower or "429" in error_lower:
            status = "rate_limited"
        elif "parse" in error_lower or "json" in error_lower:
            status = "parse_failed"
        else:
            status = "error"

        return {
            "status": status,
            "parse_ok": False,
            "provider": provider,
            "model": model,
            "best_resume": "",
            "best_score": "",
            "backup_resume": "",
            "backup_score": "",
            "confidence": "",
            "reason": "",
            "error_type": f"call_failed: {exc}",
            "cache_hit": False,
        }

def _should_run_llm_adjudication(
    has_credible_match: bool,
    winner,
    runner_up: Optional[object],
    manual_review_gap_epsilon: float = CLOSE_CALL_REVIEW_EPSILON,
) -> bool:
    if not has_credible_match or runner_up is None:
        return False

    return (
        _is_effective_tie(winner, runner_up)
        or _is_close_call_manual_review(
            winner,
            runner_up,
            gap_epsilon=manual_review_gap_epsilon,
        )
    )


def _build_llm_adjudication_prompt(
    record: dict,
    winner,
    runner_up,
    resume_evidence_list: List[object],
) -> str:
    evidence_by_resume_id = {
        evidence.document.resume_id: evidence
        for evidence in resume_evidence_list
    }

    candidates = [winner, runner_up]
    allowed_resume_names = [result.pair.resume_name for result in candidates]

    lines: List[str] = []
    lines.append("You are adjudicating between two ambiguous resume variants for one job.")
    lines.append("The deterministic selector has already narrowed the choice to these two finalists.")
    lines.append("Do not invent skills, tools, projects, outcomes, or domain exposure.")
    lines.append("Use ONLY the evidence provided.")
    lines.append("Choose exactly one resume filename from the finalist list.")
    lines.append("")
    lines.append(f"Job company: {record.get('company', '')}")
    lines.append(f"Job title: {record.get('title', '')}")
    lines.append(f"Role family: {record.get('role_family', '')}")
    lines.append(f"Required skills: {record.get('required_skills', [])}")
    lines.append(f"Preferred skills: {record.get('preferred_skills', [])}")
    lines.append(f"All skills: {record.get('all_skills', [])}")
    lines.append(f"Job description preview: {_truncate_text(record.get('description', ''), 2500)}")
    lines.append("")
    lines.append(f"Allowed finalist resumes: {allowed_resume_names}")
    lines.append("")

    for idx, strict_result in enumerate(candidates, start=1):
        resume_evidence = evidence_by_resume_id[strict_result.pair.resume_id]
        lines.append(f"{idx}. Resume: {strict_result.pair.resume_name}")
        lines.append(f"   Deterministic score: {strict_result.final_score:.6f}")
        lines.append(f"   Top dimensions: {_dimension_snapshot(strict_result)}")
        lines.append(f"   Prefilter matched terms: {list(strict_result.prefilter.matched_terms)}")
        lines.append(f"   Missing required: {list(strict_result.prefilter.missing_requirements)}")
        lines.append(f"   Extracted titles: {_resume_titles_preview(resume_evidence)}")
        lines.append("   Resume bullets:")
        for bullet in _resume_bullet_preview(resume_evidence):
            lines.append(f"   - {bullet}")
        lines.append("")

    lines.append("Return JSON with:")
    lines.append("1. adjudicated_resume: exact resume filename from the finalist list")
    lines.append("2. confidence: one of low, medium, high")
    lines.append("3. reason: short grounded explanation")
    return "\n".join(lines)


def _llm_adjudication_cache_key(
    provider: str,
    model: str,
    system_prompt: str,
    prompt: str,
) -> str:
    payload = {
        "prompt_version": LLM_ADJUDICATION_PROMPT_VERSION,
        "provider": provider,
        "model": model,
        "system_prompt": system_prompt,
        "prompt": prompt,
    }
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _llm_adjudication_cache_path(cache_key: str) -> Path:
    return LLM_ADJUDICATION_CACHE_DIR / f"{cache_key}.json"


def _load_llm_adjudication_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    path = _llm_adjudication_cache_path(cache_key)
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, dict):
        return None

    payload["status"] = "cached"
    payload["cache_hit"] = True
    return payload


def _write_llm_adjudication_cache(cache_key: str, payload: Dict[str, Any]) -> None:
    LLM_ADJUDICATION_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _llm_adjudication_cache_path(cache_key)

    cached_payload = dict(payload)
    cached_payload["cache_hit"] = False

    with path.open("w", encoding="utf-8") as f:
        json.dump(cached_payload, f, indent=2, ensure_ascii=False)


def _normalize_llm_adjudication_parsed(
    parsed: Dict[str, Any],
    allowed_resume_names: List[str],
) -> Dict[str, Any]:
    allowed = {name.strip() for name in allowed_resume_names if name.strip()}
    adjudicated_resume = str(parsed.get("adjudicated_resume", "")).strip()

    if adjudicated_resume not in allowed:
        raise ValueError(f"LLM adjudication returned invalid adjudicated_resume: {adjudicated_resume!r}")

    confidence = str(parsed.get("confidence", "")).strip().lower()
    if confidence not in {"low", "medium", "high"}:
        confidence = "low"

    reason = str(parsed.get("reason", "")).strip()

    return {
        "adjudicated_resume": adjudicated_resume,
        "confidence": confidence,
        "reason": reason,
    }


def _run_llm_adjudication(
    record: dict,
    winner,
    runner_up,
    resume_evidence_list: List[object],
) -> Dict[str, Any]:
    prompt = _build_llm_adjudication_prompt(
        record=record,
        winner=winner,
        runner_up=runner_up,
        resume_evidence_list=resume_evidence_list,
    )

    allowed_resume_names = [
        winner.pair.resume_name,
        runner_up.pair.resume_name,
    ]
    provider = str(LLM_ADJUDICATION_PROVIDER or "").strip().lower()
    model = str(LLM_ADJUDICATION_MODEL or "").strip()

    system_prompt = """
You adjudicate between two finalist resume variants after deterministic scoring found an ambiguous result.

Rules:
1. Use ONLY the evidence provided.
2. Do NOT invent skills, tools, experience, metrics, or domain exposure.
3. Choose exactly one resume filename from the finalist list.
4. Return ONLY valid JSON.
""".strip()

    cache_key = _llm_adjudication_cache_key(
        provider=provider,
        model=model,
        system_prompt=system_prompt,
        prompt=prompt,
    )

    cached = _load_llm_adjudication_cache(cache_key)
    if cached is not None:
        return cached

    try:
        if provider == "groq":
            response = run_chat_completion(
                provider=provider,
                model=model,
                temperature=LLM_ADJUDICATION_TEMPERATURE,
                max_tokens=LLM_ADJUDICATION_MAX_TOKENS,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            parsed = _parse_llm_fallback_response(response)
        else:
            response = run_chat_completion(
                provider=provider,
                model=model,
                temperature=LLM_ADJUDICATION_TEMPERATURE,
                max_tokens=LLM_ADJUDICATION_MAX_TOKENS,
                response_mime_type="application/json",
                response_schema=LLM_ADJUDICATION_RESPONSE_SCHEMA,
                return_parsed=True,
                thinking_budget=0,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            parsed = _parse_llm_fallback_response(response)

        normalized = _normalize_llm_adjudication_parsed(parsed, allowed_resume_names)

        result = {
            "status": "generated",
            "parse_ok": True,
            "provider": provider,
            "model": model,
            "adjudicated_resume": normalized["adjudicated_resume"],
            "confidence": normalized["confidence"],
            "reason": normalized["reason"],
            "error_type": "",
            "cache_hit": False,
        }
        _write_llm_adjudication_cache(cache_key, result)
        return result

    except Exception as exc:
        error_text = str(exc)
        error_lower = error_text.lower()

        if "resource_exhausted" in error_lower or "quota" in error_lower or "429" in error_lower:
            status = "rate_limited"
        elif "parse" in error_lower or "json" in error_lower:
            status = "parse_failed"
        else:
            status = "error"

        return {
            "status": status,
            "parse_ok": False,
            "provider": provider,
            "model": model,
            "adjudicated_resume": "",
            "confidence": "",
            "reason": "",
            "error_type": f"call_failed: {exc}",
            "cache_hit": False,
        }

def _contains_any_normalized(text: str, phrases: List[str]) -> bool:
    normalized_text = _normalize_text(text)
    return any(_normalize_text(phrase) in normalized_text for phrase in phrases)


def _should_suppress_low_value_llm_adjudication(llm_adjudication: Dict[str, Any]) -> bool:
    adjudicated_resume = str(llm_adjudication.get("adjudicated_resume", "")).strip()
    reason = str(llm_adjudication.get("reason", "")).strip()

    if not adjudicated_resume or not reason:
        return False

    strong_evidence_markers = [
        "retrieval corpus",
        "embedded via pinecone",
        "grounding responses in authoritative data",
        "authoritative data",
        "processing large datasets",
        "3m+",
        "k-means",
        "pca",
        "k-nearest neighbors",
        "showcase more depth in big data",
        "showcase more depth in big data processing",
        "more depth in big data processing",
        "vector databases",
        "explainable diagnostics",
    ]

    low_value_markers = [
        "slightly higher deterministic score",
        "marginally higher deterministic score",
        "difference is negligible",
        "chosen due to a slightly higher score",
        "slightly higher score",
        "nearly identical in content and deterministic score",
        "both resumes are nearly identical",
        "both resumes are very similar",
        "both resumes have nearly identical deterministic scores",
        "has a marginally higher deterministic score",
        "slightly more aligned",
        "extracted titles",
        "title match",
        "more direct 'data scientist",
        "ai engineer' in its extracted titles",
    ]

    if _contains_any_normalized(reason, strong_evidence_markers):
        return False

    return _contains_any_normalized(reason, low_value_markers)


def _suppress_llm_adjudication_result(
    llm_adjudication: Dict[str, Any],
) -> Dict[str, Any]:
    suppressed = dict(llm_adjudication)
    suppressed["status"] = "suppressed_low_value_reason"
    suppressed["adjudicated_resume"] = ""
    suppressed["confidence"] = ""
    suppressed["differs_from_deterministic"] = "False"
    return suppressed

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch-select the best resume variant for multiple jobs."
    )
    parser.add_argument(
        "--job-corpus",
        default="data/rag/job_corpus.jsonl",
        help="Path to the retrieval-ready job corpus JSONL.",
    )
    parser.add_argument(
        "--job-limit",
        type=int,
        default=50,
        help="How many jobs from the corpus to evaluate. Use 0 for all.",
    )
    parser.add_argument(
        "--company-contains",
        default="",
        help="Optional case-insensitive company substring filter.",
    )
    parser.add_argument(
        "--title-contains",
        default="",
        help="Optional case-insensitive title substring filter.",
    )
    parser.add_argument(
        "--resume-name-contains",
        default="",
        help="Optional case-insensitive resume filename substring filter.",
    )
    parser.add_argument(
        "--top-k-console",
        type=int,
        default=10,
        help="How many selected jobs to print to the console.",
    )
    parser.add_argument(
        "--output-csv",
        default="best_resume_variant_by_job.csv",
        help="Path to write the batch selector CSV.",
    )
    parser.add_argument(
        "--manual-review-gap-epsilon",
        type=float,
        default=CLOSE_CALL_REVIEW_EPSILON,
        help=(
            "If winner vs runner-up is above tie handling but at or below this gap, "
            "flag the result as a deterministic manual-review close call."
        ),
    )
    parser.add_argument(
        "--generate-llm-fallback",
        action="store_true",
        help="For jobs with no credible deterministic winner, run LLM fallback ranking across all resume variants.",
    )
    parser.add_argument(
        "--generate-llm-adjudication",
        action="store_true",
        help="For effective ties and manual-review close calls, run bounded LLM adjudication across the top two deterministic finalists.",
    )
    args = parser.parse_args()

    raw_records = _load_job_records(
        Path(args.job_corpus),
        limit=0,
    )

    job_records = [
        record for record in raw_records
        if _job_matches_filters(
            record,
            company_contains=args.company_contains,
            title_contains=args.title_contains,
        )
    ]

    if args.job_limit > 0:
        job_records = job_records[:args.job_limit]

    if not job_records:
        raise RuntimeError("No job records matched the provided filters.")

    resume_docs = load_resume_documents()
    if args.resume_name_contains.strip():
        needle = _normalize_text(args.resume_name_contains)
        resume_docs = [
            doc for doc in resume_docs
            if needle in _normalize_text(doc.resume_name)
        ]

    resume_docs = sorted(resume_docs, key=lambda doc: doc.resume_name)
    if not resume_docs:
        raise RuntimeError("No resume documents loaded after filters.")

    resume_evidence_list = [build_resume_evidence(doc) for doc in resume_docs]
    output_rows = []

    for record in job_records:
        job_evidence = build_job_evidence(record)

        results = []
        for resume_evidence in resume_evidence_list:
            result = score_resume_job_match(resume_evidence, job_evidence)
            results.append(result)

        results = sorted(results, key=_result_sort_key)
        passed_results = [result for result in results if result.prefilter.passed]
        failed_results = [result for result in results if not result.prefilter.passed]

        selected = passed_results if passed_results else results
        winner = selected[0]
        runner_up = selected[1] if len(selected) > 1 else None

        has_credible_match = _has_credible_match(passed_results)
        if not has_credible_match:
            runner_up = None

        llm_fallback = {
            "status": "disabled",
            "parse_ok": "",
            "provider": "",
            "model": "",
            "best_resume": "",
            "best_score": "",
            "backup_resume": "",
            "backup_score": "",
            "confidence": "",
            "reason": "",
            "error_type": "",
            "cache_hit": "",
        }
        llm_adjudication = {
            "status": "disabled",
            "parse_ok": "",
            "provider": "",
            "model": "",
            "adjudicated_resume": "",
            "confidence": "",
            "reason": "",
            "error_type": "",
            "cache_hit": "",
            "differs_from_deterministic": "",
        }

        if not has_credible_match and args.generate_llm_fallback:
            llm_fallback = _run_llm_fallback_ranking(
                record=record,
                strict_results=results,
                resume_evidence_list=resume_evidence_list,
            )

        is_tie = _is_effective_tie(winner, runner_up) if has_credible_match else False
        requires_manual_review = (
            _is_close_call_manual_review(
                winner,
                runner_up,
                gap_epsilon=args.manual_review_gap_epsilon,
            )
            if has_credible_match
            else False
        )
        selection_signal = _selection_signal(
            has_credible_match=has_credible_match,
            winner=winner,
            runner_up=runner_up,
            manual_review_gap_epsilon=args.manual_review_gap_epsilon,
        )
        if (
            args.generate_llm_adjudication
            and _should_run_llm_adjudication(
                has_credible_match=has_credible_match,
                winner=winner,
                runner_up=runner_up,
                manual_review_gap_epsilon=args.manual_review_gap_epsilon,
            )
        ):
            if _should_skip_llm_adjudication_for_equivalent_variants(
                winner=winner,
                runner_up=runner_up,
                resume_evidence_list=resume_evidence_list,
            ):
                llm_adjudication = {
                    "status": "skipped_equivalent_variants",
                    "parse_ok": "",
                    "provider": "",
                    "model": "",
                    "adjudicated_resume": "",
                    "confidence": "",
                    "reason": "",
                    "error_type": "",
                    "cache_hit": "",
                    "differs_from_deterministic": "False",
                }
            else:
                llm_adjudication = _run_llm_adjudication(
                    record=record,
                    winner=winner,
                    runner_up=runner_up,
                    resume_evidence_list=resume_evidence_list,
                )
                adjudicated_resume = str(llm_adjudication.get("adjudicated_resume", "")).strip()
                llm_adjudication["differs_from_deterministic"] = str(
                    bool(adjudicated_resume and adjudicated_resume != winner.pair.resume_name)
                )

                if _should_suppress_low_value_llm_adjudication(llm_adjudication):
                    llm_adjudication = _suppress_llm_adjudication_result(llm_adjudication)
        
        output_rows.append(
            {
                "job_doc_id": winner.pair.job_doc_id,
                "job_company": winner.pair.job_company,
                "job_title": winner.pair.job_title,
                "posted_at": str(record.get("posted_at", "") or ""),
                "resume_variants_considered": len(results),
                "passed_prefilter": len(passed_results),
                "filtered_out": len(failed_results),
                "winner_resume": winner.pair.resume_name if has_credible_match else "",
                "winner_score": f"{winner.final_score:.6f}",
                "winner_bucket": winner.match_bucket,
                "winner_top_dims": _dimension_snapshot(winner),
                "winner_missing_requirements": " | ".join(winner.prefilter.missing_requirements),
                "winner_matched_terms": " | ".join(winner.prefilter.matched_terms),
                "winner_prefilter_passed": winner.prefilter.passed,
                "winner_prefilter_best_title_score": f"{winner.prefilter.best_title_score:.6f}",
                "winner_prefilter_best_title": winner.prefilter.best_title,
                "winner_prefilter_matched_required_count": winner.prefilter.matched_required_count,
                "winner_prefilter_matched_preferred_count": winner.prefilter.matched_preferred_count,
                "winner_prefilter_matched_any_count": winner.prefilter.matched_any_count,
                "winner_prefilter_matched_required_terms": " | ".join(winner.prefilter.matched_required_terms),
                "winner_prefilter_matched_preferred_terms": " | ".join(winner.prefilter.matched_preferred_terms),
                "winner_prefilter_matched_any_terms": " | ".join(winner.prefilter.matched_any_terms),
                "winner_prefilter_reasons": " || ".join(winner.prefilter.reasons),
                "winner_dimension_scores_json": _dimension_scores_json(winner),
                "runner_up_resume": (
                    runner_up.pair.resume_name
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "runner_up_score": (
                    f"{runner_up.final_score:.6f}"
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "runner_up_prefilter_passed": (
                    runner_up.prefilter.passed
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "runner_up_prefilter_best_title_score": (
                    f"{runner_up.prefilter.best_title_score:.6f}"
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "runner_up_prefilter_best_title": (
                    runner_up.prefilter.best_title
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "runner_up_prefilter_matched_required_count": (
                    runner_up.prefilter.matched_required_count
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "runner_up_prefilter_matched_preferred_count": (
                    runner_up.prefilter.matched_preferred_count
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "runner_up_prefilter_matched_any_count": (
                    runner_up.prefilter.matched_any_count
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "runner_up_prefilter_matched_required_terms": (
                    " | ".join(runner_up.prefilter.matched_required_terms)
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "runner_up_prefilter_matched_preferred_terms": (
                    " | ".join(runner_up.prefilter.matched_preferred_terms)
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "runner_up_prefilter_matched_any_terms": (
                    " | ".join(runner_up.prefilter.matched_any_terms)
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "runner_up_prefilter_reasons": (
                    " || ".join(runner_up.prefilter.reasons)
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "runner_up_dimension_scores_json": (
                    _dimension_scores_json(runner_up)
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "score_gap": (
                    f"{(winner.final_score - runner_up.final_score):.6f}"
                    if has_credible_match and runner_up is not None
                    else ""
                ),
                "is_tie": is_tie,
                "selection_signal": selection_signal,
                "requires_manual_review": requires_manual_review,
                "manual_review_gap_epsilon": f"{args.manual_review_gap_epsilon:.6f}",
                "tie_epsilon": f"{TIE_EPSILON:.6f}",
                "recommendation_summary": (
                    " ".join(
                        _recommendation_lines(
                            winner,
                            runner_up,
                            manual_review_gap_epsilon=args.manual_review_gap_epsilon,
                        )
                    )
                    if has_credible_match
                    else " ".join(_no_credible_match_lines(winner))
                ),
                "llm_fallback_best_resume": llm_fallback["best_resume"],
                "llm_fallback_best_score": llm_fallback["best_score"],
                "llm_fallback_backup_resume": llm_fallback["backup_resume"],
                "llm_fallback_backup_score": llm_fallback["backup_score"],
                "llm_fallback_confidence": llm_fallback["confidence"],
                "llm_fallback_reason": llm_fallback["reason"],
                "llm_fallback_status": llm_fallback["status"],
                "llm_fallback_parse_ok": llm_fallback["parse_ok"],
                "llm_fallback_provider": llm_fallback["provider"],
                "llm_fallback_model": llm_fallback["model"],
                "llm_fallback_cache_hit": llm_fallback["cache_hit"],
                "llm_fallback_error_type": llm_fallback["error_type"],
                "llm_adjudication_resume": llm_adjudication["adjudicated_resume"],
                "llm_adjudication_confidence": llm_adjudication["confidence"],
                "llm_adjudication_reason": llm_adjudication["reason"],
                "llm_adjudication_status": llm_adjudication["status"],
                "llm_adjudication_parse_ok": llm_adjudication["parse_ok"],
                "llm_adjudication_provider": llm_adjudication["provider"],
                "llm_adjudication_model": llm_adjudication["model"],
                "llm_adjudication_cache_hit": llm_adjudication["cache_hit"],
                "llm_adjudication_differs_from_deterministic": llm_adjudication["differs_from_deterministic"],
                "llm_adjudication_error_type": llm_adjudication["error_type"],
            }
        )

    output_rows = sorted(
        output_rows,
        key=lambda row: (
            row["job_company"].lower(),
            row["job_title"].lower(),
            -float(row["winner_score"]),
            row["winner_resume"].lower(),
        ),
    )

    fieldnames = [
        "job_doc_id",
        "job_company",
        "job_title",
        "posted_at",
        "resume_variants_considered",
        "passed_prefilter",
        "filtered_out",
        "winner_resume",
        "winner_score",
        "winner_bucket",
        "winner_top_dims",
        "winner_missing_requirements",
        "winner_matched_terms",
        "winner_prefilter_passed",
        "winner_prefilter_best_title_score",
        "winner_prefilter_best_title",
        "winner_prefilter_matched_required_count",
        "winner_prefilter_matched_preferred_count",
        "winner_prefilter_matched_any_count",
        "winner_prefilter_matched_required_terms",
        "winner_prefilter_matched_preferred_terms",
        "winner_prefilter_matched_any_terms",
        "winner_prefilter_reasons",
        "winner_dimension_scores_json",
        "runner_up_resume",
        "runner_up_score",
        "runner_up_prefilter_passed",
        "runner_up_prefilter_best_title_score",
        "runner_up_prefilter_best_title",
        "runner_up_prefilter_matched_required_count",
        "runner_up_prefilter_matched_preferred_count",
        "runner_up_prefilter_matched_any_count",
        "runner_up_prefilter_matched_required_terms",
        "runner_up_prefilter_matched_preferred_terms",
        "runner_up_prefilter_matched_any_terms",
        "runner_up_prefilter_reasons",
        "runner_up_dimension_scores_json",
        "score_gap",
        "is_tie",
        "selection_signal",
        "requires_manual_review",
        "manual_review_gap_epsilon",
        "tie_epsilon",
        "recommendation_summary",
        "llm_fallback_best_resume",
        "llm_fallback_best_score",
        "llm_fallback_backup_resume",
        "llm_fallback_backup_score",
        "llm_fallback_confidence",
        "llm_fallback_reason",
        "llm_fallback_status",
        "llm_fallback_parse_ok",
        "llm_fallback_provider",
        "llm_fallback_model",
        "llm_fallback_cache_hit",
        "llm_fallback_error_type",
        "llm_adjudication_resume",
        "llm_adjudication_confidence",
        "llm_adjudication_reason",
        "llm_adjudication_status",
        "llm_adjudication_parse_ok",
        "llm_adjudication_provider",
        "llm_adjudication_model",
        "llm_adjudication_cache_hit",
        "llm_adjudication_differs_from_deterministic",
        "llm_adjudication_error_type",
    ]

    output_csv_path = Path(args.output_csv)
    with output_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)

    print("=" * 100)
    print("BATCH BEST RESUME VARIANT SELECTOR")
    print("=" * 100)
    print(f"Jobs evaluated: {len(output_rows)}")
    print(f"Resume variants considered per job: {len(resume_evidence_list)}")
    print(f"CSV written: {output_csv_path}")
    print()

    for row in output_rows[:args.top_k_console]:
        print("-" * 100)
        print(f"{row['job_company']} | {row['job_title']}")
        if row["winner_resume"]:
            print(
                f"Winner: {row['winner_resume']} | score={float(row['winner_score']):.3f} | "
                f"bucket={row['winner_bucket']} | selection={row['selection_signal']}"
            )
        else:
            print(
                f"No credible resume match | score={float(row['winner_score']):.3f} | "
                f"bucket={row['winner_bucket']}"
            )
            if row["llm_fallback_best_resume"]:
                print(
                    f"LLM fallback best available: {row['llm_fallback_best_resume']} | "
                    f"score={float(row['llm_fallback_best_score']):.3f} | "
                    f"confidence={row['llm_fallback_confidence']}"
                )
            if row["llm_fallback_backup_resume"]:
                print(
                    f"LLM fallback backup: {row['llm_fallback_backup_resume']} | "
                    f"score={float(row['llm_fallback_backup_score']):.3f}"
                )
            if row["llm_fallback_reason"]:
                print(f"LLM fallback reason: {row['llm_fallback_reason']}")

        if row["runner_up_resume"]:
            if str(row["is_tie"]).lower() == "true":
                print(
                    f"Tie backup: {row['runner_up_resume']} | "
                    f"score={float(row['runner_up_score']):.3f} | "
                    f"gap={float(row['score_gap']):.3f} | "
                    f"tie_epsilon={float(row['tie_epsilon']):.3f}"
                )
            elif str(row["requires_manual_review"]).lower() == "true":
                print(
                    f"Manual-review backup: {row['runner_up_resume']} | "
                    f"score={float(row['runner_up_score']):.3f} | "
                    f"gap={float(row['score_gap']):.3f} | "
                    f"review_epsilon={float(row['manual_review_gap_epsilon']):.3f}"
                )
            else:
                print(
                    f"Backup: {row['runner_up_resume']} | "
                    f"score={float(row['runner_up_score']):.3f} | "
                    f"gap={float(row['score_gap']):.3f}"
                )
            
        if row["llm_adjudication_resume"]:
            print(
                f"LLM adjudication: {row['llm_adjudication_resume']} | "
                f"confidence={row['llm_adjudication_confidence']} | "
                f"differs_from_deterministic={row['llm_adjudication_differs_from_deterministic']}"
            )
            if row["llm_adjudication_reason"]:
                print(f"LLM adjudication reason: {row['llm_adjudication_reason']}")

        print(f"Top dims: {row['winner_top_dims']}")
        print(
            "Audit: "
            f"title={row['winner_prefilter_best_title']} "
            f"(score={float(row['winner_prefilter_best_title_score']):.3f}), "
            f"required={row['winner_prefilter_matched_required_count']}, "
            f"preferred={row['winner_prefilter_matched_preferred_count']}, "
            f"any={row['winner_prefilter_matched_any_count']}"
        )
        if row["winner_missing_requirements"]:
            print(f"Missing requirements: {row['winner_missing_requirements']}")
        print(f"Summary: {row['recommendation_summary']}")
        print()


if __name__ == "__main__":
    main()
