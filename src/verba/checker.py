"""Answer verification with mode-aware strictness.

Word/expression mode:
  - lowercase compare
  - comma-separated alternatives in stored answer mean "any of these is valid"
  - Levenshtein typo tolerance (lenient on length)

Sentence mode:
  - lowercase compare
  - normalize multiple spaces
  - terminal punctuation ignored
  - no comma-as-alternative splitting (commas appear naturally in sentences)
  - Levenshtein typo tolerance
"""
import re
from .config import MODE_WORD, MODE_SENTENCE, MODE_EXPRESSION


def levenshtein(a: str, b: str) -> int:
    """Classic O(len(a)*len(b)) edit-distance, pure Python — no dependency."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def typo_threshold(s: str) -> int:
    """How many edits we forgive as a typo, scaled to length."""
    n = len(s)
    if n <= 3:
        return 0
    if n <= 6:
        return 1
    if n <= 12:
        return 2
    return 3


def _normalize_sentence(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[.!?,;:]+$", "", s)
    return s


def _normalize_word(s: str) -> str:
    return s.strip().lower()


def _alternatives(answer: str) -> list[str]:
    """Word/expression mode: split on commas."""
    return [a.strip() for a in answer.split(",") if a.strip()]


def check(user_input: str, expected_answer: str, mode: str) -> dict:
    """Verify a user's input against the expected answer.

    Returns dict with:
      correct  – bool, accepted as right
      exact    – bool, perfect match (no typo forgiveness used)
      typo     – bool, accepted via typo tolerance
      matched  – str, which canonical alternative matched (or closest miss)
    """
    user_input = (user_input or "").strip()
    if not user_input:
        return {"correct": False, "exact": False, "typo": False, "matched": ""}

    if mode == MODE_SENTENCE:
        candidates = [expected_answer]
        normalize = _normalize_sentence
    else:
        # word / expression
        candidates = _alternatives(expected_answer) or [expected_answer]
        normalize = _normalize_word

    u = normalize(user_input)
    best: tuple[int, str] | None = None

    for cand in candidates:
        c = normalize(cand)
        if u == c:
            return {"correct": True, "exact": True, "typo": False, "matched": cand}
        d = levenshtein(u, c)
        if best is None or d < best[0]:
            best = (d, cand)

    if best is None:
        return {"correct": False, "exact": False, "typo": False, "matched": ""}

    distance, matched = best
    if distance <= typo_threshold(matched):
        return {"correct": True, "exact": False, "typo": True, "matched": matched}
    return {"correct": False, "exact": False, "typo": False, "matched": matched}
