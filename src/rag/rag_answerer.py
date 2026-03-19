import json
from typing import Any, Dict, List, Optional
import re

from src.ai.llm_client import run_chat_completion_with_metadata, get_default_model
from src.rag.query_engine import search_jobs
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

ANSWER_LLM_TIMEOUT_SECONDS = 25
MODEL = get_default_model()
MAX_SOURCE_CHARS = 2500


SYSTEM_PROMPT = """
You answer questions about job postings using ONLY the provided sources.

STRICT RULES
1. Use only the retrieved job sources.
2. Do not add outside knowledge.
3. If the sources do not contain enough evidence, say so plainly.
4. Every substantive claim must be grounded in at least one source.
5. Cite sources inline using bracketed source IDs like [S1] or [S2].
6. If comparing or ranking jobs, explain the evidence for each selected job.
7. For each cited source, include 2 to 4 short evidence points that directly explain why the job matches the question.
8. Evidence points must be concrete and source-grounded, such as title fit, required skills, domain context, ML/LLM/RAG/agentic language, experimentation, modeling, or platform signals.
9. Return ONLY valid JSON.

Return this exact JSON shape:
{
  "answer": "string",
  "insufficient_evidence": true,
  "used_source_ids": ["S1"],
  "job_evidence": [
    {
      "source_id": "S1",
      "evidence_points": ["string", "string"]
    }
  ]
}
""".strip()



def _extract_json_from_response(response: str) -> Dict[str, Any]:
    response = (response or "").replace("```json", "").replace("```", "").strip()

    start = response.find("{")
    end = response.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in LLM response")

    return json.loads(response[start:end + 1])


def _truncate(text: str, max_chars: int = MAX_SOURCE_CHARS) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n...[truncated]"


