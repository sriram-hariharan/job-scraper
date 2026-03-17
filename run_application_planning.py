import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set
from src.matching.job_adapter import build_job_evidence


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").lower().split()).strip()


def _slugify(value: str, max_len: int = 80) -> str:
    text = _normalize_text(value)
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    if not text:
        text = "item"
    return text[:max_len]


def _run_cmd(cmd: List[str]) -> None:
    print()
    print("RUNNING:", " ".join(cmd))
    print()
    subprocess.run(cmd, check=True)


def _load_job_doc_id_to_index(job_corpus_path: Path) -> Dict[str, int]:
    if not job_corpus_path.exists():
        raise RuntimeError(f"Missing job corpus: {job_corpus_path}")

    mapping: Dict[str, int] = {}
    with job_corpus_path.open() as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)
            job_evidence = build_job_evidence(record)
            job_doc_id = str(job_evidence.job_doc_id or "").strip()

            if job_doc_id:
                mapping[job_doc_id] = idx

    if not mapping:
        raise RuntimeError(
            f"No usable job_doc_id values could be derived from {job_corpus_path}"
        )

    return mapping


def _load_shortlist_rows(shortlist_csv_path: Path) -> List[dict]:
    if not shortlist_csv_path.exists():
        raise RuntimeError(f"Missing shortlist CSV: {shortlist_csv_path}")

    with shortlist_csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise RuntimeError(f"Shortlist CSV is empty: {shortlist_csv_path}")

    return rows


def _selected_rows(
    rows: List[dict],
    include_actions: Set[str],
    packet_limit: int,
) -> List[dict]:
    filtered = [row for row in rows if row.get("action", "") in include_actions]
    filtered.sort(
        key=lambda row: (
            row["action"],
            -float(row.get("winner_score", "0") or 0),
            _normalize_text(row.get("job_company", "")),
            _normalize_text(row.get("job_title", "")),
        )
    )

    if packet_limit > 0:
        filtered = filtered[:packet_limit]

    return filtered


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the application-planning workflow: batch best-variant selection, shortlist generation, and JD diff packets."
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
        help="How many jobs from the corpus to evaluate in batch selection. Use 0 for all.",
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
        default=15,
        help="How many jobs to print in the intermediate batch/shortlist scripts.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/application_planning",
        help="Directory to write planning outputs.",
    )
    parser.add_argument(
        "--include-actions",
        default="APPLY,APPLY_REVIEW_VARIANTS,MAYBE_TAILOR",
        help="Comma-separated shortlist actions for which JD diff packets should be generated.",
    )
    parser.add_argument(
        "--job-packet-limit",
        type=int,
        default=0,
        help="Optional cap on how many JD diff packets to generate. Use 0 for all selected shortlist rows.",
    )
    args = parser.parse_args()

    job_corpus_path = Path(args.job_corpus)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    job_packets_dir = output_dir / "job_packets"
    job_packets_dir.mkdir(parents=True, exist_ok=True)

    best_variant_csv = output_dir / "best_resume_variant_by_job.csv"
    shortlist_csv = output_dir / "application_shortlist_by_job.csv"

    batch_selector_cmd = [
        sys.executable,
        "batch_select_best_resume_variant.py",
        "--job-corpus",
        str(job_corpus_path),
        "--job-limit",
        str(args.job_limit),
        "--top-k-console",
        str(args.top_k_console),
        "--output-csv",
        str(best_variant_csv),
    ]
    if args.company_contains.strip():
        batch_selector_cmd.extend(["--company-contains", args.company_contains])
    if args.title_contains.strip():
        batch_selector_cmd.extend(["--title-contains", args.title_contains])
    if args.resume_name_contains.strip():
        batch_selector_cmd.extend(["--resume-name-contains", args.resume_name_contains])

    _run_cmd(batch_selector_cmd)

    shortlist_cmd = [
        sys.executable,
        "application_shortlist_from_batch_selector.py",
        "--input-csv",
        str(best_variant_csv),
        "--output-csv",
        str(shortlist_csv),
        "--top-k-console",
        str(args.top_k_console),
    ]
    if args.company_contains.strip():
        shortlist_cmd.extend(["--company-contains", args.company_contains])
    if args.title_contains.strip():
        shortlist_cmd.extend(["--title-contains", args.title_contains])

    _run_cmd(shortlist_cmd)

    job_doc_id_to_index = _load_job_doc_id_to_index(job_corpus_path)
    shortlist_rows = _load_shortlist_rows(shortlist_csv)

    include_actions = {
        action.strip()
        for action in args.include_actions.split(",")
        if action.strip()
    }
    selected = _selected_rows(
        shortlist_rows,
        include_actions=include_actions,
        packet_limit=args.job_packet_limit,
    )

    manifest_rows = []

    for row in selected:
        job_doc_id = row["job_doc_id"]
        if job_doc_id not in job_doc_id_to_index:
            raise RuntimeError(f"Could not map job_doc_id to index: {job_doc_id}")

        job_index = job_doc_id_to_index[job_doc_id]
        winner_resume = row["winner_resume"]
        company = row["job_company"]
        title = row["job_title"]

        file_slug = (
            f"{_slugify(company, 30)}__"
            f"{_slugify(title, 60)}__"
            f"{_slugify(winner_resume, 40)}"
        )
        packet_json_path = job_packets_dir / f"{file_slug}.json"

        diff_cmd = [
            sys.executable,
            "jd_resume_diff_helper.py",
            "--job-corpus",
            str(job_corpus_path),
            "--job-index",
            str(job_index),
            "--resume-name-contains",
            winner_resume,
            "--output-json",
            str(packet_json_path),
        ]

        _run_cmd(diff_cmd)

        manifest_rows.append(
            {
                "job_doc_id": job_doc_id,
                "job_company": company,
                "job_title": title,
                "action": row["action"],
                "winner_resume": winner_resume,
                "winner_score": row["winner_score"],
                "runner_up_resume": row["runner_up_resume"],
                "runner_up_score": row["runner_up_score"],
                "score_gap": row["score_gap"],
                "is_tie": row["is_tie"],
                "packet_json": str(packet_json_path),
            }
        )

    manifest_csv = output_dir / "job_packet_manifest.csv"
    fieldnames = [
        "job_doc_id",
        "job_company",
        "job_title",
        "action",
        "winner_resume",
        "winner_score",
        "runner_up_resume",
        "runner_up_score",
        "score_gap",
        "is_tie",
        "packet_json",
    ]
    with manifest_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for manifest_row in manifest_rows:
            writer.writerow(manifest_row)

    print()
    print("=" * 100)
    print("APPLICATION PLANNING WORKFLOW COMPLETE")
    print("=" * 100)
    print(f"Best-variant CSV : {best_variant_csv}")
    print(f"Shortlist CSV    : {shortlist_csv}")
    print(f"Packet manifest  : {manifest_csv}")
    print(f"Job packets dir  : {job_packets_dir}")
    print(f"Packets created  : {len(manifest_rows)}")
    print()


if __name__ == "__main__":
    main()