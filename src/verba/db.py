"""SQLite layer. The DB is the single source of truth.

Three tables:
  items     — content (one row per prompt/answer pair)
  attempts  — append-only log of every answer
  progress  — current SR state per (item, direction)
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterable, Optional

from .config import get_db_path


SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    language    TEXT NOT NULL,
    category    TEXT NOT NULL,
    prompt      TEXT NOT NULL,    -- always English side
    answer      TEXT NOT NULL,    -- always target-language side
    extra       TEXT,             -- optional metadata (gender, notes, etc.)
    created_at  TEXT NOT NULL,
    UNIQUE(language, category, prompt, answer)
);

CREATE INDEX IF NOT EXISTS idx_items_lang_cat ON items(language, category);

CREATE TABLE IF NOT EXISTS attempts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id       INTEGER NOT NULL,
    direction     TEXT NOT NULL,
    correct       INTEGER NOT NULL,
    user_answer   TEXT,
    hints_used    INTEGER NOT NULL DEFAULT 0,
    attempted_at  TEXT NOT NULL,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_attempts_item ON attempts(item_id);

CREATE TABLE IF NOT EXISTS progress (
    item_id    INTEGER NOT NULL,
    direction  TEXT NOT NULL,
    streak     INTEGER NOT NULL DEFAULT 0,
    last_seen  TEXT,
    next_due   TEXT,
    PRIMARY KEY (item_id, direction),
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_progress_due ON progress(next_due);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect():
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


# ---------------------------------------------------------------- Reads

def list_languages() -> list[str]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT language FROM items ORDER BY language"
        ).fetchall()
        return [r["language"] for r in rows]


def list_categories(language: str) -> list[str]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM items WHERE language = ? ORDER BY category",
            (language,),
        ).fetchall()
        return [r["category"] for r in rows]


def get_items(language: str, categories: Optional[list[str]] = None) -> list[dict]:
    """Return items for a language, optionally filtered by category list."""
    with connect() as conn:
        if categories:
            placeholders = ",".join("?" * len(categories))
            rows = conn.execute(
                f"SELECT * FROM items WHERE language = ? "
                f"AND category IN ({placeholders})",
                (language, *categories),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM items WHERE language = ?", (language,)
            ).fetchall()
        return [dict(r) for r in rows]


def get_progress(item_id: int, direction: str) -> Optional[dict]:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM progress WHERE item_id = ? AND direction = ?",
            (item_id, direction),
        ).fetchone()
        return dict(row) if row else None


# ---------------------------------------------------------------- Writes

def add_item(
    language: str, category: str, prompt: str, answer: str, extra: Optional[str] = None
) -> Optional[int]:
    """Insert a new item. Returns its id, or None if duplicate."""
    with connect() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO items (language, category, prompt, answer, extra, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (language, category, prompt, answer, extra, now_iso()),
            )
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None


def bulk_add_items(rows: Iterable[tuple]) -> tuple[int, int]:
    """rows: iterable of (language, category, prompt, answer, extra).
    Returns (inserted, skipped_duplicates)."""
    inserted = 0
    skipped = 0
    ts = now_iso()
    with connect() as conn:
        for lang, cat, prompt, answer, extra in rows:
            try:
                conn.execute(
                    "INSERT INTO items (language, category, prompt, answer, extra, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (lang, cat, prompt, answer, extra, ts),
                )
                inserted += 1
            except sqlite3.IntegrityError:
                skipped += 1
    return inserted, skipped


def record_attempt(
    item_id: int, direction: str, correct: bool, user_answer: str, hints_used: int
) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO attempts "
            "(item_id, direction, correct, user_answer, hints_used, attempted_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (item_id, direction, 1 if correct else 0, user_answer, hints_used, now_iso()),
        )


def upsert_progress(item_id: int, direction: str, streak: int, next_due: str) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO progress (item_id, direction, streak, last_seen, next_due) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(item_id, direction) DO UPDATE SET "
            "  streak = excluded.streak, "
            "  last_seen = excluded.last_seen, "
            "  next_due = excluded.next_due",
            (item_id, direction, streak, now_iso(), next_due),
        )


# ---------------------------------------------------------------- Stats

def overall_stats() -> dict:
    with connect() as conn:
        n_items = conn.execute("SELECT COUNT(*) AS c FROM items").fetchone()["c"]
        n_attempts = conn.execute("SELECT COUNT(*) AS c FROM attempts").fetchone()["c"]
        n_correct = conn.execute(
            "SELECT COUNT(*) AS c FROM attempts WHERE correct = 1"
        ).fetchone()["c"]
        return {
            "items": n_items,
            "attempts": n_attempts,
            "correct": n_correct,
            "accuracy": (n_correct / n_attempts) if n_attempts else 0.0,
        }


def language_stats(language: str) -> dict:
    with connect() as conn:
        n_items = conn.execute(
            "SELECT COUNT(*) AS c FROM items WHERE language = ?", (language,)
        ).fetchone()["c"]
        n_attempts = conn.execute(
            "SELECT COUNT(*) AS c FROM attempts a "
            "JOIN items i ON i.id = a.item_id WHERE i.language = ?",
            (language,),
        ).fetchone()["c"]
        n_correct = conn.execute(
            "SELECT COUNT(*) AS c FROM attempts a "
            "JOIN items i ON i.id = a.item_id WHERE i.language = ? AND a.correct = 1",
            (language,),
        ).fetchone()["c"]
        return {
            "language": language,
            "items": n_items,
            "attempts": n_attempts,
            "correct": n_correct,
            "accuracy": (n_correct / n_attempts) if n_attempts else 0.0,
        }
