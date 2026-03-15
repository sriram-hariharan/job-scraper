import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path("data/market_intel.db")


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_skill_corpus_table():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS extracted_skills (
        run_id TEXT,
        company TEXT,
        title TEXT,
        skill TEXT,
        skill_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def init_llm_skill_cache_table():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS llm_skill_cache (
        cache_key TEXT PRIMARY KEY,
        model TEXT NOT NULL,
        required_skills_json TEXT NOT NULL,
        preferred_skills_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_llm_skill_cache_model
    ON llm_skill_cache(model)
    """)

    conn.commit()
    conn.close()


def get_cached_llm_skills(cache_key: str) -> Optional[Dict[str, List[str]]]:
    init_llm_skill_cache_table()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT required_skills_json, preferred_skills_json
    FROM llm_skill_cache
    WHERE cache_key = ?
    """, (cache_key,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    required_json, preferred_json = row

    return {
        "required_skills": json.loads(required_json),
        "preferred_skills": json.loads(preferred_json),
    }


def store_cached_llm_skills(
    cache_key: str,
    model: str,
    required_skills: List[str],
    preferred_skills: List[str],
):
    init_llm_skill_cache_table()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO llm_skill_cache (
        cache_key,
        model,
        required_skills_json,
        preferred_skills_json
    )
    VALUES (?, ?, ?, ?)
    """, (
        cache_key,
        model,
        json.dumps(required_skills, ensure_ascii=False),
        json.dumps(preferred_skills, ensure_ascii=False),
    ))

    conn.commit()
    conn.close()


def store_job_skills(run_id: str, jobs: List[Dict[str, Any]]):
    init_skill_corpus_table()

    conn = get_conn()
    cur = conn.cursor()

    rows = []

    for job in jobs:
        company = job.get("company", "")
        title = job.get("title", "")

        intel = job.get("intelligence", {}) or {}
        skills = intel.get("skills", {}) or {}

        for skill in skills.get("required", []) or []:
            rows.append((run_id, company, title, skill, "required"))

        for skill in skills.get("preferred", []) or []:
            rows.append((run_id, company, title, skill, "preferred"))

    cur.executemany("""
    INSERT INTO extracted_skills (run_id, company, title, skill, skill_type)
    VALUES (?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()


def get_top_corpus_skills(limit: int = 100):
    init_skill_corpus_table()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT skill, COUNT(*) as freq
    FROM extracted_skills
    GROUP BY skill
    ORDER BY freq DESC, skill ASC
    LIMIT ?
    """, (limit,))

    rows = cur.fetchall()
    conn.close()

    return rows