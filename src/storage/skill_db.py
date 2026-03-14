import sqlite3
from pathlib import Path

DB_PATH = Path("data/market_intel.db")


def get_conn():

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    return sqlite3.connect(DB_PATH)


def init_skill_db():

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS discovered_skills (
        skill TEXT PRIMARY KEY,
        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        occurrences INTEGER DEFAULT 1
    )
    """)

    conn.commit()
    conn.close()


def get_existing_skills():

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT skill FROM discovered_skills")

    skills = {row[0] for row in cur.fetchall()}

    conn.close()

    return skills


def insert_or_update_skill(skill):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO discovered_skills(skill, occurrences)
    VALUES (?,1)
    ON CONFLICT(skill)
    DO UPDATE SET occurrences = occurrences + 1
    """, (skill,))

    conn.commit()
    conn.close()