def _build_prompt_sources(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sources: List[Dict[str, Any]] = []

    for i, result in enumerate(results, start=1):
        sources.append(
            {
                "source_id": f"S{i}",
                "doc_id": result.get("doc_id", ""),
                "company": result.get("company", ""),
                "title": result.get("title", ""),
                "location": result.get("location", ""),
                "source": result.get("source", ""),
                "job_url": result.get("job_url", ""),
                "posted_at": result.get("posted_at", ""),
                "score": result.get("score"),
                "preview": result.get("preview", ""),
                "retrieval_text": _truncate(result.get("retrieval_text", "")),
            }
        )

    return sources


def _build_output_sources(
    prompt_sources: List[Dict[str, Any]],
    used_source_ids: List[str],
) -> List[Dict[str, Any]]:
    used = set(used_source_ids)

    return [
        {
            "source_id": source["source_id"],
            "doc_id": source["doc_id"],
            "company": source["company"],
            "title": source["title"],
            "location": source["location"],
            "source": source["source"],
            "job_url": source["job_url"],
            "posted_at": source["posted_at"],
            "score": source["score"],
            "preview": source["preview"],
        }
        for source in prompt_sources
        if source["source_id"] in used
    ]


def _build_user_prompt(question: str, sources: List[Dict[str, Any]]) -> str:
    blocks = []

    for source in sources:
        blocks.append(
            "\n".join(
                [
                    f"SOURCE {source['source_id']}",
                    f"doc_id: {source['doc_id']}",
                    f"company: {source['company']}",
                    f"title: {source['title']}",
                    f"location: {source['location']}",
                    f"source: {source['source']}",
                    f"job_url: {source['job_url']}",
                    "evidence:",
                    source["retrieval_text"],
                ]
            )
        )

    source_text = "\n\n".join(blocks)

    return f"""
    QUESTION:
    {question}

    SOURCES:
    {source_text}

    Answer the question using only the sources above.
    If you compare, rank, or recommend jobs, explain the concrete evidence for each selected source.
    Cite source IDs inline like [S1] and [S2].
    Return JSON only.
    """.strip()


def _normalize_used_source_ids(
    used_source_ids: Any,
    valid_source_ids: List[str],
) -> List[str]:
    if not isinstance(used_source_ids, list):
        return []

    valid = set(valid_source_ids)
    normalized: List[str] = []

    for item in used_source_ids:
        source_id = str(item or "").strip()
        if source_id in valid and source_id not in normalized:
            normalized.append(source_id)

    return normalized

def _normalize_evidence_points(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []

    normalized: List[str] = []
    for item in value:
        point = str(item or "").strip()
        if point and point not in normalized:
            normalized.append(point)

    return normalized[:4]


def _normalize_job_evidence(
    value: Any,
    valid_source_ids: List[str],
) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []

    valid = set(valid_source_ids)
    normalized: List[Dict[str, Any]] = []
    seen_source_ids: set[str] = set()

    for item in value:
        if not isinstance(item, dict):
            continue

        source_id = str(item.get("source_id") or "").strip()
        if not source_id or source_id not in valid or source_id in seen_source_ids:
            continue

        evidence_points = _normalize_evidence_points(item.get("evidence_points"))
        if not evidence_points:
            continue

        normalized.append(
            {
                "source_id": source_id,
                "evidence_points": evidence_points,
            }
        )
        seen_source_ids.add(source_id)

    return normalized


def _build_job_evidence_output(
    prompt_sources: List[Dict[str, Any]],
    job_evidence: List[Dict[str, Any]],
    allowed_source_ids: List[str],
) -> List[Dict[str, Any]]:
    source_lookup = {
        source["source_id"]: source
        for source in prompt_sources
    }
    allowed = set(allowed_source_ids)

    output: List[Dict[str, Any]] = []
    for item in job_evidence:
        source_id = item.get("source_id", "")
        if source_id not in allowed:
            continue

        source = source_lookup.get(source_id)
        if not source:
            continue

        output.append(
            {
                "source_id": source_id,
                "title": source.get("title", ""),
                "company": source.get("company", ""),
                "job_url": source.get("job_url", ""),
                "evidence_points": item.get("evidence_points", []),
            }
        )

    return output

def _ensure_inline_citations(answer: str, used_source_ids: List[str]) -> str:
    answer = (answer or "").strip()
    if not answer or not used_source_ids:
        return answer

    has_inline = any(f"[{source_id}]" in answer for source_id in used_source_ids)
    if has_inline:
        return answer

    citation_suffix = " ".join(f"[{source_id}]" for source_id in used_source_ids)
    return f"{answer} {citation_suffix}".strip()

def _normalize_insufficient_answer(answer: str) -> str:
    answer = (answer or "").strip()
    if answer:
        return answer

    return "I could not produce a grounded answer from the retrieved job documents."

def _strip_inline_citations(answer: str) -> str:
    answer = (answer or "").strip()
    answer = re.sub(r"\s*\[(S\d+)\]", "", answer)
    return re.sub(r"\s+", " ", answer).strip()

def _extract_inline_source_ids(answer: str, valid_source_ids: List[str]) -> List[str]:
    answer = (answer or "").strip()
    if not answer:
        return []

    valid = set(valid_source_ids)
    found = re.findall(r"\[(S\d+)\]", answer)

    ordered: List[str] = []
    for source_id in found:
        if source_id in valid and source_id not in ordered:
            ordered.append(source_id)

    return ordered

def _run_chat_completion_with_timeout(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(
        run_chat_completion_with_metadata,
        model=MODEL,
        temperature=0,
        max_tokens=500,
        messages=messages,
    )
    try:
        return future.result(timeout=ANSWER_LLM_TIMEOUT_SECONDS)
    except FuturesTimeoutError as exc:
        future.cancel()
        raise TimeoutError(
            f"LLM answer generation timed out after {ANSWER_LLM_TIMEOUT_SECONDS} seconds"
        ) from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
        
def answer_job_query(
    question: str,
    top_k: int = 5,
    fetch_k: int = 15,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    try:
        results = search_jobs(
            query=question,
            top_k=top_k,
            fetch_k=fetch_k,
            filters=filters,
        )
    except TimeoutError:
        return {
            "question": question,
            "answer": "I could not answer this because semantic retrieval timed out.",
            "insufficient_evidence": True,
            "used_source_ids": [],
            "sources": [],
            "retrieved_count": 0,
        }
    except Exception as exc:
        return {
            "question": question,
            "answer": f"I could not answer this because retrieval failed: {exc}",
            "insufficient_evidence": True,
            "used_source_ids": [],
            "sources": [],
            "retrieved_count": 0,
        }

    retrieval_lanes_used = sorted({
        lane
        for result in results
        for lane in result.get("retrieval_lanes", [])
        if lane in {"semantic", "lexical"}
    })
    if not results:
        return {
            "question": question,
            "answer": "I could not answer this because no matching job documents were retrieved.",
            "insufficient_evidence": True,
            "used_source_ids": [],
            "sources": [],
            "retrieved_count": 0,
            "job_evidence": [],
        }

    prompt_sources = _build_prompt_sources(results)
    valid_source_ids = [source["source_id"] for source in prompt_sources]

    try:
        llm_result = _run_chat_completion_with_timeout(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(question, prompt_sources)},
            ]
        )
        parsed = _extract_json_from_response(llm_result["content"])
        llm_provider = llm_result.get("provider", "")
        llm_model = llm_result.get("model", "")
        llm_fallback_used = bool(llm_result.get("fallback_used", False))
    except TimeoutError:
        return {
            "question": question,
            "answer": f"I could not answer this because the LLM timed out after {ANSWER_LLM_TIMEOUT_SECONDS} seconds.",
            "insufficient_evidence": True,
            "used_source_ids": [],
            "sources": [],
            "retrieved_count": len(results),
            "llm_provider": "",
            "llm_model": "",
            "llm_fallback_used": False,
            "retrieval_lanes_used": [],
            "job_evidence": [],
        }
    except Exception as exc:
        return {
            "question": question,
            "answer": f"I could not answer this because grounded answer generation failed: {exc}",
            "insufficient_evidence": True,
            "used_source_ids": [],
            "sources": [],
            "retrieved_count": len(results),
            "llm_provider": "",
            "llm_model": "",
            "llm_fallback_used": False,
            "retrieval_lanes_used": [],
            "job_evidence": [],
        }

    answer = str(parsed.get("answer") or "").strip()
    insufficient_evidence = bool(parsed.get("insufficient_evidence", False))
    model_used_source_ids = _normalize_used_source_ids(
        parsed.get("used_source_ids", []),
        valid_source_ids,
    )
    normalized_job_evidence = _normalize_job_evidence(
        parsed.get("job_evidence", []),
        valid_source_ids,
    )

    answer = _ensure_inline_citations(answer, model_used_source_ids)
    cited_source_ids = _extract_inline_source_ids(answer, valid_source_ids)

    if cited_source_ids:
        used_source_ids = cited_source_ids
    else:
        used_source_ids = []

    if answer and not insufficient_evidence and not used_source_ids:
        insufficient_evidence = True
        answer = "I could not produce a grounded answer because the answer text did not contain valid source citations."

    if insufficient_evidence:
        used_source_ids = []
        answer = _strip_inline_citations(answer)
        answer = _normalize_insufficient_answer(answer)

    if insufficient_evidence:
        job_evidence_output = []
    else:
        job_evidence_output = _build_job_evidence_output(
            prompt_sources=prompt_sources,
            job_evidence=normalized_job_evidence,
            allowed_source_ids=used_source_ids,
        )

    return {
        "question": question,
        "answer": answer,
        "insufficient_evidence": insufficient_evidence,
        "used_source_ids": used_source_ids,
        "sources": _build_output_sources(prompt_sources, used_source_ids) if not insufficient_evidence else [],
        "retrieved_count": len(results),
        "llm_provider": llm_provider,
        "llm_model": llm_model,
        "llm_fallback_used": llm_fallback_used,
        "retrieval_lanes_used": retrieval_lanes_used,
        "job_evidence": job_evidence_output,
    }


if __name__ == "__main__":
    demo = answer_job_query(
        question="Which retrieved jobs look strongest for experimentation-heavy data science work using causal inference and looker?",
        top_k=3,
        fetch_k=10,
    )
    print(json.dumps(demo, indent=2, ensure_ascii=False))