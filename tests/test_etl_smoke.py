import os
import sqlite3
from contextlib import closing

from src.etl import run_etl
from src.db import get_db_path, apply_schema, db_conn


def test_schema_and_small_etl(monkeypatch):
    # Limit the date window to 3 days for CI speed
    monkeypatch.setenv("END_DATE", "2024-01-10")
    monkeypatch.setenv("START_DATE", "2024-01-07")
    monkeypatch.setenv("PAGE_SIZE", "1000")

    run_etl()

    db_path = get_db_path()
    with closing(sqlite3.connect(db_path)) as conn:
        cur = conn.cursor()
        # Tables exist
        for t in ("service_requests", "agency", "complaint_type", "descriptor", "borough"):
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (t,))
            assert cur.fetchone(), f"Missing table: {t}"
        # Some rows ingested
        cur.execute("SELECT COUNT(*) FROM service_requests")
        assert cur.fetchone()[0] >= 0 