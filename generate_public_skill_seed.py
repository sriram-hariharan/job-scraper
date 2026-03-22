import argparse
import csv
import json
import re
import sys
import os
import time
from groq import Groq
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, List, Optional, Set, Tuple

# --------------------------------------------------------------------------------------
# TEMP LOCAL CONFIG FOR OFFLINE SKILL MINING ONLY
# This script is intentionally standalone and must not import runtime workflow modules.
# Do not import these values into scoring/runtime code directly.
# --------------------------------------------------------------------------------------

NORMALIZATION_MAP = {
    "llm apis": "llm",
    "large language models": "llm",
    "retrieval based ai systems": "rag",
    "retrievalbased ai systems": "rag",
    "vector databases": "vector db",
    "scikitlearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "support vector machine": "svm",
    "support vector machines": "svm",
    "random forests": "random forest",
    "jupyter notebook": "jupyter",
    "jupyter notebooks": "jupyter",
}

ALIAS_MAP = {
    "ab testing": "a/b testing",
    "ab tests": "a/b testing",
    "air flow": "airflow",
    "gen ai": "generative ai",
    "source control": "version control",
    "source code management": "version control",
    "version control systems": "version control",
    "ml": "machine learning",
    "nlp": "natural language processing",
}

COMMON_SKILL_PATTERNS = [
    "python",
    "sql",
    "r",
    "sas",
    "tableau",
    "looker",
    "power bi",
    "excel",
    "airflow",
    "dbt",
    "snowflake",
    "bigquery",
    "databricks",
    "spark",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "machine learning",
    "deep learning",
    "a/b testing",
    "bayesian inference",
    "causal inference",
    "experimental design",
    "hypothesis testing",
    "regression",
    "classification",
    "forecasting",
    "statistical modeling",
    "data science",
    "data analysis",
    "analytics",
    "generative ai",
    "llm",
    "jupyter",
    "git",
    "github",
    "gitlab",
    "version control",
    "random forest",
    "svm",
]

ANALYTICS_ML_SIGNAL_PATTERNS = [
    "machine learning",
    "deep learning",
    "model",
    "modeling",
    "regression",
    "classification",
    "forecasting",
    "statistics",
    "statistical",
    "statistical modeling",
    "analytics",
    "analysis",
    "data science",
    "random forest",
    "svm",
    "natural language processing",
    "computer vision",
    "time series",
]

TOOLING_SIGNAL_PATTERNS = [
    "python",
    "sql",
    "r",
    "sas",
    "tableau",
    "looker",
    "power bi",
    "airflow",
    "dbt",
    "snowflake",
    "bigquery",
    "databricks",
    "spark",
    "pytorch",
    "tensorflow",
    "jupyter",
    "git",
    "github",
    "gitlab",
    "version control",
    "docker",
    "kubernetes",
    "aws",
    "gcp",
    "azure",
]

DROP_EXACT = {
    "",
    "data scientist",
    "senior data scientist",
    "junior data scientist",
    "sr data scientist",
    "jr data scientist",
    "data analyst",
    "senior data analyst",
    "machine learning engineer",
    "senior machine learning engineer",
}

INVALID_SKILL_PATTERNS = [
    r"\b(full relocation package|relocation package)\b",
    r"\b(data scientist|data analyst|machine learning engineer|software engineer)\b.*\b(data scientist|data analyst|machine learning engineer|software engineer)\b",
    r"\bvisa\b",
    r"\bsponsorship\b",
    r"\bemployment\b",
    r"\bbenefits\b",
    r"\bsalary\b",
    r"\bcompensation\b",
    r"\bbonus\b",
    r"\byears? of experience\b",
    r"\bminimum qualifications?\b",
    r"\bpreferred qualifications?\b",
    r"\bresponsibilities\b",
    r"\brequirements\b",
]

OUTPUT_JSON_NAME = "public_skill_seed.json"
OUTPUT_REVIEW_CSV_NAME = "public_skill_review.csv"
OUTPUT_CONSTS_NAME = "generated_const_candidates.py"

OUTPUT_LLM_CLEANUP_JSON_NAME = "public_skill_llm_cleanup.json"
OUTPUT_LLM_RECOVERY_JSON_NAME = "public_skill_llm_recovery.json"
OUTPUT_SKIPPED_AUDIT_CSV_NAME = "public_skill_skipped_audit.csv"
OUTPUT_RECOVERED_REVIEW_CSV_NAME = "public_skill_recovered_review.csv"
OUTPUT_LLM_CACHE_DIR_NAME = "llm_cache"

_HEADER_LIKE_VALUES = {
    "skill",
    "skills",
    "raw_skill",
    "raw_skills",
    "keyword",
    "keywords",
    "term",
    "terms",
}

DEFAULT_LLM_PROVIDER = "groq"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_LLM_MAX_TOKENS = 500
DEFAULT_LLM_TEMPERATURE = 0.0
DEFAULT_LLM_TIMEOUT_SECONDS = 30
DEFAULT_LLM_PROMPT_VERSION = "v1"

