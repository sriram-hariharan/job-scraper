import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, List, Set


OUTPUT_JSON_NAME = "onet_skill_seed.json"
OUTPUT_TITLE_REVIEW_CSV_NAME = "onet_title_review.csv"
OUTPUT_OCCUPATION_SNAPSHOT_CSV_NAME = "onet_occupation_skill_snapshot.csv"
OUTPUT_TECH_AGGREGATE_CSV_NAME = "onet_target_family_tech_aggregate.csv"

TARGET_CANONICAL_TITLE_ALLOWLIST: Dict[str, List[str]] = {
    "analytics": [
        "Business Intelligence Analysts",
        "Financial Quantitative Analysts",
        "Fraud Examiners, Investigators and Analysts",
    ],
    "data_science": [
        "Data Scientists",
        "Statisticians",
        "Biostatisticians",
        "Operations Research Analysts",
    ],
    "machine_learning": [
        "Computer and Information Research Scientists",
        "Data Scientists",
    ],
    "engineering_data_platform": [
        "Database Administrators",
        "Database Architects",
        "Data Warehousing Specialists",
    ],
}

GENERIC_TECH_EXACT_EXCLUDE = {
    "desktop computer",
    "desktop computers",
    "document management software",
    "laptop computer",
    "laptop computers",
    "microsoft office software",
    "microsoft outlook",
    "microsoft powerpoint",
    "microsoft word",
    "notebook computer",
    "personal computer",
    "personal computers",
    "tablet computer",
    "tablet computers",
}

GENERIC_TECH_CONTAINS_EXCLUDE = [
    "printer",
    "telephone",
    "fax",
    "scanner",
    "photocopier",
    "cash register",
    "calculator",
]

TECHNICAL_KNOWLEDGE_ALLOWLIST = {
    "computers and electronics",
    "engineering and technology",
    "mathematics",
    "telecommunications",
}


def _normalize_text(value: str) -> str:
    text = str(value or "").lower().strip()
    if not text:
        return ""
    text = text.replace("&", " and ")
    text = text.replace("/", " / ")
    text = re.sub(r"[^a-z0-9+#/\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    normalization_map = {
        "machine-learning": "machine learning",
        "artificial-intelligence": "artificial intelligence",
        "business-intelligence": "business intelligence",
        "ml": "machine learning",
        "ai": "artificial intelligence",
        "bi": "business intelligence",
    }
    alias_map = {
        "mle": "machine learning engineer",
        "ml engineer": "machine learning engineer",
        "ai/ml": "artificial intelligence machine learning",
        "ds": "data science",
    }

    previous = None
    while text and text != previous:
        previous = text
        text = normalization_map.get(text, text)
        text = alias_map.get(text, text)

    return text


