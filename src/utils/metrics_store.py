import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/pipeline_metrics.db")


def init_metrics_db():
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
        run_id INTEGER,
        stage TEXT,
        ats TEXT,
        count INTEGER
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
        datetime.utcnow().isoformat(),
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

def get_last_ats_counts(stage):

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    SELECT ats, count
    FROM ats_metrics
    WHERE run_id = (
        SELECT id FROM pipeline_runs
        ORDER BY id DESC
        LIMIT 1
    )
    AND stage = ?
    """, (stage,))

    rows = cur.fetchall()
    conn.close()

    return {ats: count for ats, count in rows}