ANALYTICS_HINT_PATTERNS = [
    "machine learning",
    "deep learning",
    "model",
    "modeling",
    "regression",
    "classification",
    "forecast",
    "forecasting",
    "statistics",
    "statistical",
    "bayesian",
    "causal inference",
    "hypothesis testing",
    "experiment",
    "experimentation",
    "a/b testing",
    "random forest",
    "svm",
    "xgboost",
    "lightgbm",
    "catboost",
    "nlp",
    "natural language processing",
    "computer vision",
    "time series",
    "data mining",
    "statistical analysis",
    "data modeling",
    "predictive models",
    "predictive modeling",
    "time series",
]

TOOLING_HINT_PATTERNS = [
    "python",
    "sql",
    "r",
    "sas",
    "tableau",
    "looker",
    "power bi",
    "airflow",
    "dbt",
    "snowflake",
    "bigquery",
    "databricks",
    "spark",
    "pytorch",
    "tensorflow",
    "jupyter",
    "git",
    "github",
    "gitlab",
    "version control",
    "docker",
    "kubernetes",
    "aws",
    "gcp",
    "azure",
    "hadoop",
    "hive",
    "impala",
    "mysql",
    "sql server",
    "oracle",
    "linux",
    "redshift",
    "mongodb",
    "cassandra",
    "couchbase",
    "jenkins",
    "javascript",
    "java",
    "scala",
    "bash",
    "matlab",
]

GENERIC_JUNK_TERMS = {
    "agile",
    "ai",
    "architecture",
    "automated",
    "big data",
    "data science",
    "mathematical",
    "metrics",
    "networks",
    "physics",
    "project",
    "security",
}

BASELINE_FAMILY_HINTS: Dict[str, List[str]] = {
    "notebook_workflow": [
        "jupyter",
        "notebook",
        "notebooks",
        "google colab",
        "colab",
        "ipynb",
    ],
    "version_control": [
        "git",
        "github",
        "gitlab",
        "bitbucket",
        "version control",
        "source control",
        "source code management",
    ],
    "classical_ml_methods": [
        "random forest",
        "svm",
        "support vector machine",
        "support vector machines",
        "xgboost",
        "lightgbm",
        "catboost",
        "decision tree",
        "decision trees",
        "logistic regression",
        "linear regression",
        "clustering",
        "k means",
        "k-means",
        "pca",
    ],
    "model_development_basics": [
        "machine learning",
        "deep learning",
        "feature engineering",
        "model training",
        "model evaluation",
        "hyperparameter tuning",
        "cross validation",
        "cross-validation",
        "feature selection",
        "model deployment",
    ],
}

RECOVERABLE_SKIP_REASONS = {
    "too_many_tokens",
    "stack_blob",
    "mixed_numeric_phrase",
    "long_freeform_phrase",
}

GENERIC_NON_SKILL_TERMS = {
    "administration",
    "agile",
    "algorithms",
    "analysis",
    "analytics",
    "artificial intelligence",
    "claims",
    "data",
    "data scientist",
    "database",
    "development",
    "machine learning",
    "management",
    "modeling",
    "natural language processing",
    "programming",
    "project",
    "python",
    "r",
    "research",
    "sas",
    "security",
    "spark",
    "sql",
    "statistics",
    "testing",
    "transform",
}

def _normalize_text(value: str) -> str:
    text = str(value or "").lower().strip()
    if not text:
        return ""

    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9+/\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    previous = None
    while text and text != previous:
        previous = text
        text = NORMALIZATION_MAP.get(text, text)
        text = ALIAS_MAP.get(text, text)

    return text


def _contains_pattern(text: str, pattern: str) -> bool:
    normalized_text = _normalize_text(text)
    normalized_pattern = _normalize_text(pattern)
    if not normalized_text or not normalized_pattern:
        return False
    return re.search(rf"\b{re.escape(normalized_pattern)}\b", normalized_text) is not None


def _looks_like_header(cell: str) -> bool:
    normalized = _normalize_text(cell)
    return normalized in _HEADER_LIKE_VALUES


def _split_cell(cell: str) -> List[str]:
    value = str(cell or "").strip()
    if not value:
        return []

    # Split only on delimiters commonly used for list-like cells.
    # Do not split on "/" because terms like "a/b testing" and "r/python" may be meaningful.
    if ";" in value or "|" in value or "," in value:
        parts = re.split(r"[;|,]+", value)
        return [part.strip() for part in parts if part.strip()]

    return [value]


def _fetch_csv_text(csv_path: str, csv_url: str) -> str:
    if csv_path.strip():
        path = Path(csv_path)
        if not path.exists():
            raise RuntimeError(f"CSV path does not exist: {path}")
        return path.read_text(encoding="utf-8")

    if csv_url.strip():
        with urllib.request.urlopen(csv_url, timeout=30) as response:
            return response.read().decode("utf-8")

    raise RuntimeError("Provide either --csv-path or --csv-url")


def _extract_raw_terms(csv_text: str) -> List[str]:
    rows = list(csv.reader(csv_text.splitlines()))
    terms: List[str] = []

    for row_idx, row in enumerate(rows):
        if not row:
            continue

        # If the first row looks like a header, skip it.
        if row_idx == 0 and all(_looks_like_header(cell) for cell in row if str(cell).strip()):
            continue

        for cell in row:
            for part in _split_cell(cell):
                cleaned = str(part or "").strip()
                if cleaned:
                    terms.append(cleaned)

    return terms


