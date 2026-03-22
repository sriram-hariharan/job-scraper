import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, List, Set, Tuple


OUTPUT_JSON_NAME = "merged_skill_seed.json"
OUTPUT_TOOLING_CSV_NAME = "merged_tooling_registry_review.csv"
OUTPUT_ANALYTICS_CSV_NAME = "merged_analytics_ml_registry_review.csv"
OUTPUT_BASELINE_CSV_NAME = "merged_baseline_familiarity_review.csv"

# Terms that are already well covered or too generic to be promoted again from mined sources.
ALREADY_SEEDED_RUNTIME_TERMS = {
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
}

GENERIC_REVIEW_EXCLUDE = {
    "adobe acrobat",
    "adobe photoshop",
    "ai",
    "ajax",
    "apple macos",
    "architecture",
    "automated",
    "big data",
    "bookkeeping software",
    "business intelligence software",
    "data scientist",
    "electronic health record ehr software",
    "esri arcgis software",
    "extensible markup language xml",
    "javascript",
    "mathematical",
    "metrics",
    "microsoft access",
    "microsoft excel",
    "microsoft sharepoint",
    "microsoft visio",
    "networks",
    "oracle",
    "physics",
    "project",
    "salesforce software",
    "sap software",
    "security",
}

ONET_TECH_NORMALIZATION = {
    "amazon web services aws software": "aws",
    "amazon web services aws cloudformation": "aws cloudformation",
    "amazon dynamodb": "dynamodb",
    "amazon elastic compute cloud ec2": "ec2",
    "amazon redshift": "redshift",
    "apache airflow": "airflow",
    "apache hadoop": "hadoop",
    "apache hive": "hive",
    "apache kafka": "kafka",
    "apache spark": "spark",
    "apache subversion svn": "svn",
    "atlassian jira": "jira",
    "ibm spss statistics": "spss",
    "ibm terraform": "terraform",
    "microsoft azure software": "azure",
    "microsoft power bi": "power bi",
    "microsoft sql server": "sql server",
    "oracle java": "java",
    "oracle cloud software": "oracle cloud",
    "structured query language sql": "sql",
    "the mathworks matlab": "matlab",
}

PUBLIC_TERM_NORMALIZATION = {
    "support vector machine": "svm",
    "support vector machines": "svm",
    "random forests": "random forest",
    "natural language processing": "natural language processing",
    "predictive models": "predictive modeling",
    "machine learning algorithms": "machine learning algorithms",
}

MERGED_TERM_NORMALIZATION = {
    "alteryx software": "alteryx",
    "ansible software": "ansible",
    "apache cassandra": "cassandra",
    "building predictive models": "predictive modeling",
    "deep learning networks": "deep learning",
    "ibm db2": "db2",
    "machine learning - python": "machine learning",
    "machine learning aml python": "azure machine learning",
    "machine learning jda software": "jda",
    "machine learning ml": "machine learning",
    "machine learning models": "machine learning",
    "modeling - python": "modeling",
    "python - machine learning": "machine learning",
    "salesforce software": "salesforce",
    "sap software": "sap",
    "spark - machine learning": "spark",
    "sql and relational databases": "sql",
    "sql tableau marketing analysis": "tableau",
    "statistical analysis/modeling": "statistical analysis",
    "statistics/data modeling": "data modeling",
}

def _normalize_text(value: str) -> str:
    text = str(value or "").lower().strip()
    if not text:
        return ""
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9+#/\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_term(value: str) -> str:
    text = _normalize_text(value)
    if not text:
        return ""

    previous = None
    while text != previous:
        previous = text
        text = ONET_TECH_NORMALIZATION.get(text, text)
        text = PUBLIC_TERM_NORMALIZATION.get(text, text)
        text = MERGED_TERM_NORMALIZATION.get(text, text)

    return text


