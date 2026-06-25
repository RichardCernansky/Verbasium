"""Simple Leitner-box spaced repetition.

Streak counts consecutive correct answers per (item, direction).
Wrong resets streak to 0. Intervals grow with streak.

Easy to swap for SM-2 later; everything you need to reconstruct it lives
in the `attempts` table.
"""
from datetime import datetime, timezone, timedelta

from . import db


# Days to wait at each streak level. Beyond the last index, hold at max.
INTERVALS_DAYS = [0, 1, 3, 7, 14, 30, 60]


def compute_next_due(streak: int) -> str:
    idx = min(streak, len(INTERVALS_DAYS) - 1)
    days = INTERVALS_DAYS[idx]
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def update_after_attempt(item_id: int, direction: str, correct: bool) -> None:
    cur = db.get_progress(item_id, direction)
    streak = cur["streak"] if cur else 0
    streak = streak + 1 if correct else 0
    db.upsert_progress(item_id, direction, streak, compute_next_due(streak))