def _skip_reason(normalized: str) -> Optional[str]:
    if not normalized:
        return "empty_after_normalization"

    if len(normalized) < 2:
        return "too_short"

    if len(normalized) > 80:
        return "too_long"

    if normalized in DROP_EXACT:
        return "drop_exact"

    if re.search(r"https?://|www\.", normalized):
        return "url_like"

    if re.fullmatch(r"\d+", normalized):
        return "numeric_only"

    if re.fullmatch(r"[a-z]\d+|v\d+", normalized):
        return "version_or_code_like"

    for pattern in INVALID_SKILL_PATTERNS:
        if re.search(pattern, normalized):
            return "invalid_skill_pattern"

    if normalized in {"and", "or", "with", "using"}:
        return "connector_word"

    tokens = normalized.split()

    if len(tokens) >= 8:
        return "too_many_tokens"

    if sum(1 for token in tokens if token in {"python", "sql", "r", "sas", "java", "c++"}) >= 3 and len(tokens) >= 5:
        return "stack_blob"

    if any(token.isdigit() for token in tokens) and len(tokens) >= 4:
        return "mixed_numeric_phrase"

    if len(tokens) >= 5 and not any(
        phrase in normalized
        for phrase in (
            "machine learning",
            "deep learning",
            "natural language processing",
            "computer vision",
            "a/b testing",
            "version control",
            "power bi",
        )
    ):
        return "long_freeform_phrase"

    return None


def _sorted_set(values: Set[str]) -> List[str]:
    return sorted(values, key=lambda value: (value.lower(), value))


def _classify_baseline_families(term: str) -> List[str]:
    matches: List[str] = []
    for family_name, patterns in BASELINE_FAMILY_HINTS.items():
        if any(_contains_pattern(term, pattern) for pattern in patterns):
            matches.append(family_name)
    return sorted(matches)


def _is_candidate_analytics_ml(term: str, existing_analytics: Set[str]) -> bool:
    if term in existing_analytics:
        return False
    return any(_contains_pattern(term, pattern) for pattern in ANALYTICS_HINT_PATTERNS)


def _is_candidate_tooling(term: str, existing_tooling: Set[str]) -> bool:
    if term in existing_tooling:
        return False
    return any(_contains_pattern(term, pattern) for pattern in TOOLING_HINT_PATTERNS)

def _is_promotable_candidate_term(
    term: str,
    *,
    existing_common: Set[str],
    existing_analytics: Set[str],
    existing_tooling: Set[str],
) -> bool:
    if not term:
        return False

    if term in GENERIC_NON_SKILL_TERMS:
        return False

    if term in GENERIC_JUNK_TERMS:
        return False

    if term in existing_common or term in existing_analytics or term in existing_tooling:
        return False

    tokens = term.split()

    if len(tokens) >= 5:
        return False

    banned_subphrases = [
        "data scientist",
        "analyst",
        "engineer",
        "manager",
        "required",
        "experience",
        "skills",
        "knowledge",
        "work environment",
    ]
    if any(fragment in term for fragment in banned_subphrases):
        return False

    if len(tokens) == 1:
        allowed_singletons = {
            "hadoop",
            "hive",
            "impala",
            "mysql",
            "oracle",
            "linux",
            "tableau",
            "tensorflow",
            "mongodb",
            "cassandra",
            "couchbase",
            "jenkins",
            "javascript",
            "java",
            "scala",
            "bash",
            "matlab",
            "nosql",
            "aws",
            "docker",
            "kubernetes",
            "airflow",
            "spark",
            "git",
            "github",
            "gitlab",
            "redshift",
            "snowflake",
            "dbt",
            "sqlserver",
            "cplusplus",
            "c++",
        }
        return term in allowed_singletons

    strong_multiword_markers = [
        "server",
        "database",
        "analysis",
        "modeling",
        "models",
        "mining",
        "vision",
        "language processing",
        "time series",
        "neural",
        "learning",
        "regression",
        "classification",
    ]
    return any(marker in term for marker in strong_multiword_markers)

def _render_python_literal(value) -> str:
    return json.dumps(value, indent=4, ensure_ascii=False)

def _needs_llm_cleanup(term: str) -> bool:
    normalized = _normalize_text(term)
    if not normalized:
        return False

    tokens = normalized.split()

    if len(tokens) >= 4:
        return True

    if "/" in normalized and normalized not in {"a/b testing"}:
        return True

    if "-" in normalized and len(tokens) >= 3:
        return True

    if any(
        phrase in normalized
        for phrase in [
            " and ",
            " or ",
            " with ",
            " using ",
        ]
    ) and len(tokens) >= 3:
        return True

    return False


def _strip_json_fences(text: str) -> str:
    value = str(text or "").strip()
    if not value:
        return ""

    if value.startswith("```"):
        lines = value.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        if lines and lines[0].strip().lower() == "json":
            lines = lines[1:]

        value = "\n".join(lines).strip()

    return value


def _cleanup_cache_key(model: str, raw_term: str) -> str:
    payload = {
        "prompt_version": DEFAULT_LLM_PROMPT_VERSION,
        "provider": DEFAULT_LLM_PROVIDER,
        "model": model,
        "raw_term": raw_term,
    }
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    import hashlib
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _cleanup_cache_path(cache_dir: Path, cache_key: str) -> Path:
    return cache_dir / f"{cache_key}.json"


