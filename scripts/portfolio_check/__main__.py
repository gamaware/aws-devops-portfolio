"""Command line: check, readme, covers, siblings, owner and live (python -m portfolio_check <command>)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import checks, readme, render
from .checks import Result
from .covers import refresh
from .live import run as live_run
from .model import CatalogError, load

INDEX_ROOT = Path(__file__).resolve().parents[2]
CATALOG = INDEX_ROOT / "data" / "catalog.yaml"


def _report(results: list[Result]) -> int:
    for result in results:
        print(f"{result.status:<5} {result.message}")
    failed = sum(r.status == "FAIL" for r in results)
    passed = sum(r.status == "pass" for r in results)
    skipped = sum(r.status == "skip" for r in results)
    print(f"{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


def _overrides(pairs: list[str]) -> dict[str, Path]:
    overrides = {}
    for pair in pairs:
        service_id, sep, path = pair.partition("=")
        if not sep or not service_id or not path:
            raise SystemExit(f"--source expects ID=PATH, got '{pair}'")
        overrides[service_id] = Path(path).expanduser()
    return overrides


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="portfolio_check", description=__doc__)
    parser.add_argument(
        "--repos-root",
        type=Path,
        default=Path(os.environ.get("REPOS_ROOT") or INDEX_ROOT.parent),
        help="folder that holds the sibling repositories (default: REPOS_ROOT or the parent of this repository)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="offline checks of the catalog, this repository and every listed repository")
    commands.add_parser("readme", help="rewrite the generated cards in README.md from the catalog")
    covers = commands.add_parser("covers", help="copy each repository cover into assets/ at card size")
    covers.add_argument("--source", action="append", default=[], metavar="ID=PATH", help="cover to use for a service")
    commands.add_parser("siblings", help="print '<GitHub name> <local folder>' for every listed repository")
    commands.add_parser("owner", help="print the GitHub owner of the listed repositories")
    commands.add_parser("live", help="compare the catalog with the live GitHub repositories (network, read-only)")
    args = parser.parse_args(argv)

    try:
        catalog = load(CATALOG)
    except CatalogError as error:
        print(f"FAIL  {error}", file=sys.stderr)
        return 1

    if args.command == "check":
        return _report(checks.run(catalog, INDEX_ROOT, args.repos_root.resolve()))
    if args.command in ("owner", "siblings"):
        siblings = [f"{repo.name} {repo.local}" for repo in catalog.all_repos()[1:]]
        print(catalog.owner if args.command == "owner" else "\n".join(siblings))
        return 0
    if args.command == "readme":
        path = INDEX_ROOT / "README.md"
        text = path.read_text(encoding="utf-8")
        path.write_text(readme.replace_generated(text, render.cards_block(catalog)), encoding="utf-8")
        print("README.md cards regenerated from data/catalog.yaml")
        return 0
    if args.command == "covers":
        for note in refresh(catalog, INDEX_ROOT, args.repos_root.resolve(), _overrides(args.source)):
            print(note)
        return 0
    return _report(live_run(catalog))


if __name__ == "__main__":
    sys.exit(main())
