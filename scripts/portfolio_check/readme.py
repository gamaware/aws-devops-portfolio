"""README rules from STANDARD section 2, and the generated block this repository keeps in its own README."""

from __future__ import annotations

import re

# The fixed order of level-two headings. The first section depends on the repository type; License may close it.
OPENERS = ("What this proves", "Executive summary")
SECTIONS = (
    "Inspect the deliverable",
    "Scenario and acceptance criteria",
    "Architecture",
    "Verify locally",
    "Repository map",
    "Decisions and trade-offs",
    "Security and quality gates",
    "Limits and production adaptations",
    "Related work",
)
CLOSING = "License"

BEGIN = "<!-- BEGIN GENERATED: cards from data/catalog.yaml, run `make readme` -->"
END = "<!-- END GENERATED: cards -->"

_NUMBER_WORDS = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
    "twenty",
]

# A CommonMark code fence: up to three spaces, then three or more backticks or tildes.
_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def h2_headings(markdown: str) -> list[str]:
    """Level-two ATX headings outside fenced code blocks, in document order."""
    headings = []
    fence = ""  # the opening fence while inside a code block
    for line in markdown.splitlines():
        match = _FENCE_RE.match(line)
        if fence:
            # Only a run of the same character, at least as long and with nothing after it, closes the block.
            closes = (
                match is not None
                and match.group(1)[0] == fence[0]
                and len(match.group(1)) >= len(fence)
                and not line[match.end() :].strip()
            )
            if closes:
                fence = ""
        elif match and not (match.group(1)[0] == "`" and "`" in line[match.end() :]):
            # CommonMark: a backtick fence's info string may not contain a backtick, or the line is not a fence.
            fence = match.group(1)
        elif line.startswith("## "):
            headings.append(line[3:].strip())
    return headings


def section_order_errors(markdown: str) -> list[str]:
    """Return one message per deviation from the fixed section order; an empty list means it complies."""
    headings = h2_headings(markdown)
    expected_tail = [*SECTIONS]
    if headings and headings[-1] == CLOSING:
        headings = headings[:-1]
    if not headings:
        return ["no level-two headings"]
    if headings[0] not in OPENERS:
        return [f"first section is '{headings[0]}', expected one of: {', '.join(OPENERS)}"]
    if headings[1:] == expected_tail:
        return []
    errors = []
    missing = [s for s in expected_tail if s not in headings]
    extra = [h for h in headings[1:] if h not in expected_tail]
    if missing:
        errors.append(f"missing sections: {', '.join(missing)}")
    if extra:
        errors.append(f"sections outside the standard: {', '.join(extra)}")
    if not missing and not extra:
        errors.append(f"sections out of order: {' > '.join(headings[1:])}")
    return errors


def number_word(n: int) -> str:
    """Spell out 0-20 as the README prose does; larger numbers stay digits."""
    return _NUMBER_WORDS[n] if 0 <= n < len(_NUMBER_WORDS) else str(n)


def counts_phrase(services: int, repositories: int) -> str:
    """The README phrase that states how many services and public repositories the catalog lists."""
    return f"{number_word(services)} services backed by {number_word(repositories)} public repositories"


def mentions(markdown: str, phrase: str) -> bool:
    """True when `phrase` appears in `markdown`, ignoring line wrapping and repeated spaces."""
    return " ".join(phrase.split()) in " ".join(markdown.split())


def replace_generated(markdown: str, block: str) -> str:
    """Swap the text between the BEGIN and END markers for `block`."""
    start = markdown.find(BEGIN)
    end = markdown.find(END)
    if start == -1 or end == -1 or end < start:
        raise ValueError("README.md needs the BEGIN GENERATED and END GENERATED markers, in that order")
    return f"{markdown[: start + len(BEGIN)]}\n{block}{markdown[end:]}"
