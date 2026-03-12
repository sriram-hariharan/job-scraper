import sqlite3
from pathlib import Path
from threading import Lock
from models.description import Description

DB_PATH = Path("data/description_cache.db")

_db_lock = Lock()

def _get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_cache():
    with _db_lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS descriptions (
            job_id TEXT PRIMARY KEY,
            html TEXT,
            text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        conn.close()


def get_description(job_id):

    with _db_lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT html, text FROM descriptions WHERE job_id=?",
            (job_id,)
        )

        row = cur.fetchone()
        conn.close()

    if not row:
        return None

    return Description(
        job_id=job_id,
        html=row[0],
        text=row[1]
    )


def save_description(description: Description):

    with _db_lock:
        conn = _get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT OR REPLACE INTO descriptions (job_id, html, text)
            VALUES (?, ?, ?)
            """,
            (
                description.job_id,
                description.html,
                description.text
            )
        )

        conn.commit()
        conn.close()