"""Interactive numbered menus.

Flow:  language → mode → submode (if word mode) → direction → quiz

Inside the menu:
  number   pick that option
  b        back one level
  q        quit the app

Quitting raises QuitSignal which propagates to main_menu and exits.
"""
from typing import Optional

from . import db

from . import manage
from .config import (
    RESET, BOLD, DIM, CYAN, YELLOW,
    DIRECTION_FORWARD, DIRECTION_BACKWARD,
    MODE_WORD, MODE_SENTENCE, MODE_EXPRESSION,
    mode_for_category,
)
from .quiz import run_quiz
from .stats import show_stats


class QuitSignal(Exception):
    """Raised when the user picks 'q' anywhere. Caught only at main_menu."""


# Sentinel for "go back one level"
class _Back:
    def __repr__(self):
        return "BACK"
BACK = _Back()


def _choose(title: str, options: list[tuple[str, object]], allow_back: bool = True):
    """Show a numbered menu. Returns the chosen value, or BACK. Raises QuitSignal."""

    # infinite loop for choosing
    while True:
        print()
        print(f"{BOLD}{title}{RESET}")
        # first print out the options
        for i, (label, _) in enumerate(options, 1):
            print(f"  {CYAN}{i}{RESET}. {label}")
        # print others
        if allow_back:
            print(f"  {DIM}b. back   q. quit{RESET}")
        else:
            print(f"  {DIM}q. quit{RESET}")

        # try to get the input from user
        try:
            raw = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            raise QuitSignal()
        
        # check whats in the input and return
        if raw in ("q", "quit", "exit"):
            raise QuitSignal()
        if allow_back and raw in ("b", "back"):
            return BACK
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(options):
                return options[idx - 1][1]
        print(f"{YELLOW}invalid choice{RESET}")


# ------ Main loop ----------
def main_menu() -> None:
    try:
        while True:
            _top()
    except QuitSignal: #quit signal raised from inside of _top 
        print(f"{DIM}bye{RESET}")


def _top() -> None:
    print()
    print(f"{BOLD}verba{RESET}  {DIM}— terminal language drill{RESET}")
    languages = db.list_languages()

    # if no languages in the DB
    if not languages:
        print(f"{YELLOW}you don't have any items yet{RESET}")
        choice = _choose(
            "what now?",
            [
                ("Add an item", "add"),
                ("Import from file", "import"),
            ],
            allow_back=False,
        )
        if choice == "add":
            manage.add_item_interactive()
        elif choice == "import":
            manage.import_interactive()
        return

    # some languages found 
    options: list[tuple[str, object]] = [(lang.title(), ("lang", lang)) for lang in languages]
    options.append(("Add an item", ("action", "add")))
    options.append(("Import from file", ("action", "import")))
    options.append(("Stats", ("action", "stats")))

    choice = _choose("Select language", options, allow_back=False)
    if choice is BACK:
        return  # no back at top

    kind, value = choice  # type: ignore[misc]
    if kind == "action":
        if value == "add":
            manage.add_item_interactive()
        elif value == "import":
            manage.import_interactive()
        elif value == "stats":
            show_stats()
        return

    # kind == "lang"
    _language_flow(value)


# ---------------------------------------------------------------- Per-language

def _language_flow(language: str) -> None:
    cats = db.list_categories(language)
    if not cats:
        print(f"{YELLOW}no items for {language}{RESET}")
        return

    word_cats = [c for c in cats if mode_for_category(c) == MODE_WORD]
    sentence_cats = [c for c in cats if mode_for_category(c) == MODE_SENTENCE]
    expression_cats = [c for c in cats if mode_for_category(c) == MODE_EXPRESSION]

    while True:  # mode loop
        mode_options: list[tuple[str, object]] = []
        if word_cats:
            mode_options.append(("Word mode", MODE_WORD))
        if sentence_cats:
            mode_options.append(("Sentence mode", MODE_SENTENCE))
        if expression_cats:
            mode_options.append(("Expression mode", MODE_EXPRESSION))

        if len(mode_options) == 1:
            # only one mode; skip the picker but allow back via the next level
            mode = mode_options[0][1]
            picked_mode_implicitly = True
        else:
            mode = _choose(f"{language.title()} — select mode", mode_options)
            if mode is BACK:
                return
            picked_mode_implicitly = False

        # ---- submode (only for word mode with >1 category) ----
        if mode == MODE_WORD:
            categories = _pick_word_submode(language, word_cats)
        elif mode == MODE_SENTENCE:
            categories = sentence_cats
        else:
            categories = expression_cats

        if categories is BACK:
            if picked_mode_implicitly:
                return  # skip back past the auto-picked mode
            continue  # back to mode picker

        # ---- direction ----
        direction = _pick_direction()
        if direction is BACK:
            continue  # back to mode picker (close enough)

        run_quiz(language, categories, direction)
        # After quiz, loop back to mode picker.


def _pick_word_submode(language: str, word_cats: list[str]):
    if len(word_cats) == 0:
        return BACK
    if len(word_cats) == 1:
        return word_cats  # auto-select; nothing to choose
    options: list[tuple[str, object]] = [("All", word_cats)]
    for c in sorted(word_cats):
        options.append((c.title() + "s", [c]))
    return _choose(f"{language.title()} — word category", options)


def _pick_direction():
    return _choose(
        "Direction",
        [
            ("English → target", DIRECTION_FORWARD),
            ("Target → English", DIRECTION_BACKWARD),
        ],
    )
