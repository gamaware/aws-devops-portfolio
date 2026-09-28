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
        elif match:
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


def replace_generated(markdown: str, block: str) -> str:
    """Swap the text between the BEGIN and END markers for `block`."""
    start = markdown.find(BEGIN)
    end = markdown.find(END)
    if start == -1 or end == -1 or end < start:
        raise ValueError("README.md needs the BEGIN GENERATED and END GENERATED markers, in that order")
    return f"{markdown[: start + len(BEGIN)]}\n{block}{markdown[end:]}"
