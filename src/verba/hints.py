"""Progressive letter-reveal hints.

reveal("laufen", 0) -> "______"
reveal("laufen", 1) -> "l_____"
reveal("laufen", 2) -> "la____"
reveal("guten Tag", 3) -> "gut__ ___"   (spaces and punctuation always shown)
"""


def reveal(answer: str, hints_used: int) -> str:
    out = []
    revealed = 0
    for ch in answer:
        if ch.isalpha():
            if revealed < hints_used:
                out.append(ch)
                revealed += 1
            else:
                out.append("_")
        else:
            out.append(ch)
    return "".join(out)


def max_hints(answer: str) -> int:
    return sum(1 for ch in answer if ch.isalpha())
