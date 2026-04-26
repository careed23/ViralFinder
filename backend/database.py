import sqlite3
from contextlib import closing

DB_FILE = "viralfinder.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with closing(get_db_connection()) as conn:
        with conn as c:
            c.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id TEXT PRIMARY KEY,
                    started_at TEXT,
                    status TEXT,
                    source TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS domain_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id TEXT,
                    domain TEXT,
                    score REAL,
                    tier TEXT,
                    available INTEGER,
                    has_product_signals INTEGER,
                    ai_category TEXT,
                    snapshot_count INTEGER,
                    wayback_url TEXT,
                    created_at TEXT,
                    FOREIGN KEY (scan_id) REFERENCES scans (id)
                )
            """)
        conn.commit()

def persist_scan_results(job_id, results):
    with closing(get_db_connection()) as conn:
        with conn as c:
            c.execute("UPDATE scans SET status = 'completed' WHERE id = ?", (job_id,))
            for result in results:
                c.execute("""
                    INSERT INTO domain_results (
                        scan_id, domain, score, tier, available,
                        has_product_signals, ai_category, snapshot_count,
                        wayback_url, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_id,
                    result.domain,
                    result.opportunity_score,
                    result.tier,
                    int(result.is_available),
                    int(result.has_product_signals),
                    result.ai_category,
                    result.total_snapshots,
                    f"https://web.archive.org/web/*/{result.domain}",
                    result.creation_date.isoformat() if result.creation_date else None
                ))
        conn.commit()

def get_scan_results_from_db(job_id):
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM domain_results WHERE scan_id = ?", (job_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
