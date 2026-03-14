import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("data/pipeline_metrics.db")


def init_metrics_db():

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pipeline_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        runtime_seconds REAL,
        scraped INTEGER,
        filtered INTEGER,
        deduped INTEGER,
        ranked INTEGER,
        details INTEGER,
        new_jobs INTEGER,
        drop_pct REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ats_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        stage TEXT NOT NULL,
        ats TEXT NOT NULL,
        count INTEGER NOT NULL,
        FOREIGN KEY (run_id) REFERENCES pipeline_runs(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS company_hiring_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER NOT NULL,
        company TEXT NOT NULL,
        ats TEXT NOT NULL,
        job_count INTEGER NOT NULL,
        FOREIGN KEY (run_id) REFERENCES pipeline_runs(id)
    )
    """)

    conn.commit()
    conn.close()


def get_last_run():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    SELECT id, scraped, filtered, deduped, ranked, details, drop_pct
    FROM pipeline_runs
    ORDER BY id DESC
    LIMIT 1
    """)

    row = cur.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "run_id": row[0],
        "scraped": row[1],
        "filtered": row[2],
        "deduped": row[3],
        "ranked": row[4],
        "details": row[5],
        "drop_pct": row[6]
    }

def get_last_ats_counts(stage):

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    SELECT ats, count
    FROM ats_metrics
    WHERE run_id = (
        SELECT id FROM pipeline_runs ORDER BY id DESC LIMIT 1
    )
    AND stage = ?
    """, (stage,))

    rows = cur.fetchall()

    conn.close()

    return {ats: count for ats, count in rows}

def record_pipeline_run(runtime, scraped, filtered, deduped, ranked, details, new_jobs, drop_pct):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO pipeline_runs (
        timestamp,
        runtime_seconds,
        scraped,
        filtered,
        deduped,
        ranked,
        details,
        new_jobs,
        drop_pct
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(timezone.utc).isoformat(),
        runtime,
        scraped,
        filtered,
        deduped,
        ranked,
        details,
        new_jobs,
        drop_pct
    ))

    run_id = cur.lastrowid
    conn.commit()
    conn.close()

    return run_id


def record_ats_counts(run_id, stage, counts):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    rows = [(run_id, stage, ats, count) for ats, count in counts.items()]

    cur.executemany("""
    INSERT INTO ats_metrics (run_id, stage, ats, count)
    VALUES (?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()

def record_company_hiring(run_id, jobs):

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    company_counts = {}

    for job in jobs:

        company = job.get("company")
        ats = job.get("source")

        if not company or not ats:
            continue

        key = (company, ats)

        company_counts[key] = company_counts.get(key, 0) + 1

    rows = [
        (run_id, company, ats, count)
        for (company, ats), count in company_counts.items()
    ]

    cur.executemany("""
    INSERT INTO company_hiring_metrics (run_id, company, ats, job_count)
    VALUES (?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()


def get_hiring_momentum():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    SELECT
        c1.company,
        c1.ats,
        c1.job_count AS current_jobs,
        COALESCE(c2.job_count, 0) AS previous_jobs
    FROM company_hiring_metrics c1
    LEFT JOIN company_hiring_metrics c2
        ON c1.company = c2.company
        AND c1.ats = c2.ats
        AND c2.run_id = (
            SELECT id FROM pipeline_runs
            ORDER BY id DESC
            LIMIT 1 OFFSET 1
        )
    WHERE c1.run_id = (
        SELECT id FROM pipeline_runs
        ORDER BY id DESC
        LIMIT 1
    )
    """)

    rows = cur.fetchall()
    conn.close()

    momentum = []

    for company, ats, current_jobs, previous_jobs in rows:

        delta = current_jobs - previous_jobs

        if delta != 0:
            momentum.append((company, ats, previous_jobs, current_jobs, delta))

    momentum.sort(key=lambda x: x[4], reverse=True)

    return momentum