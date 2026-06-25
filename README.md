# verba

Terminal language drill. SQLite-backed, no dependencies beyond Python stdlib.

## Install

```
pip install -e .
```

This installs the `verba` command.

## Usage

```
verba                     # open the interactive menu
verba add                 # interactively add an item
verba add --lang german --category verb --prompt run --answer "laufen, rennen"
verba import vocab.txt    # bulk import
verba stats               # overall stats
verba stats --lang german # per-language stats
```

## Quiz commands

While answering inside a quiz session:

```
:hint    reveal one more letter of the answer
:show    show the full answer (no penalty in stats, you still get marked wrong if you skip)
:skip    skip this item (marked wrong)
:quit    end the session
```

## Import file format

One item per line, pipe-separated:

```
language | category | prompt (English) | answer (target lang) | optional extra
```

For word/expression categories, you can put comma-separated alternatives in
the answer column — typing any one of them counts as correct.

Lines starting with `#` and blank lines are ignored.

Example:

```
german | noun | dog       | Hund            | der
german | verb | run       | laufen, rennen
german | sentence | I am hungry | Ich habe Hunger
latin  | vocabulary | water | aqua
```

## Where data lives

`$XDG_DATA_HOME/verba/verba.db` (or `~/.local/share/verba/verba.db`).

Override with `VERBA_DB=/path/to/db verba …`.
