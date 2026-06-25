"""Show stats."""
from typing import Optional

from . import db
from .config import RESET, BOLD, CYAN, GREEN


def show_stats(language: Optional[str] = None) -> None:
    print()
    if language:
        s = db.language_stats(language)
        print(f"{BOLD}{language.title()} stats{RESET}")
    else:
        s = db.overall_stats()
        print(f"{BOLD}Overall stats{RESET}")
    print(f"  items     {CYAN}{s['items']}{RESET}")
    print(f"  attempts  {CYAN}{s['attempts']}{RESET}")
    print(f"  correct   {GREEN}{s['correct']}{RESET}")
    if s["attempts"]:
        print(f"  accuracy  {GREEN}{s['accuracy'] * 100:.1f}%{RESET}")
