"""SQLite storage for saved translations (text only - never video or images)."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .config import DB_PATH


@dataclass
class HistoryEntry:
    id: int
    text: str
    word_count: int
    created_at: str  # "YYYY-MM-DD HH:MM:SS" local time


class HistoryDB:
    def __init__(self, path: Path | str = DB_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as con:
            con.execute(
                """CREATE TABLE IF NOT EXISTS translations (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       text TEXT NOT NULL,
                       word_count INTEGER NOT NULL,
                       created_at TEXT NOT NULL)"""
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=10)

    def add(self, text: str) -> int:
        text = (text or "").strip()
        if not text:
            raise ValueError("Cannot save an empty translation.")
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with closing(self._connect()) as con, con:
            cur = con.execute(
                "INSERT INTO translations (text, word_count, created_at) VALUES (?, ?, ?)",
                (text, len(text.split()), stamp),
            )
            return int(cur.lastrowid)

    def list(self, limit: int = 500, search: str = "") -> List[HistoryEntry]:
        sql = "SELECT id, text, word_count, created_at FROM translations"
        args: list = []
        if search.strip():
            sql += " WHERE text LIKE ?"
            args.append(f"%{search.strip()}%")
        sql += " ORDER BY id DESC LIMIT ?"
        args.append(int(limit))
        with closing(self._connect()) as con:
            return [HistoryEntry(*row) for row in con.execute(sql, args)]

    def get(self, entry_id: int) -> Optional[HistoryEntry]:
        with closing(self._connect()) as con:
            row = con.execute(
                "SELECT id, text, word_count, created_at FROM translations WHERE id = ?", (entry_id,)
            ).fetchone()
        return HistoryEntry(*row) if row else None

    def delete(self, entry_id: int) -> bool:
        with closing(self._connect()) as con, con:
            return con.execute("DELETE FROM translations WHERE id = ?", (entry_id,)).rowcount > 0

    def clear(self) -> int:
        with closing(self._connect()) as con, con:
            return con.execute("DELETE FROM translations").rowcount

    def count(self) -> int:
        with closing(self._connect()) as con:
            return int(con.execute("SELECT COUNT(*) FROM translations").fetchone()[0])
