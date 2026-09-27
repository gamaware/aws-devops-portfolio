"""Render the service cards that sit between the generated markers in README.md."""

from __future__ import annotations

import textwrap

from .model import Catalog, Service

LINE_LENGTH = 120  # markdownlint MD013 in this repository
KIND_LABEL = {"lab": "lab", "labs": "teaching labs", "sample": "fictional sample deliverable", "index": "index"}


def cover_path(service: Service) -> str:
    return f"assets/{service.id}.png"


def anchor(title: str) -> str:
    """GitHub's heading anchor: lowercase, spaces to hyphens, punctuation other than hyphens dropped."""
    kept = "".join(c for c in title.lower() if c.isalnum() or c in " -")
    return kept.replace(" ", "-")


def _offer_link(catalog: Catalog, service: Service) -> str:
    if service.offer_status == "pending":
        return f"{service.offer} (listing pending on Upwork)"
    return f"[{service.offer}]({catalog.offer_url(service)})"


def _repo_line(catalog: Catalog, service: Service) -> str:
    repo = service.repo
    line = f"[`{repo.name}`]({catalog.repo_url(repo)}), {KIND_LABEL[repo.kind]}"
    if repo.status == "in-progress":
        line += " (in progress)"
    return line


def overview_table(catalog: Catalog) -> list[str]:
    rows = [
        "| Service | Repository | Strongest artifact | Upwork offer |",
        "| --- | --- | --- | --- |",
    ]
    for service in catalog.services:
        offer = "pending" if service.offer_status == "pending" else f"[Open]({catalog.offer_url(service)})"
        rows.append(
            f"| [{service.offer}](#{anchor(service.offer)}) "
            f"| [`{service.repo.name}`]({catalog.repo_url(service.repo)}) "
            f"| [{service.artifact.label}]({catalog.artifact_url(service)}) "
            f"| {offer} |"
        )
    return rows


def bullet(text: str) -> list[str]:
    """One list item wrapped to the Markdown line length, continuation lines indented under the text."""
    return textwrap.wrap(
        text,
        width=LINE_LENGTH,
        initial_indent="- ",
        subsequent_indent="  ",
        break_long_words=False,
        break_on_hyphens=False,
    )


def card(catalog: Catalog, service: Service) -> list[str]:
    fields = [
        f"**Client problem:** {service.problem}",
        f"**Repository:** {_repo_line(catalog, service)}",
        f"**Strongest artifact:** [{service.artifact.label}]({catalog.artifact_url(service)}). "
        f"{service.artifact.summary}",
        f"**Verification scope:** {service.verification}",
        f"**Upwork offer:** {_offer_link(catalog, service)}",
    ]
    return [
        f"### {service.offer}",
        "",
        f"[![{service.offer} cover]({cover_path(service)})]({catalog.repo_url(service.repo)})",
        "",
        *(line for field in fields for line in bullet(field)),
        "",
    ]


def more(catalog: Catalog) -> list[str]:
    if not catalog.more:
        return []
    lines = ["### More", ""]
    for extra in catalog.more:
        lines.extend(
            bullet(
                f"[`{extra.repo.name}`]({catalog.repo_url(extra.repo)}), {KIND_LABEL[extra.repo.kind]}: {extra.summary}"
            )
        )
    lines.append("")
    return lines


def cards_block(catalog: Catalog) -> str:
    """The Markdown between the markers: overview table, one card per service, then extra repositories."""
    lines = ["", *overview_table(catalog), ""]
    for service in catalog.services:
        lines.extend(card(catalog, service))
    lines.extend(more(catalog))
    return "\n".join(lines) + "\n"
