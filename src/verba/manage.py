"""Item management: add (single) and import (bulk)."""
from pathlib import Path
from typing import Iterator, Optional

from . import db
from .config import RESET, BOLD, DIM, GREEN, YELLOW, RED


# ---------------------------------------------------------------- Add (single)

def add_item_interactive() -> None:
    """Interactive single-item add. Empty input cancels."""
    print()
    print(f"{BOLD}Add an item{RESET}  {DIM}(empty input cancels){RESET}")

    def ask(label: str) -> Optional[str]:
        try:
            return input(f"  {label}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

    language = ask("language (e.g. german)")
    if not language:
        return
    category = ask("category (noun / verb / adjective / sentence / expression / ...)")
    if not category:
        return
    prompt = ask("prompt (English)")
    if not prompt:
        return
    answer = ask("answer (target language; comma-separate alternatives)")
    if not answer:
        return
    extra_raw = ask("extra (optional, e.g. gender)")
    extra = extra_raw if extra_raw else None

    item_id = db.add_item(language.lower(), category.lower(), prompt, answer, extra)
    if item_id is None:
        print(f"  {YELLOW}Duplicate — not added.{RESET}")
    else:
        print(f"  {GREEN}✓ added (id={item_id}){RESET}")


def add_item_noninteractive(
    language: str, category: str, prompt: str, answer: str, extra: Optional[str] = None
) -> Optional[int]:
    return db.add_item(language.lower(), category.lower(), prompt, answer, extra)


# ---------------------------------------------------------------- Import (bulk)

IMPORT_FORMAT_HELP = (
    "File format: one item per line, pipe-separated.\n"
    "  language | category | prompt (English) | answer (target) | [extra]\n"
    "Lines starting with # are ignored."
)


def parse_import_file(path: Path) -> Iterator[tuple]:
    """Yield (language, category, prompt, answer, extra) tuples. Skips bad lines
    with a warning to stdout."""
    with open(path, "r", encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4:
                print(f"  {YELLOW}line {n}: only {len(parts)} fields, skipping{RESET}")
                continue
            language = parts[0].lower()
            category = parts[1].lower()
            prompt = parts[2]
            answer = parts[3]
            extra = parts[4] if len(parts) > 4 and parts[4] else None
            yield (language, category, prompt, answer, extra)


def import_from_file(path: Path) -> tuple[int, int]:
    rows = list(parse_import_file(path))
    if not rows:
        return 0, 0
    return db.bulk_add_items(rows)


def import_interactive() -> None:
    print()
    print(f"{BOLD}Bulk import{RESET}")
    for ln in IMPORT_FORMAT_HELP.splitlines():
        print(f"  {DIM}{ln}{RESET}")
    try:
        raw = input("  file path: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return
    if not raw:
        return
    path = Path(raw).expanduser()
    if not path.exists():
        print(f"  {RED}not found: {path}{RESET}")
        return
    inserted, skipped = import_from_file(path)
    if inserted == 0 and skipped == 0:
        print(f"  {YELLOW}no valid rows found{RESET}")
    else:
        print(
            f"  {GREEN}imported {inserted}{RESET}, "
            f"{YELLOW}skipped {skipped} duplicate(s){RESET}"
        )
