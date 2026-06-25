"""Quiz session loop."""
import random
from typing import Optional

from . import db, hints

from . import sr
from .checker import check
from .config import (
    RESET, BOLD, DIM, RED, GREEN, YELLOW, CYAN,
    DIRECTION_FORWARD,
    MODE_WORD, MODE_SENTENCE, MODE_EXPRESSION,
)


COMMANDS_HELP = f"{DIM}commands: :hint  :skip  :show  :quit{RESET}"


def _shown_and_expected(item: dict, direction: str) -> tuple[str, str]:
    """Return (text shown to user, text they must type)."""
    if direction == DIRECTION_FORWARD:
        # English prompt → target answer
        return item["prompt"], item["answer"]
    else:
        # target answer → English prompt
        return item["answer"], item["prompt"]


def _mode_for_item(item: dict) -> str:
    cat = item["category"]
    if cat == "sentence":
        return MODE_SENTENCE
    if cat == "expression":
        return MODE_EXPRESSION
    return MODE_WORD


def run_quiz(
    language: str,
    categories: Optional[list[str]],
    direction: str,
    limit: Optional[int] = None,
) -> None:
    items = db.get_items(language, categories=categories)
    if not items:
        print(f"{YELLOW}No items found for that selection.{RESET}")
        return

    random.shuffle(items)
    if limit:
        items = items[:limit]

    total = len(items)
    correct_count = 0
    skipped = 0
    arrow = "→" if direction == DIRECTION_FORWARD else "←"
    cat_label = ", ".join(categories) if categories else "all"

    print()
    print(
        f"{BOLD}Starting quiz:{RESET} {total} items  "
        f"{DIM}({language}, {cat_label}, {arrow}){RESET}"
    )
    print(COMMANDS_HELP)
    print()

    for i, item in enumerate(items, 1):
        shown, expected = _shown_and_expected(item, direction)
        mode = _mode_for_item(item)
        hints_used = 0

        print(f"{DIM}[{i}/{total}]{RESET} {BOLD}{shown}{RESET}")
        if item.get("extra"):
            print(f"  {DIM}({item['extra']}){RESET}")

        # Inner loop — handles :hint/:show/:skip without consuming the question
        while True:
            try:
                user = input("  > ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                print(f"{YELLOW}Quiz interrupted.{RESET}")
                _summary(correct_count, skipped, i - 1)
                return

            if user == ":quit":
                _summary(correct_count, skipped, i - 1)
                return

            if user == ":skip":
                print(f"  {YELLOW}Skipped.{RESET}  answer: {BOLD}{expected}{RESET}")
                skipped += 1
                db.record_attempt(item["id"], direction, False, "", hints_used)
                sr.update_after_attempt(item["id"], direction, False)
                print()
                break

            if user == ":show":
                print(f"  {DIM}answer: {expected}{RESET}")
                continue

            if user == ":hint":
                if hints_used >= hints.max_hints(expected):
                    print(f"  {DIM}(no more hints){RESET}")
                    continue
                hints_used += 1
                print(f"  {CYAN}{hints.reveal(expected, hints_used)}{RESET}")
                continue

            if not user:
                continue

            result = check(user, expected, mode)
            if result["correct"]:
                if result["exact"]:
                    print(f"  {GREEN}✓ correct{RESET}")
                else:
                    print(
                        f"  {GREEN}✓ correct{RESET} "
                        f"{DIM}(typo — exact: {result['matched']}){RESET}"
                    )
                correct_count += 1
                db.record_attempt(item["id"], direction, True, user, hints_used)
                sr.update_after_attempt(item["id"], direction, True)
            else:
                print(f"  {RED}✗ wrong{RESET}  answer: {BOLD}{expected}{RESET}")
                db.record_attempt(item["id"], direction, False, user, hints_used)
                sr.update_after_attempt(item["id"], direction, False)
            print()
            break

    _summary(correct_count, skipped, total)


def _summary(correct: int, skipped: int, attempted: int) -> None:
    if attempted == 0:
        return
    wrong = attempted - correct - skipped
    pct = 100 * correct / attempted
    print()
    print(
        f"{BOLD}session summary:{RESET}  "
        f"{GREEN}{correct} correct{RESET}  "
        f"{RED}{wrong} wrong{RESET}  "
        f"{YELLOW}{skipped} skipped{RESET}  "
        f"{DIM}({pct:.0f}%){RESET}"
    )
