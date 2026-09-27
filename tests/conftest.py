"""Shared fixtures: a minimal valid catalog and a fake sibling repository on disk."""

from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest

from portfolio_check import readme

INDEX_ROOT = Path(__file__).resolve().parents[1]
STANDARD_README = "\n\n".join(
    ["# Example", "## What this proves", *(f"## {s}" for s in readme.SECTIONS), "## License"]
).replace("## Related work", "## Related work\n\n[index](https://github.com/example-owner/example-index)")

RAW = {
    "owner": "example-owner",
    "profile_url": "https://www.upwork.com/freelancers/~0100000000000000000",
    "offer_url_prefix": "https://www.upwork.com/services/product/",
    "index": {
        "name": "example-index",
        "kind": "index",
        "description": "Demonstrates a portfolio through cards; verified offline.",
        "topics": ["aws", "devops", "portfolio"],
    },
    "services": [
        {
            "id": "audit",
            "offer": "Terraform audit and fix",
            "offer_id": "1000000000000000001",
            "problem": "Untrusted Terraform.",
            "repo": {
                "name": "example-lab",
                "local": "example-lab-folder",
                "kind": "lab",
                "description": "Demonstrates a rescue through a report; verified offline with tests.",
                "topics": ["aws", "devops", "portfolio", "lab", "terraform"],
            },
            "artifact": {"label": "Report", "path": "report/REPORT.md", "summary": "Ranked findings."},
            "verification": "Offline tests.",
        }
    ],
    "more": [],
}


@pytest.fixture
def raw() -> dict:
    return copy.deepcopy(RAW)


def make_repo(root: Path, readme_text: str = STANDARD_README, adrs: int = 2) -> Path:
    """A sibling repository that passes every structure check."""
    for name in ("LICENSE", "CHANGELOG.md", "report/REPORT.md"):
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text("x\n", encoding="utf-8")
    (root / "README.md").write_text(readme_text, encoding="utf-8")
    (root / "docs/adr").mkdir(parents=True)
    for number in range(1, adrs + 1):
        (root / f"docs/adr/{number:04d}-decision.md").write_text("# ADR\n", encoding="utf-8")
    (root / "docs/assets").mkdir(parents=True)
    shutil.copy(INDEX_ROOT / "assets/cicd.png", root / "docs/assets/cover.png")  # 640x480 is 4:3 too
    return root
