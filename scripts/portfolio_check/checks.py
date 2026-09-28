"""Offline consistency checks: the catalog, this repository, and each sibling repository it lists."""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass
from pathlib import Path

from . import readme, render
from .covers import COVER_SIZE, same_pixels
from .model import Catalog, Repo, Service, catalog_rule_errors

REQUIRED_FILES = ("README.md", "LICENSE", "CHANGELOG.md", "docs/assets/cover.png")
MINIMAL_FILES = ("README.md", "LICENSE")
MIN_ADRS = 2
PREVIEW_SIZE = (1280, 640)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_HEADER_LEN = 24  # signature, IHDR length and type, width, height


@dataclass(frozen=True)
class Result:
    status: str  # "pass", "FAIL" or "skip"
    message: str


def _pass(message: str) -> Result:
    return Result("pass", message)


def _fail(message: str) -> Result:
    return Result("FAIL", message)


def _skip(message: str) -> Result:
    return Result("skip", message)


def png_size(path: Path) -> tuple[int, int] | None:
    """Width and height from the PNG header, or None when the file is not a PNG."""
    head = path.read_bytes()[:PNG_HEADER_LEN]
    if len(head) < PNG_HEADER_LEN or not head.startswith(PNG_SIGNATURE) or head[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", head[16:24])
    return width, height


def adr_count(root: Path) -> int:
    return len(list((root / "docs" / "adr").glob("[0-9][0-9][0-9][0-9]-*.md")))


def structure_results(
    name: str, root: Path, files: tuple[str, ...], min_adrs: int, *, sections: bool = True
) -> list[Result]:
    """Required files, ADR count and README section order for one repository."""
    results = []
    missing = [f for f in files if not (root / f).is_file()]
    results.append(_fail(f"{name}: missing {', '.join(missing)}") if missing else _pass(f"{name}: required files"))
    if min_adrs:
        count = adr_count(root)
        adr_ok = count >= min_adrs
        results.append((_pass if adr_ok else _fail)(f"{name}: {count} ADRs in docs/adr (at least {min_adrs})"))
    readme_path = root / "README.md"
    if sections and readme_path.is_file():
        errors = readme.section_order_errors(readme_path.read_text(encoding="utf-8"))
        results.extend(_fail(f"{name}: README {e}") for e in errors)
        if not errors:
            results.append(_pass(f"{name}: README sections follow the standard order"))
    return results


def cover_results(catalog: Catalog, index_root: Path, repos_root: Path) -> list[Result]:
    """Each card cover exists at card size and holds the pixels made from the repository's current cover."""
    results = []
    expected = {f"{s.id}.png" for s in catalog.services}
    actual = {p.name for p in (index_root / "assets").glob("*.png")}
    results.extend(
        _fail(f"assets/{orphan} belongs to no service in the catalog") for orphan in sorted(actual - expected)
    )
    for service in catalog.services:
        name = f"{service.id} cover"
        card = index_root / render.cover_path(service)
        if not card.is_file():
            results.append(_fail(f"{name}: {render.cover_path(service)} is missing; run make covers"))
            continue
        size = png_size(card)
        if size != COVER_SIZE:
            results.append(_fail(f"{name}: {render.cover_path(service)} is {size}, expected PNG {COVER_SIZE}"))
            continue
        source = repos_root / service.repo.local / "docs/assets/cover.png"
        if not source.is_file():
            if service.repo.status == "in-progress":
                results.append(_skip(f"{name}: {service.repo.name} has no cover yet; card keeps the approved cover"))
            else:
                results.append(_fail(f"{name}: {service.repo.local}/docs/assets/cover.png is missing"))
            continue
        try:
            same = same_pixels(card, source)
        except ValueError as error:
            results.append(_fail(f"{name}: {error}"))
        else:
            if same:
                results.append(_pass(f"{name}: made from {service.repo.name}/docs/assets/cover.png"))
            else:
                results.append(
                    _fail(f"{name}: differs from {service.repo.name}/docs/assets/cover.png; run make covers")
                )
    return results


def _repo_results(catalog: Catalog, repo: Repo, repos_root: Path, service: Service | None) -> list[Result]:
    root = repos_root / repo.local
    label = repo.name if repo.local == repo.name else f"{repo.name} ({repo.local})"
    if not root.is_dir():
        if repo.status == "in-progress":
            return [_skip(f"{label}: in progress and not checked out at {root}")]
        return [_fail(f"{label}: no folder at {root}; clone it there or set REPOS_ROOT")]
    if not repo.standard:
        return [
            _pass(f"{label}: folder found (extra repository)"),
            *structure_results(label, root, MINIMAL_FILES, 0, sections=False),
        ]
    if repo.status == "in-progress":
        return [_pass(f"{label}: folder found"), _skip(f"{label}: in progress, structure checks skipped")]
    results = [_pass(f"{label}: folder found"), *structure_results(label, root, REQUIRED_FILES, MIN_ADRS)]
    index_url = catalog.repo_url(catalog.index)
    text = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").is_file() else ""
    results.append(
        _pass(f"{label}: README links to {catalog.index.name}")
        if re.search(re.escape(index_url) + r"(?![\w.-])", text)
        else _fail(f"{label}: README has no link to {index_url}")
    )
    if service is not None:
        artifact = root / service.artifact.path
        exists = artifact.is_dir() if service.artifact.path.endswith("/") else artifact.is_file()
        results.append(
            _pass(f"{label}: artifact {service.artifact.path} exists")
            if exists
            else _fail(f"{label}: artifact {service.artifact.path} not found")
        )
    return results


def index_results(catalog: Catalog, index_root: Path) -> list[Result]:
    """This repository: catalog rules, its own structure, the generated cards and the social preview."""
    errors = catalog_rule_errors(catalog)
    results = [_fail(f"catalog: {e}") for e in errors] or [_pass("catalog: names, offers, descriptions and topics")]
    results.extend(structure_results(catalog.index.name, index_root, (*MINIMAL_FILES, "CHANGELOG.md"), MIN_ADRS))
    readme_text = (index_root / "README.md").read_text(encoding="utf-8")
    try:
        current = readme.replace_generated(readme_text, render.cards_block(catalog)) == readme_text
    except ValueError as error:
        results.append(_fail(f"{catalog.index.name}: {error}"))
    else:
        results.append(
            _pass(f"{catalog.index.name}: README cards match data/catalog.yaml")
            if current
            else _fail(f"{catalog.index.name}: README cards differ from data/catalog.yaml; run make readme")
        )
    preview = index_root / "docs/assets/social-preview.png"
    size = png_size(preview) if preview.is_file() else None
    results.append(
        _pass(f"{catalog.index.name}: social preview is {PREVIEW_SIZE[0]}x{PREVIEW_SIZE[1]}")
        if size == PREVIEW_SIZE
        else _fail(f"{catalog.index.name}: docs/assets/social-preview.png must be a {PREVIEW_SIZE} PNG, got {size}")
    )
    return results


def run(catalog: Catalog, index_root: Path, repos_root: Path) -> list[Result]:
    results = index_results(catalog, index_root)
    results.extend(cover_results(catalog, index_root, repos_root))
    for service in catalog.services:
        results.extend(_repo_results(catalog, service.repo, repos_root, service))
    for extra in catalog.more:
        results.extend(_repo_results(catalog, extra.repo, repos_root, None))
    return results
