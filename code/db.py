import sqlite3
from typing import Optional, List, Any, Tuple
from pathlib import Path
from datetime import date, datetime
import json

DB_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS categories (
        category_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        icon TEXT,
        color TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS budgets (
        budget_id TEXT PRIMARY KEY,
        category_id TEXT,
        limit_value REAL NOT NULL,
        period TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS records (
        record_id TEXT PRIMARY KEY,
        amount REAL NOT NULL,
        type TEXT NOT NULL,
        date TEXT NOT NULL,
        category_id TEXT,
        account_id TEXT,
        tags TEXT,
        note TEXT,
        attachments TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS notifications (
        notif_id TEXT PRIMARY KEY,
        type TEXT,
        message TEXT,
        timestamp TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS accounts (
        account_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT,
        balance REAL DEFAULT 0.0,
        currency TEXT DEFAULT 'CNY'
    )
    """,
]


class Database:
    def __init__(self, path: Optional[str] = None):
        self.path = Path(path or Path.cwd() / "accounting.db")
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        for s in DB_SCHEMA:
            cur.execute(s)
        self.conn.commit()
        # Ensure legacy databases get account_id column if missing
        cur.execute("PRAGMA table_info(records)")
        cols = [r[1] for r in cur.fetchall()]
        if 'account_id' not in cols:
            try:
                cur.execute('ALTER TABLE records ADD COLUMN account_id TEXT')
                self.conn.commit()
            except Exception:
                # ignore if cannot alter (very old sqlite), but proceed
                pass

    def backup(self, dest: str) -> None:
        # simple file copy of the sqlite file
        import shutil
        self.conn.commit()
        shutil.copy2(str(self.path), dest)

    def restore(self, src: str) -> None:
        import shutil
        self.conn.close()
        shutil.copy2(src, str(self.path))
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row

    def execute(self, sql: str, params: Tuple = ()) -> sqlite3.Cursor:
        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()
        return cur

    def query(self, sql: str, params: Tuple = ()) -> List[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    def close(self):
        self.conn.close()