def _is_valid_candidate(term: str) -> bool:
    if not term:
        return False
    if term in ALREADY_SEEDED_RUNTIME_TERMS:
        return False
    if term in GENERIC_REVIEW_EXCLUDE:
        return False
    if len(term) < 2:
        return False
    if len(term.split()) > 4:
        return False
    banned = [
        "data scientist",
        "analyst",
        "engineer",
        "manager",
        "specialist",
        "experience",
        "required",
        "skills",
        "knowledge",
    ]
    if any(fragment in term for fragment in banned):
        return False
    return True


def _tooling_score_markers(term: str) -> bool:
    tooling_markers = [
        "server",
        "sql",
        "hadoop",
        "hive",
        "spark",
        "linux",
        "scala",
        "java",
        "matlab",
        "mongodb",
        "cassandra",
        "couchbase",
        "redshift",
        "aws",
        "azure",
        "docker",
        "kubernetes",
        "jenkins",
        "jira",
        "mysql",
        "oracle cloud",
        "ec2",
        "dynamodb",
        "airflow",
        "kafka",
        "terraform",
        "svn",
    ]
    return any(marker in term for marker in tooling_markers)


def _analytics_ml_score_markers(term: str) -> bool:
    analytics_markers = [
        "data mining",
        "statistical analysis",
        "data modeling",
        "predictive modeling",
        "machine learning algorithms",
        "random forest",
        "svm",
        "time series",
        "classification",
        "regression",
        "modeling",
        "nlp",
        "natural language processing",
    ]
    return any(marker in term for marker in analytics_markers)

def _should_keep_tooling_candidate(
    term: str,
    *,
    onet_support: int,
    public_tooling_candidate: bool,
    public_recovered_count: int,
) -> bool:
    if not _is_valid_candidate(term):
        return False

    if term in GENERIC_REVIEW_EXCLUDE:
        return False

    strong_keep = {
        "alteryx",
        "ansible",
        "aws",
        "azure",
        "azure machine learning",
        "bash",
        "c++",
        "cassandra",
        "couchbase",
        "docker",
        "dynamodb",
        "ec2",
        "hadoop",
        "hive",
        "impala",
        "java",
        "jenkins",
        "jira",
        "kafka",
        "kubernetes",
        "linux",
        "matlab",
        "mongodb",
        "mysql",
        "oracle cloud",
        "redshift",
        "scala",
        "splunk enterprise",
        "sql server",
        "terraform",
    }

    if term in strong_keep:
        return True

    return onet_support >= 2 or public_tooling_candidate or public_recovered_count >= 2


def _should_keep_analytics_candidate(
    term: str,
    *,
    public_analytics_candidate: bool,
    public_recovered_count: int,
) -> bool:
    if not _is_valid_candidate(term):
        return False

    if term in GENERIC_REVIEW_EXCLUDE:
        return False

    strong_keep = {
        "bayesian hierarchical modeling",
        "data mining",
        "data modeling",
        "linear regression",
        "logistic regression",
        "machine learning algorithms",
        "natural language processing",
        "predictive modeling",
        "statistical analysis",
    }

    if term in strong_keep:
        return True

    return public_analytics_candidate and public_recovered_count >= 1

