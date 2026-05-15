import sqlite3
from typing import List, Dict
from datetime import datetime

DB_PATH = "prismintel.db"


def init_db() -> None:
    """Create the research_jobs table if it doesn't exist."""
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS research_jobs (
            job_id         TEXT PRIMARY KEY,
            company_name   TEXT NOT NULL,
            status         TEXT NOT NULL,
            created_at     TEXT NOT NULL,
            report_markdown TEXT DEFAULT ''
        )
    """)
    con.commit()
    con.close()


def save_job(job_id: str, company_name: str,
             status: str, report_markdown: str = "") -> None:
    """Insert or update a research job record."""
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT OR REPLACE INTO research_jobs VALUES (?,?,?,?,?)",
        (job_id, company_name, status,
         datetime.now().isoformat(), report_markdown)
    )
    con.commit()
    con.close()


def get_history() -> List[Dict]:
    """Return last 10 jobs ordered by newest first."""
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        """SELECT job_id, company_name, status, created_at
           FROM research_jobs
           ORDER BY created_at DESC LIMIT 10"""
    ).fetchall()
    con.close()
    return [{"job_id": r[0], "company_name": r[1],
             "status": r[2], "created_at": r[3]}
            for r in rows]


if __name__ == "__main__":
    import os
    import sys
    from pathlib import Path

    # Use a temp DB for testing
    DB_PATH = "test_prismintel.db"

    # Clean up any previous test DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    # Test init_db
    init_db()
    assert os.path.exists(DB_PATH), "DB file should exist after init"
    print("[PASS] init_db() - table created")

    # Test save_job
    save_job("job_001", "Tesla", "running")
    save_job("job_002", "Apple", "complete", "# Apple Report\nContent here.")
    print("[PASS] save_job() - two jobs saved")

    # Test get_history
    history = get_history()
    assert len(history) == 2, f"Expected 2 jobs, got {len(history)}"
    assert history[0]["company_name"] == "Apple"  # newest first
    assert history[1]["company_name"] == "Tesla"
    print(f"[PASS] get_history() - returned {len(history)} jobs")

    # Test upsert (INSERT OR REPLACE)
    save_job("job_001", "Tesla", "complete", "# Tesla Report")
    history = get_history()
    tesla_job = [j for j in history if j["job_id"] == "job_001"][0]
    assert tesla_job["status"] == "complete"
    print("[PASS] save_job() upsert - status updated to 'complete'")

    # Cleanup test DB
    os.remove(DB_PATH)
    print("\n[PASS] All sqlite.py tests passed")