def _normalize_title(value: str) -> str:
    text = _normalize_text(value)
    if not text:
        return ""
    text = re.sub(r"\b(sr|senior)\b", "senior", text)
    text = re.sub(r"\b(jr|junior)\b", "junior", text)
    text = re.sub(r"\b(iii|ii|iv|v)\b", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_skill(value: str) -> str:
    text = _normalize_text(value)
    if not text:
        return ""

    skill_map = {
        "document management software": "document management software",
        "data base user interface and query software": "database query software",
        "natural language processing": "natural language processing",
        "machine learning": "machine learning",
        "deep learning": "deep learning",
    }
    return skill_map.get(text, text)

def _contains_whole_phrase(text: str, phrase: str) -> bool:
    normalized_text = _normalize_title(text)
    normalized_phrase = _normalize_title(phrase)
    if not normalized_text or not normalized_phrase:
        return False
    return re.search(rf"\b{re.escape(normalized_phrase)}\b", normalized_text) is not None

def _detect_title_families(title: str) -> List[str]:
    normalized = _normalize_title(title)
    if not normalized:
        return []

    matches: List[str] = []

    for family_name, canonical_titles in TARGET_CANONICAL_TITLE_ALLOWLIST.items():
        if any(normalized == _normalize_title(candidate) for candidate in canonical_titles):
            matches.append(family_name)

    return sorted(matches)


def _read_tsv(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


def _safe_float(value: str) -> float:
    try:
        return float(str(value).strip())
    except Exception:
        return 0.0


def _sample_join(values: List[str], limit: int = 8) -> str:
    unique: List[str] = []
    seen: Set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        unique.append(value)
        if len(unique) >= limit:
            break
    return " | ".join(unique)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Standalone O*NET skill seed extractor for offline taxonomy review."
    )
    parser.add_argument(
        "--onet-dir",
        required=True,
        help="Path to the extracted O*NET text folder containing Occupation Data.txt etc.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/skill_taxonomy/onet_seed",
        help="Directory for generated review artifacts.",
    )
    parser.add_argument(
        "--top-skills-per-occupation",
        type=int,
        default=12,
        help="How many importance-ranked O*NET skills to keep per occupation in the snapshot.",
    )
    parser.add_argument(
        "--top-tech-per-occupation",
        type=int,
        default=15,
        help="How many technology examples to keep per occupation in the snapshot.",
    )
    args = parser.parse_args()

    onet_dir = Path(args.onet_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    occupation_path = onet_dir / "Occupation Data.txt"
    skills_path = onet_dir / "Skills.txt"
    technology_path = onet_dir / "Technology Skills.txt"
    knowledge_path = onet_dir / "Knowledge.txt"
    alternate_titles_path = onet_dir / "Alternate Titles.txt"

    required_paths = [
        occupation_path,
        skills_path,
        technology_path,
        knowledge_path,
        alternate_titles_path,
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    if missing:
        raise RuntimeError(f"Missing required O*NET files: {missing}")

    occupations_rows = _read_tsv(occupation_path)
    skills_rows = _read_tsv(skills_path)
    technology_rows = _read_tsv(technology_path)
    knowledge_rows = _read_tsv(knowledge_path)
    alternate_title_rows = _read_tsv(alternate_titles_path)

    occupations: Dict[str, dict] = {}
    title_index: DefaultDict[str, Set[str]] = defaultdict(set)
    target_family_index: DefaultDict[str, Set[str]] = defaultdict(set)

    for row in occupations_rows:
        code = str(row.get("O*NET-SOC Code", "")).strip()
        title = str(row.get("Title", "")).strip()
        description = str(row.get("Description", "")).strip()
        normalized_title = _normalize_title(title)
        matched_families = _detect_title_families(title)

        occupations[code] = {
            "onet_soc_code": code,
            "title": title,
            "normalized_title": normalized_title,
            "description": description,
            "matched_target_families": matched_families,
            "alternate_titles": [],
            "normalized_alternate_titles": [],
            "skills_importance": [],
            "knowledge_areas": [],
            "technology_examples": [],
        }

        if normalized_title:
            title_index[normalized_title].add(code)

        for family_name in matched_families:
            target_family_index[family_name].add(code)

    for row in alternate_title_rows:
        code = str(row.get("O*NET-SOC Code", "")).strip()
        alt_title = str(row.get("Alternate Title", "")).strip()
        if not code or code not in occupations or not alt_title:
            continue

        normalized_alt = _normalize_title(alt_title)
        occupations[code]["alternate_titles"].append(alt_title)
        if normalized_alt:
            occupations[code]["normalized_alternate_titles"].append(normalized_alt)
            title_index[normalized_alt].add(code)

    skills_by_code: DefaultDict[str, List[dict]] = defaultdict(list)
    for row in skills_rows:
        code = str(row.get("O*NET-SOC Code", "")).strip()
        scale_id = str(row.get("Scale ID", "")).strip()
        element_name = str(row.get("Element Name", "")).strip()
        data_value = _safe_float(row.get("Data Value", ""))

        if not code or code not in occupations:
            continue

        # Use Importance rows only for now.
        if scale_id != "IM":
            continue

        normalized_skill = _normalize_skill(element_name)
        if not normalized_skill:
            continue

        skills_by_code[code].append(
            {
                "skill": element_name,
                "normalized_skill": normalized_skill,
                "importance": data_value,
            }
        )
    knowledge_by_code: DefaultDict[str, List[dict]] = defaultdict(list)
    for row in knowledge_rows:
        code = str(row.get("O*NET-SOC Code", "")).strip()
        scale_id = str(row.get("Scale ID", "")).strip()
        element_name = str(row.get("Element Name", "")).strip()
        data_value = _safe_float(row.get("Data Value", ""))

        if not code or code not in occupations:
            continue

        if scale_id != "IM":
            continue

        normalized_knowledge = _normalize_skill(element_name)
        if not normalized_knowledge:
            continue

        if normalized_knowledge not in TECHNICAL_KNOWLEDGE_ALLOWLIST:
            continue

        knowledge_by_code[code].append(
            {
                "knowledge": element_name,
                "normalized_knowledge": normalized_knowledge,
                "importance": data_value,
            }
        )

    for code, items in knowledge_by_code.items():
        best_by_knowledge: Dict[str, dict] = {}
        for item in items:
            key = item["normalized_knowledge"]
            existing = best_by_knowledge.get(key)
            if existing is None or item["importance"] > existing["importance"]:
                best_by_knowledge[key] = item

        ranked = sorted(
            best_by_knowledge.values(),
            key=lambda item: (-item["importance"], item["normalized_knowledge"]),
        )
        occupations[code]["knowledge_areas"] = ranked[:8]
    for code, items in skills_by_code.items():
        best_by_skill: Dict[str, dict] = {}
        for item in items:
            key = item["normalized_skill"]
            existing = best_by_skill.get(key)
            if existing is None or item["importance"] > existing["importance"]:
                best_by_skill[key] = item

        ranked = sorted(
            best_by_skill.values(),
            key=lambda item: (-item["importance"], item["normalized_skill"]),
        )
        occupations[code]["skills_importance"] = ranked[: args.top_skills_per_occupation]

    tech_by_code: DefaultDict[str, List[dict]] = defaultdict(list)
    for row in technology_rows:
        code = str(row.get("O*NET-SOC Code", "")).strip()
        example = str(row.get("Example", "")).strip()
        commodity_title = str(row.get("Commodity Title", "")).strip()
        hot = str(row.get("Hot Technology", "")).strip()
        in_demand = str(row.get("In Demand", "")).strip()

        if not code or code not in occupations or not example:
            continue

        normalized_example = _normalize_skill(example)
        if not normalized_example:
            continue

        if normalized_example in GENERIC_TECH_EXACT_EXCLUDE:
            continue

        if any(fragment in normalized_example for fragment in GENERIC_TECH_CONTAINS_EXCLUDE):
            continue

        tech_by_code[code].append(
            {
                "example": example,
                "normalized_example": normalized_example,
                "commodity_title": commodity_title,
                "hot_technology": hot,
                "in_demand": in_demand,
            }
        )

    for code, items in tech_by_code.items():
        best_by_example: Dict[str, dict] = {}
        for item in items:
            key = item["normalized_example"]
            existing = best_by_example.get(key)
            if existing is None:
                best_by_example[key] = item
                continue

            existing_score = (existing["hot_technology"] == "Y", existing["in_demand"] == "Y")
            new_score = (item["hot_technology"] == "Y", item["in_demand"] == "Y")
            if new_score > existing_score:
                best_by_example[key] = item

        ranked = sorted(
            best_by_example.values(),
            key=lambda item: (
                item["hot_technology"] != "Y",
                item["in_demand"] != "Y",
                item["normalized_example"],
            ),
        )
        occupations[code]["technology_examples"] = ranked[: args.top_tech_per_occupation]

    title_review_rows: List[dict] = []
    occupation_snapshot_rows: List[dict] = []

    family_tech_counts: DefaultDict[str, DefaultDict[str, int]] = defaultdict(lambda: defaultdict(int))

    for code in sorted(occupations.keys()):
        record = occupations[code]
        alt_titles = sorted(set(record["alternate_titles"]))
        normalized_alt_titles = sorted(set(record["normalized_alternate_titles"]))
        matched_families = sorted(set(record["matched_target_families"]))

        knowledge_names = [item["normalized_knowledge"] for item in record["knowledge_areas"]]
        tech_names = [item["normalized_example"] for item in record["technology_examples"]]

        for family_name in matched_families:
            for tech_name in sorted(set(tech_names)):
                family_tech_counts[family_name][tech_name] += 1

        title_review_rows.append(
            {
                "onet_soc_code": code,
                "canonical_title": record["title"],
                "normalized_canonical_title": record["normalized_title"],
                "matched_target_families": ",".join(matched_families),
                "alternate_title_count": len(alt_titles),
                "knowledge_count": len(record["knowledge_areas"]),
                "technology_example_count": len(record["technology_examples"]),
                "sample_alternate_titles": _sample_join(alt_titles, limit=8),
                "sample_top_knowledge": _sample_join(knowledge_names, limit=8),
                "sample_top_technology_examples": _sample_join(tech_names, limit=8),
            }
        )

        occupation_snapshot_rows.append(
            {
                "onet_soc_code": code,
                "canonical_title": record["title"],
                "description": record["description"],
                "matched_target_families": ",".join(matched_families),
                "top_knowledge": " | ".join(
                    f"{item['normalized_knowledge']} ({item['importance']:.2f})"
                    for item in record["knowledge_areas"]
                ),
                "top_technology_examples": " | ".join(
                    item["normalized_example"] for item in record["technology_examples"]
                ),
            }
        )

        record["alternate_titles"] = alt_titles
        record["normalized_alternate_titles"] = normalized_alt_titles
        record["matched_target_families"] = matched_families

    payload = {
        "source": {
            "onet_dir": str(onet_dir),
        },
        "summary": {
            "occupation_count": len(occupations),
            "title_index_count": len(title_index),
            "target_family_counts": {
                family_name: len(sorted(codes))
                for family_name, codes in sorted(target_family_index.items())
            },
        },
        "target_family_index": {
            family_name: sorted(codes)
            for family_name, codes in sorted(target_family_index.items())
        },
        "title_index": {
            normalized_title: sorted(codes)
            for normalized_title, codes in sorted(title_index.items())
        },
        "occupations": [occupations[code] for code in sorted(occupations.keys())],
    }

    json_path = output_dir / OUTPUT_JSON_NAME
    title_review_csv_path = output_dir / OUTPUT_TITLE_REVIEW_CSV_NAME
    occupation_snapshot_csv_path = output_dir / OUTPUT_OCCUPATION_SNAPSHOT_CSV_NAME
    tech_aggregate_csv_path = output_dir / OUTPUT_TECH_AGGREGATE_CSV_NAME

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    with title_review_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "onet_soc_code",
                "canonical_title",
                "normalized_canonical_title",
                "matched_target_families",
                "alternate_title_count",
                "knowledge_count",
                "technology_example_count",
                "sample_alternate_titles",
                "sample_top_knowledge",
                "sample_top_technology_examples",
            ],
        )
        writer.writeheader()
        writer.writerows(title_review_rows)

    with occupation_snapshot_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "onet_soc_code",
                "canonical_title",
                "description",
                "matched_target_families",
                "top_knowledge",
                "top_technology_examples",
            ],
        )
        writer.writeheader()
        writer.writerows(occupation_snapshot_rows)

    aggregate_rows: List[dict] = []
    for family_name in sorted(family_tech_counts.keys()):
        for tech_name, count in sorted(
            family_tech_counts[family_name].items(),
            key=lambda item: (-item[1], item[0]),
        ):
            aggregate_rows.append(
                {
                    "target_family": family_name,
                    "technology": tech_name,
                    "occupation_count": count,
                }
            )

    with tech_aggregate_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "target_family",
                "technology",
                "occupation_count",
            ],
        )
        writer.writeheader()
        writer.writerows(aggregate_rows)

    print()
    print("=" * 100)
    print("O*NET SKILL SEED GENERATION COMPLETE")
    print("=" * 100)
    print(f"Occupations loaded          : {len(occupations)}")
    print(f"Normalized title index size : {len(title_index)}")
    print("Target family counts        :")
    for family_name, count in payload["summary"]["target_family_counts"].items():
        print(f"  - {family_name}: {count}")
    print()
    print(f"JSON written                : {json_path}")
    print(f"Title review CSV written    : {title_review_csv_path}")
    print(f"Occupation snapshot CSV     : {occupation_snapshot_csv_path}")
    print(f"Tech aggregate CSV          : {tech_aggregate_csv_path}")
    print()

    preview = [
        row for row in title_review_rows
        if row["matched_target_families"]
    ][:20]

    if preview:
        print("Preview of matched target occupations:")
        for row in preview:
            print(
                f"  {row['onet_soc_code']} | {row['canonical_title']} | "
                f"families={row['matched_target_families']} | "
                f"knowledge={row['sample_top_knowledge']} | "
                f"tech={row['sample_top_technology_examples']}"
            )
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        raise