def _sorted_terms(values: Set[str]) -> List[str]:
    return sorted(values, key=lambda x: (x.lower(), x))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv_rows(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge reviewed O*NET and public skill seed artifacts into const-ready candidate review layers."
    )
    parser.add_argument(
        "--onet-dir",
        default="outputs/skill_taxonomy/onet_seed_v4",
        help="Directory containing O*NET v4 seed artifacts.",
    )
    parser.add_argument(
        "--public-dir",
        default="outputs/skill_taxonomy/public_seed_github_recovery_v4",
        help="Directory containing public seed v4 artifacts.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/skill_taxonomy/merged_seed_v1",
        help="Directory for merged review artifacts.",
    )
    args = parser.parse_args()

    onet_dir = Path(args.onet_dir)
    public_dir = Path(args.public_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    onet_json_path = onet_dir / "onet_skill_seed.json"
    onet_agg_path = onet_dir / "onet_target_family_tech_aggregate.csv"
    public_json_path = public_dir / "public_skill_seed.json"
    public_recovered_csv_path = public_dir / "public_skill_recovered_review.csv"

    required = [onet_json_path, onet_agg_path, public_json_path, public_recovered_csv_path]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"Missing required inputs: {missing}")

    onet_payload = _load_json(onet_json_path)
    public_payload = _load_json(public_json_path)
    public_recovered_rows = _load_csv_rows(public_recovered_csv_path)
    onet_agg_rows = _load_csv_rows(onet_agg_path)

    tooling_rows: List[dict] = []
    analytics_rows: List[dict] = []
    baseline_rows: List[dict] = []

    tooling_terms: Set[str] = set()
    analytics_terms: Set[str] = set()
    baseline_terms: DefaultDict[str, Set[str]] = defaultdict(set)

    onet_tooling_support: DefaultDict[str, int] = defaultdict(int)
    onet_tooling_families: DefaultDict[str, Set[str]] = defaultdict(set)

    for row in onet_agg_rows:
        raw_term = row.get("technology", "")
        family = row.get("target_family", "")
        count = int(row.get("occupation_count", "0") or 0)

        term = _normalize_term(raw_term)
        if not _is_valid_candidate(term):
            continue

        onet_tooling_support[term] += count
        if family:
            onet_tooling_families[term].add(family)

    public_candidate_buckets = public_payload.get("candidate_const_buckets", {})
    public_tooling_candidates = {
        _normalize_term(term)
        for term in public_candidate_buckets.get("candidate_tooling_signals", [])
        if _normalize_term(term)
    }
    public_analytics_candidates = {
        _normalize_term(term)
        for term in public_candidate_buckets.get("candidate_analytics_ml_signals", [])
        if _normalize_term(term)
    }
    public_baseline_candidates = {
        family: {
            _normalize_term(term)
            for term in terms
            if _normalize_term(term)
        }
        for family, terms in public_candidate_buckets.get("candidate_baseline_familiarity_families", {}).items()
    }

    recovered_counts: Counter[str] = Counter()
    recovered_sources: DefaultDict[str, List[str]] = defaultdict(list)
    for row in public_recovered_rows:
        term = _normalize_term(row.get("recovered_skill", ""))
        if not term:
            continue
        try:
            count = int(row.get("count", "0") or 0)
        except Exception:
            count = 0
        recovered_counts[term] += count
        source_examples = str(row.get("source_examples", "")).strip()
        if source_examples and source_examples not in recovered_sources[term]:
            recovered_sources[term].append(source_examples)

    # Tooling merge
    candidate_tooling_pool = set(onet_tooling_support.keys()) | public_tooling_candidates | {
        term for term in recovered_counts.keys() if _tooling_score_markers(term)
    }

    for term in _sorted_terms(candidate_tooling_pool):
        if not _tooling_score_markers(term) and term not in public_tooling_candidates and term not in onet_tooling_support:
            continue

        onet_support = onet_tooling_support.get(term, 0)
        public_tooling = term in public_tooling_candidates
        public_recovered = recovered_counts.get(term, 0)

        if not _should_keep_tooling_candidate(
            term,
            onet_support=onet_support,
            public_tooling_candidate=public_tooling,
            public_recovered_count=public_recovered,
        ):
            continue

        tooling_terms.add(term)
        tooling_rows.append(
            {
                "term": term,
                "onet_total_occupation_support": onet_support,
                "onet_families": ",".join(sorted(onet_tooling_families.get(term, set()))),
                "public_tooling_candidate": str(public_tooling),
                "public_recovered_count": public_recovered,
                "public_recovered_examples": " | ".join(recovered_sources.get(term, [])[:3]),
                "sources": ",".join(
                    sorted(
                        {
                            source
                            for source, present in [
                                ("onet", term in onet_tooling_support),
                                ("public_tooling", public_tooling),
                                ("public_recovered", term in recovered_counts),
                            ]
                            if present
                        }
                    )
                ),
            }
        )

    # Analytics / ML merge
    candidate_analytics_pool = public_analytics_candidates | {
        term for term in recovered_counts.keys() if _analytics_ml_score_markers(term)
    }

    for term in _sorted_terms(candidate_analytics_pool):
        if not _analytics_ml_score_markers(term) and term not in public_analytics_candidates:
            continue

        public_analytics = term in public_analytics_candidates
        public_recovered = recovered_counts.get(term, 0)

        if not _should_keep_analytics_candidate(
            term,
            public_analytics_candidate=public_analytics,
            public_recovered_count=public_recovered,
        ):
            continue

        analytics_terms.add(term)
        analytics_rows.append(
            {
                "term": term,
                "public_analytics_candidate": str(public_analytics),
                "public_recovered_count": public_recovered,
                "public_recovered_examples": " | ".join(recovered_sources.get(term, [])[:3]),
                "sources": ",".join(
                    sorted(
                        {
                            source
                            for source, present in [
                                ("public_analytics", public_analytics),
                                ("public_recovered", term in recovered_counts),
                            ]
                            if present
                        }
                    )
                ),
            }
        )

    # Baseline familiarity merge
    for family, terms in public_baseline_candidates.items():
        for term in _sorted_terms(terms):
            if not _should_keep_analytics_candidate(
                term,
                public_analytics_candidate=(term in public_analytics_candidates),
                public_recovered_count=recovered_counts.get(term, 0),
            ):
                continue
            baseline_terms[family].add(term)
            baseline_rows.append(
                {
                    "family": family,
                    "term": term,
                    "public_baseline_candidate": "True",
                    "public_recovered_count": recovered_counts.get(term, 0),
                    "public_recovered_examples": " | ".join(recovered_sources.get(term, [])[:3]),
                }
            )

    payload = {
        "source": {
            "onet_dir": str(onet_dir),
            "public_dir": str(public_dir),
        },
        "summary": {
            "tooling_candidate_count": len(tooling_terms),
            "analytics_ml_candidate_count": len(analytics_terms),
            "baseline_family_sizes": {
                family: len(terms)
                for family, terms in sorted(baseline_terms.items())
            },
        },
        "candidate_registry": {
            "tooling": _sorted_terms(tooling_terms),
            "analytics_ml": _sorted_terms(analytics_terms),
            "baseline_familiarity": {
                family: _sorted_terms(terms)
                for family, terms in sorted(baseline_terms.items())
            },
        },
    }

    json_path = output_dir / OUTPUT_JSON_NAME
    tooling_csv_path = output_dir / OUTPUT_TOOLING_CSV_NAME
    analytics_csv_path = output_dir / OUTPUT_ANALYTICS_CSV_NAME
    baseline_csv_path = output_dir / OUTPUT_BASELINE_CSV_NAME

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    with tooling_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "term",
                "onet_total_occupation_support",
                "onet_families",
                "public_tooling_candidate",
                "public_recovered_count",
                "public_recovered_examples",
                "sources",
            ],
        )
        writer.writeheader()
        writer.writerows(tooling_rows)

    with analytics_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "term",
                "public_analytics_candidate",
                "public_recovered_count",
                "public_recovered_examples",
                "sources",
            ],
        )
        writer.writeheader()
        writer.writerows(analytics_rows)

    with baseline_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "family",
                "term",
                "public_baseline_candidate",
                "public_recovered_count",
                "public_recovered_examples",
            ],
        )
        writer.writeheader()
        writer.writerows(baseline_rows)

    print()
    print("=" * 100)
    print("MERGED SKILL SEED GENERATION COMPLETE")
    print("=" * 100)
    print(f"Tooling candidates            : {len(tooling_terms)}")
    print(f"Analytics/ML candidates       : {len(analytics_terms)}")
    print(f"Baseline family sizes         : {payload['summary']['baseline_family_sizes']}")
    print()
    print(f"JSON written                  : {json_path}")
    print(f"Tooling review CSV            : {tooling_csv_path}")
    print(f"Analytics/ML review CSV       : {analytics_csv_path}")
    print(f"Baseline familiarity CSV      : {baseline_csv_path}")
    print()

    print("Top tooling candidates:")
    for row in tooling_rows[:20]:
        print(row)

    print("\nTop analytics/ml candidates:")
    for row in analytics_rows[:20]:
        print(row)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        raise