def _load_cleanup_cache(cache_dir: Path, cache_key: str) -> Optional[dict]:
    path = _cleanup_cache_path(cache_dir, cache_key)
    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if not isinstance(payload, dict):
        return None

    payload["cache_hit"] = True
    return payload


def _write_cleanup_cache(cache_dir: Path, cache_key: str, payload: dict) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cleanup_cache_path(cache_dir, cache_key)

    cached_payload = dict(payload)
    cached_payload["cache_hit"] = False
    path.write_text(json.dumps(cached_payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not found in environment")
    return Groq(api_key=api_key)


def _build_cleanup_messages(raw_term: str) -> List[dict]:
    system_prompt = """
You clean noisy job-skill phrases into atomic skill terms.

Rules:
1. Use ONLY the provided raw phrase.
2. Do NOT invent new skills that are not directly supported by the raw phrase.
3. Split multi-skill phrases into atomic, meaningful skill/tool/method terms.
4. Remove role names, seniority, hiring noise, generic filler, and sentence fragments.
5. Keep terms compact and lowercase-friendly.
6. Return ONLY valid JSON.
7. If nothing useful is present, return an empty skills list.

Return JSON with:
- raw_term: original input phrase
- cleaned_skills: array of atomic skill strings
- dropped_fragments: array of dropped noise fragments
- reasoning: short explanation
""".strip()

    user_prompt = f"Raw phrase:\n{raw_term}"
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _parse_cleanup_response(text: str) -> dict:
    cleaned = _strip_json_fences(text)
    if not cleaned:
        raise ValueError("Empty LLM cleanup response")

    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("LLM cleanup response is not a JSON object")

    cleaned_skills = parsed.get("cleaned_skills", [])
    dropped_fragments = parsed.get("dropped_fragments", [])
    reasoning = str(parsed.get("reasoning", "")).strip()
    raw_term = str(parsed.get("raw_term", "")).strip()

    if not isinstance(cleaned_skills, list):
        raise ValueError("cleaned_skills must be a list")
    if not isinstance(dropped_fragments, list):
        raise ValueError("dropped_fragments must be a list")

    normalized_skills: List[str] = []
    for value in cleaned_skills:
        skill = _normalize_text(str(value or ""))
        if not skill:
            continue
        if skill not in normalized_skills:
            normalized_skills.append(skill)

    normalized_drops: List[str] = []
    for value in dropped_fragments:
        frag = _normalize_text(str(value or ""))
        if not frag:
            continue
        if frag not in normalized_drops:
            normalized_drops.append(frag)

    return {
        "raw_term": raw_term,
        "cleaned_skills": normalized_skills,
        "dropped_fragments": normalized_drops,
        "reasoning": reasoning,
    }

def _build_recovery_messages(raw_term: str, skip_reason: str) -> List[dict]:
    system_prompt = """
You recover atomic skill terms from a noisy phrase that was previously filtered out.

Rules:
1. Use ONLY the provided raw phrase.
2. Do NOT invent new skills, tools, methods, or domains.
3. Extract only atomic, meaningful skill/tool/method terms.
4. Drop role names, departments, generic business words, filler, and sentence fragments.
5. Return ONLY valid JSON.
6. If the phrase contains no reliable recoverable skills, return an empty recovered_skills list.

Return JSON with:
- raw_term: original input phrase
- skip_reason: original filter reason
- recovered_skills: array of atomic recovered skill strings
- dropped_fragments: array of dropped noise fragments
- reasoning: short explanation
""".strip()

    user_prompt = f"Skip reason: {skip_reason}\nRaw phrase:\n{raw_term}"
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _parse_recovery_response(text: str) -> dict:
    cleaned = _strip_json_fences(text)
    if not cleaned:
        raise ValueError("Empty LLM recovery response")

    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("LLM recovery response is not a JSON object")

    recovered_skills = parsed.get("recovered_skills", [])
    dropped_fragments = parsed.get("dropped_fragments", [])
    reasoning = str(parsed.get("reasoning", "")).strip()
    raw_term = str(parsed.get("raw_term", "")).strip()
    skip_reason = str(parsed.get("skip_reason", "")).strip()

    if not isinstance(recovered_skills, list):
        raise ValueError("recovered_skills must be a list")
    if not isinstance(dropped_fragments, list):
        raise ValueError("dropped_fragments must be a list")

    normalized_skills: List[str] = []
    for value in recovered_skills:
        skill = _normalize_text(str(value or ""))
        if not skill:
            continue
        if skill not in normalized_skills:
            normalized_skills.append(skill)

    normalized_drops: List[str] = []
    for value in dropped_fragments:
        frag = _normalize_text(str(value or ""))
        if not frag:
            continue
        if frag not in normalized_drops:
            normalized_drops.append(frag)

    return {
        "raw_term": raw_term,
        "skip_reason": skip_reason,
        "recovered_skills": normalized_skills,
        "dropped_fragments": normalized_drops,
        "reasoning": reasoning,
    }


def _run_groq_recovery(raw_term: str, skip_reason: str, model: str, max_tokens: int) -> dict:
    client = _get_groq_client()
    messages = _build_recovery_messages(raw_term, skip_reason)

    response = client.chat.completions.create(
        model=model,
        temperature=DEFAULT_LLM_TEMPERATURE,
        max_tokens=max_tokens,
        messages=messages,
    )

    content = response.choices[0].message.content
    return _parse_recovery_response(content)

def _run_groq_cleanup(raw_term: str, model: str, max_tokens: int) -> dict:
    client = _get_groq_client()
    messages = _build_cleanup_messages(raw_term)

    response = client.chat.completions.create(
        model=model,
        temperature=DEFAULT_LLM_TEMPERATURE,
        max_tokens=max_tokens,
        messages=messages,
    )

    content = response.choices[0].message.content
    return _parse_cleanup_response(content)

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Offline public skill taxonomy mining utility. "
            "Generates candidate review artifacts only and never edits runtime consts."
        )
    )
    parser.add_argument(
        "--csv-path",
        default="",
        help="Optional local CSV path containing one or more raw skill columns.",
    )
    parser.add_argument(
        "--csv-url",
        default="",
        help="Optional remote CSV URL to download and mine.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/skill_taxonomy/public_seed",
        help="Directory for generated review artifacts.",
    )
    parser.add_argument(
        "--use-llm-cleanup",
        action="store_true",
        help="Use Groq to split noisy composite phrases into atomic skill candidates.",
    )
    parser.add_argument(
        "--llm-model",
        default=DEFAULT_GROQ_MODEL,
        help="Groq model for optional cleanup.",
    )
    parser.add_argument(
        "--llm-max-tokens",
        type=int,
        default=DEFAULT_LLM_MAX_TOKENS,
        help="Max output tokens for optional cleanup calls.",
    )
    parser.add_argument(
        "--llm-cleanup-limit",
        type=int,
        default=100,
        help="Maximum number of noisy terms to send to the LLM. Use 0 for all.",
    )
    parser.add_argument(
        "--use-llm-recovery",
        action="store_true",
        help="Recover atomic skill candidates from filtered noisy phrases using Groq.",
    )
    parser.add_argument(
        "--llm-recovery-limit",
        type=int,
        default=120,
        help="Maximum number of recoverable skipped phrases to send to the LLM. Use 0 for all.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    llm_cache_dir = output_dir / OUTPUT_LLM_CACHE_DIR_NAME
    llm_cleanup_results: List[dict] = []
    llm_recovery_results: List[dict] = []
    suppressed_accepted_source_terms: Set[str] = set()

    csv_text = _fetch_csv_text(args.csv_path, args.csv_url)
    raw_terms = _extract_raw_terms(csv_text)

    existing_common = {_normalize_text(value) for value in COMMON_SKILL_PATTERNS if _normalize_text(value)}
    existing_analytics = {_normalize_text(value) for value in ANALYTICS_ML_SIGNAL_PATTERNS if _normalize_text(value)}
    existing_tooling = {_normalize_text(value) for value in TOOLING_SIGNAL_PATTERNS if _normalize_text(value)}

    accepted_counter: Counter[str] = Counter()
    raw_examples: DefaultDict[str, List[str]] = defaultdict(list)
    skip_counter: Counter[str] = Counter()
    skipped_counter: Counter[Tuple[str, str]] = Counter()
    skipped_raw_examples: DefaultDict[Tuple[str, str], List[str]] = defaultdict(list)

    for raw_term in raw_terms:
        normalized = _normalize_text(raw_term)
        reason = _skip_reason(normalized)

        if reason is not None:
            skip_counter[reason] += 1
            skipped_counter[(normalized, reason)] += 1
            key = (normalized, reason)
            if len(skipped_raw_examples[key]) < 5 and raw_term not in skipped_raw_examples[key]:
                skipped_raw_examples[key].append(raw_term)
            continue

        accepted_counter[normalized] += 1
        if len(raw_examples[normalized]) < 5 and raw_term not in raw_examples[normalized]:
            raw_examples[normalized].append(raw_term)

    accepted_terms = set(accepted_counter.keys())

    llm_candidate_terms = [
        term
        for term in sorted(accepted_terms, key=lambda value: (-accepted_counter[value], value))
        if _needs_llm_cleanup(term)
    ]

    if args.llm_cleanup_limit > 0:
        llm_candidate_terms = llm_candidate_terms[:args.llm_cleanup_limit]

    if args.use_llm_cleanup:
        expanded_terms: Counter[str] = Counter()

        for term in llm_candidate_terms:
            cache_key = _cleanup_cache_key(args.llm_model, term)
            cached = _load_cleanup_cache(llm_cache_dir, cache_key)

            if cached is not None:
                llm_cleanup_results.append(cached)
                cleaned_skills = cached.get("cleaned_skills", [])
                if cleaned_skills:
                    suppressed_accepted_source_terms.add(term)
                for cleaned_skill in cleaned_skills:
                    expanded_terms[cleaned_skill] += accepted_counter[term]
                    if len(raw_examples[cleaned_skill]) < 5 and term not in raw_examples[cleaned_skill]:
                        raw_examples[cleaned_skill].append(term)
                continue

            try:
                parsed = _run_groq_cleanup(
                    raw_term=term,
                    model=args.llm_model,
                    max_tokens=args.llm_max_tokens,
                )
                result = {
                    "status": "generated",
                    "provider": "groq",
                    "model": args.llm_model,
                    "raw_term": term,
                    "cleaned_skills": parsed["cleaned_skills"],
                    "dropped_fragments": parsed["dropped_fragments"],
                    "reasoning": parsed["reasoning"],
                    "cache_hit": False,
                }
                _write_cleanup_cache(llm_cache_dir, cache_key, result)
                llm_cleanup_results.append(result)

                if parsed["cleaned_skills"]:
                    suppressed_accepted_source_terms.add(term)

                for cleaned_skill in parsed["cleaned_skills"]:
                    expanded_terms[cleaned_skill] += accepted_counter[term]
                    if len(raw_examples[cleaned_skill]) < 5 and term not in raw_examples[cleaned_skill]:
                        raw_examples[cleaned_skill].append(term)

                time.sleep(0.2)

            except Exception as exc:
                result = {
                    "status": "error",
                    "provider": "groq",
                    "model": args.llm_model,
                    "raw_term": term,
                    "cleaned_skills": [],
                    "dropped_fragments": [],
                    "reasoning": "",
                    "error": str(exc),
                    "cache_hit": False,
                }
                _write_cleanup_cache(llm_cache_dir, cache_key, result)
                llm_cleanup_results.append(result)

        for cleaned_skill, count in expanded_terms.items():
            accepted_counter[cleaned_skill] += count

        accepted_terms = set(accepted_counter.keys())

    skipped_audit_rows: List[dict] = []
    for (normalized_term, reason), count in sorted(
        skipped_counter.items(),
        key=lambda item: (-item[1], item[0][1], item[0][0]),
    ):
        skipped_audit_rows.append(
            {
                "normalized_term": normalized_term,
                "skip_reason": reason,
                "count": count,
                "raw_examples": " | ".join(skipped_raw_examples.get((normalized_term, reason), [])),
                "recoverable": str(reason in RECOVERABLE_SKIP_REASONS),
            }
        )

    recovery_candidates = [
        row for row in skipped_audit_rows
        if row["recoverable"] == "True" and row["normalized_term"]
    ]

    if args.llm_recovery_limit > 0:
        recovery_candidates = recovery_candidates[:args.llm_recovery_limit]

    recovered_counter: Counter[str] = Counter()
    recovered_examples: DefaultDict[str, List[str]] = defaultdict(list)

    if args.use_llm_recovery:
        for row in recovery_candidates:
            raw_term = row["normalized_term"]
            skip_reason = row["skip_reason"]
            cache_key = _cleanup_cache_key(args.llm_model, f"recovery::{skip_reason}::{raw_term}")
            cached = _load_cleanup_cache(llm_cache_dir, cache_key)

            if cached is not None:
                llm_recovery_results.append(cached)
                for recovered_skill in cached.get("recovered_skills", []):
                    recovered_counter[recovered_skill] += int(row["count"])
                    if raw_term not in recovered_examples[recovered_skill]:
                        recovered_examples[recovered_skill].append(raw_term)
                    if len(raw_examples[recovered_skill]) < 5 and raw_term not in raw_examples[recovered_skill]:
                        raw_examples[recovered_skill].append(raw_term)
                continue

            try:
                parsed = _run_groq_recovery(
                    raw_term=raw_term,
                    skip_reason=skip_reason,
                    model=args.llm_model,
                    max_tokens=args.llm_max_tokens,
                )
                result = {
                    "status": "generated",
                    "provider": "groq",
                    "model": args.llm_model,
                    "raw_term": raw_term,
                    "skip_reason": skip_reason,
                    "recovered_skills": parsed["recovered_skills"],
                    "dropped_fragments": parsed["dropped_fragments"],
                    "reasoning": parsed["reasoning"],
                    "cache_hit": False,
                }
                _write_cleanup_cache(llm_cache_dir, cache_key, result)
                llm_recovery_results.append(result)

                for recovered_skill in parsed["recovered_skills"]:
                    recovered_counter[recovered_skill] += int(row["count"])
                    if raw_term not in recovered_examples[recovered_skill]:
                        recovered_examples[recovered_skill].append(raw_term)
                    if len(raw_examples[recovered_skill]) < 5 and raw_term not in raw_examples[recovered_skill]:
                        raw_examples[recovered_skill].append(raw_term)

                time.sleep(0.2)

            except Exception as exc:
                result = {
                    "status": "error",
                    "provider": "groq",
                    "model": args.llm_model,
                    "raw_term": raw_term,
                    "skip_reason": skip_reason,
                    "recovered_skills": [],
                    "dropped_fragments": [],
                    "reasoning": "",
                    "error": str(exc),
                    "cache_hit": False,
                }
                _write_cleanup_cache(llm_cache_dir, cache_key, result)
                llm_recovery_results.append(result)

        for recovered_skill, count in recovered_counter.items():
            accepted_counter[recovered_skill] += count

        accepted_terms = set(accepted_counter.keys())

    recovered_review_rows: List[dict] = []
    for recovered_skill, count in sorted(
        recovered_counter.items(),
        key=lambda item: (-item[1], item[0]),
    ):
        recovered_review_rows.append(
            {
                "recovered_skill": recovered_skill,
                "count": count,
                "source_examples": " | ".join(recovered_examples.get(recovered_skill, [])[:5]),
            }
        )

    filtered_candidate_terms = {
        term
        for term in accepted_terms
        if term not in suppressed_accepted_source_terms and term not in GENERIC_NON_SKILL_TERMS
    }
        
    candidate_common_skills: Set[str] = set()
    candidate_analytics_ml_signals: Set[str] = set()
    candidate_tooling_signals: Set[str] = set()
    candidate_baseline_families: Dict[str, Set[str]] = {
        family_name: set()
        for family_name in BASELINE_FAMILY_HINTS.keys()
    }

    review_rows: List[dict] = []

    for term in sorted(filtered_candidate_terms, key=lambda value: (-accepted_counter[value], value)):
        baseline_families = _classify_baseline_families(term)
        promotable = _is_promotable_candidate_term(
            term,
            existing_common=existing_common,
            existing_analytics=existing_analytics,
            existing_tooling=existing_tooling,
        )
        propose_common = False
        propose_analytics = promotable and _is_candidate_analytics_ml(term, existing_analytics)
        propose_tooling = promotable and _is_candidate_tooling(term, existing_tooling)

        if propose_common:
            candidate_common_skills.add(term)
        if propose_analytics:
            candidate_analytics_ml_signals.add(term)
        if propose_tooling:
            candidate_tooling_signals.add(term)
        if promotable:
            for family_name in baseline_families:
                candidate_baseline_families[family_name].add(term)

        review_rows.append(
            {
                "term": term,
                "count": accepted_counter[term],
                "raw_examples": " | ".join(raw_examples.get(term, [])),
                "already_in_common_skills": str(term in existing_common),
                "already_in_analytics_ml_signals": str(term in existing_analytics),
                "already_in_tooling_signals": str(term in existing_tooling),
                "candidate_common_skill": str(propose_common),
                "candidate_analytics_ml_signal": str(propose_analytics),
                "candidate_tooling_signal": str(propose_tooling),
                "candidate_baseline_families": ",".join(baseline_families),
                "promotable": str(promotable),
            }
        )

    candidate_baseline_families_sorted = {
        family_name: _sorted_set(values)
        for family_name, values in candidate_baseline_families.items()
    }

    payload = {
        "source": {
            "csv_path": args.csv_path,
            "csv_url": args.csv_url,
        },
        "summary": {
            "raw_term_count": len(raw_terms),
            "accepted_unique_terms": len(accepted_terms),
            "skipped_total": int(sum(skip_counter.values())),
            "skip_reasons": dict(sorted(skip_counter.items(), key=lambda item: item[0])),
            "suppressed_accepted_source_terms": len(suppressed_accepted_source_terms),
            "filtered_generic_non_skill_terms": len(accepted_terms & GENERIC_NON_SKILL_TERMS),
        },
        "accepted_terms_all": _sorted_set(accepted_terms),
        "existing_runtime_overlap": {
            "common_skills_overlap": _sorted_set(accepted_terms & existing_common),
            "analytics_ml_signals_overlap": _sorted_set(accepted_terms & existing_analytics),
            "tooling_signals_overlap": _sorted_set(accepted_terms & existing_tooling),
        },
        "candidate_const_buckets": {
            "candidate_common_skills": _sorted_set(candidate_common_skills),
            "candidate_analytics_ml_signals": _sorted_set(candidate_analytics_ml_signals),
            "candidate_tooling_signals": _sorted_set(candidate_tooling_signals),
            "candidate_baseline_familiarity_families": candidate_baseline_families_sorted,
            "candidate_recovered_skills": _sorted_set(set(recovered_counter.keys())),
        },
        "llm_cleanup": {
            "enabled": bool(args.use_llm_cleanup),
            "provider": "groq" if args.use_llm_cleanup else "",
            "model": args.llm_model if args.use_llm_cleanup else "",
            "candidate_term_count": len(llm_candidate_terms),
            "result_count": len(llm_cleanup_results),
        },
        "llm_recovery": {
            "enabled": bool(args.use_llm_recovery),
            "provider": "groq" if args.use_llm_recovery else "",
            "model": args.llm_model if args.use_llm_recovery else "",
            "candidate_term_count": len(recovery_candidates),
            "result_count": len(llm_recovery_results),
            "recovered_unique_skill_count": len(recovered_counter),
        },
    }

    json_path = output_dir / OUTPUT_JSON_NAME
    review_csv_path = output_dir / OUTPUT_REVIEW_CSV_NAME
    consts_path = output_dir / OUTPUT_CONSTS_NAME
    llm_cleanup_json_path = output_dir / OUTPUT_LLM_CLEANUP_JSON_NAME
    llm_recovery_json_path = output_dir / OUTPUT_LLM_RECOVERY_JSON_NAME
    skipped_audit_csv_path = output_dir / OUTPUT_SKIPPED_AUDIT_CSV_NAME
    recovered_review_csv_path = output_dir / OUTPUT_RECOVERED_REVIEW_CSV_NAME

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    
    with llm_cleanup_json_path.open("w", encoding="utf-8") as f:
        json.dump(llm_cleanup_results, f, indent=2, ensure_ascii=False)
    
    with llm_recovery_json_path.open("w", encoding="utf-8") as f:
        json.dump(llm_recovery_results, f, indent=2, ensure_ascii=False)

    with skipped_audit_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "normalized_term",
                "skip_reason",
                "count",
                "raw_examples",
                "recoverable",
            ],
        )
        writer.writeheader()
        writer.writerows(skipped_audit_rows)

    with recovered_review_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "recovered_skill",
                "count",
                "source_examples",
            ],
        )
        writer.writeheader()
        writer.writerows(recovered_review_rows)

    with review_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "term",
                "count",
                "raw_examples",
                "already_in_common_skills",
                "already_in_analytics_ml_signals",
                "already_in_tooling_signals",
                "promotable",
                "candidate_common_skill",
                "candidate_analytics_ml_signal",
                "candidate_tooling_signal",
                "candidate_baseline_families",
            ],
        )
        writer.writeheader()
        writer.writerows(review_rows)

    generated_lines: List[str] = []
    generated_lines.append('"""')
    generated_lines.append("Generated candidate consts from a public skill source.")
    generated_lines.append("Review only. Do not import this file into runtime scoring.")
    generated_lines.append('"""')
    generated_lines.append("")
    generated_lines.append(
        f"PUBLIC_SKILL_ACCEPTED_TERMS = {_render_python_literal(payload['accepted_terms_all'])}"
    )
    generated_lines.append("")
    generated_lines.append(
        "PUBLIC_SKILL_NEW_COMMON_SKILL_CANDIDATES = "
        + _render_python_literal(payload["candidate_const_buckets"]["candidate_common_skills"])
    )
    generated_lines.append("")
    generated_lines.append(
        "PUBLIC_SKILL_NEW_ANALYTICS_ML_SIGNAL_CANDIDATES = "
        + _render_python_literal(payload["candidate_const_buckets"]["candidate_analytics_ml_signals"])
    )
    generated_lines.append("")
    generated_lines.append(
        "PUBLIC_SKILL_NEW_TOOLING_SIGNAL_CANDIDATES = "
        + _render_python_literal(payload["candidate_const_buckets"]["candidate_tooling_signals"])
    )
    generated_lines.append("")
    generated_lines.append(
        "PUBLIC_SKILL_NEW_BASELINE_FAMILIARITY_FAMILIES = "
        + _render_python_literal(payload["candidate_const_buckets"]["candidate_baseline_familiarity_families"])
    )
    generated_lines.append("")
    generated_lines.append(
        "PUBLIC_SKILL_RECOVERED_SKILL_CANDIDATES = "
        + _render_python_literal(payload["candidate_const_buckets"]["candidate_recovered_skills"])
    )
    generated_lines.append("")

    consts_path.write_text("\n".join(generated_lines), encoding="utf-8")

    print()
    print("=" * 100)
    print("PUBLIC SKILL SEED GENERATION COMPLETE")
    print("=" * 100)
    print(f"Raw terms extracted           : {len(raw_terms)}")
    print(f"Accepted unique normalized    : {len(accepted_terms)}")
    print(f"Filtered candidate terms      : {len(filtered_candidate_terms)}")
    print(f"Skipped rows                  : {int(sum(skip_counter.values()))}")
    print(f"Suppressed source blobs       : {len(suppressed_accepted_source_terms)}")
    print(f"Candidate common skills       : {len(candidate_common_skills)}")
    print(f"Candidate analytics/ml signals: {len(candidate_analytics_ml_signals)}")
    print(f"Candidate tooling signals     : {len(candidate_tooling_signals)}")
    print("Candidate baseline families   :")
    for family_name, values in candidate_baseline_families_sorted.items():
        print(f"  - {family_name}: {len(values)}")
    print()
    print(f"JSON written      : {json_path}")
    print(f"Review CSV written: {review_csv_path}")
    print(f"Consts written    : {consts_path}")
    print()

    print(f"LLM cleanup JSON  : {llm_cleanup_json_path}")
    print(f"LLM recovery JSON : {llm_recovery_json_path}")
    print(f"Skipped audit CSV : {skipped_audit_csv_path}")
    print(f"Recovered CSV     : {recovered_review_csv_path}")
    if args.use_llm_cleanup:
        generated = sum(1 for row in llm_cleanup_results if row.get("status") == "generated")
        cached = sum(1 for row in llm_cleanup_results if row.get("cache_hit"))
        errors = sum(1 for row in llm_cleanup_results if row.get("status") == "error")
        print(f"LLM cleanup used  : True")
        print(f"LLM cleanup model : {args.llm_model}")
        print(f"LLM generated     : {generated}")
        print(f"LLM cached        : {cached}")
        print(f"LLM errors        : {errors}")
    else:
        print("LLM cleanup used  : False")
    
    if args.use_llm_recovery:
        generated = sum(1 for row in llm_recovery_results if row.get("status") == "generated")
        cached = sum(1 for row in llm_recovery_results if row.get("cache_hit"))
        errors = sum(1 for row in llm_recovery_results if row.get("status") == "error")
        print(f"LLM recovery used : True")
        print(f"LLM recovery model: {args.llm_model}")
        print(f"LLM recovery gen  : {generated}")
        print(f"LLM recovery cache: {cached}")
        print(f"LLM recovery err  : {errors}")
        print(f"Recovered skills  : {len(recovered_counter)}")
    else:
        print("LLM recovery used : False")

    top_terms = sorted(
        ((term, accepted_counter[term]) for term in filtered_candidate_terms),
        key=lambda item: (-item[1], item[0]),
    )[:20]

    if top_terms:
        print("Top normalized terms:")
        for term, count in top_terms:
            print(f"  {count:>4} | {term}")

    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        raise