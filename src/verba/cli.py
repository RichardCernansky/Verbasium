"""Entry point.

  verba                          interactive menu
  verba add                      interactive add prompt
  verba add --lang … --category … --prompt … --answer … [--extra …]
                                 non-interactive add (scripting-friendly)
  verba import <file>            bulk import from pipe-separated file
  verba stats [--lang <lang>]    show stats
"""
import argparse
import sys
from pathlib import Path

from . import db

from . import manage
from .menu import main_menu
from .stats import show_stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="verba",
        description="Terminal language drill. Run without args to open the menu.",
    )
    subs = parser.add_subparsers(dest="cmd")

    p_add = subs.add_parser("add", help="Add a single item")
    p_add.add_argument("--lang", help="language (e.g. german)")
    p_add.add_argument("--category", help="category (noun, verb, sentence, ...)")
    p_add.add_argument("--prompt", help="English side")
    p_add.add_argument("--answer", help="target-language side (commas = alternatives)")
    p_add.add_argument("--extra", help="optional extra metadata")

    p_imp = subs.add_parser("import", help="Bulk import items from a pipe-separated file")
    p_imp.add_argument("file", help="path to file")

    p_stats = subs.add_parser("stats", help="Show stats")
    p_stats.add_argument("--lang", help="filter to a specific language")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    db.init_db()  # idempotent; ensures schema on first run

    # no args -> go menu
    if args.cmd is None:
        try:
            main_menu()
        except KeyboardInterrupt:
            print()
        return 0

    # args with add -> add item 
    if args.cmd == "add":
        has_all = all([args.lang, args.category, args.prompt, args.answer])
        if has_all:
            item_id = manage.add_item_noninteractive(
                args.lang, args.category, args.prompt, args.answer, args.extra
            )
            if item_id is None:
                print("duplicate; not added", file=sys.stderr)
                return 1
            print(f"added id={item_id}")
            return 0
        # missing some fields → fall back to interactive
        manage.add_item_interactive()
        return 0

    # args with import -> import batch of items
    if args.cmd == "import":
        path = Path(args.file).expanduser()
        if not path.exists():
            print(f"file not found: {path}", file=sys.stderr)
            return 1
        inserted, skipped = manage.import_from_file(path)
        print(f"imported {inserted}, skipped {skipped} duplicate(s)")
        return 0

    if args.cmd == "stats":
        show_stats(args.lang.lower() if args.lang else None)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
