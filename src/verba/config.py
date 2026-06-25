"""Constants, paths, and ANSI colors."""
import os
from pathlib import Path


# ---------------------------------------------------------------- DB location

def get_db_path() -> Path:
    """DB location. Override with VERBA_DB env var (handy for testing)."""
    custom = os.environ.get("VERBA_DB")
    if custom:
        return Path(custom).expanduser()
    data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(data_home) if data_home else Path.home() / ".local" / "share"
    return base / "verba" / "verba.db"


# ---------------------------------------------------------------- ANSI colors

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"


# ---------------------------------------------------------------- Modes

MODE_WORD = "word"
MODE_SENTENCE = "sentence"
MODE_EXPRESSION = "expression"

DIRECTION_FORWARD = "forward"    # English  -> target language
DIRECTION_BACKWARD = "backward"  # target language -> English


# Which categories belong to which mode. Anything not listed is word mode.
# This means: as soon as you add an item with category="adverb", it just shows
# up under Word mode automatically — no code change needed.
SENTENCE_CATEGORIES = {"sentence"}
EXPRESSION_CATEGORIES = {"expression"}


def mode_for_category(category: str) -> str:
    if category in SENTENCE_CATEGORIES:
        return MODE_SENTENCE
    if category in EXPRESSION_CATEGORIES:
        return MODE_EXPRESSION
    return MODE_WORD
