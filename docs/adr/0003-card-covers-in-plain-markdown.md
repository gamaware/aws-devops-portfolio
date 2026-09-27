# ADR 0003: Keep card covers as small copies in plain Markdown

## Status

Accepted

## Context

Each card shows the cover of its Upwork offer, which each repository keeps as a 1600x1200 `docs/assets/cover.png`.
GitHub renders a Markdown image at its natural width up to the page width, so ten full-size covers make a long page.
Sizing an image needs an HTML `img` tag, which markdownlint rule MD033 rejects, and this portfolio does not suppress
lint rules.

## Decision

`make covers` resizes each repository cover to 640x480 into `assets/<service id>.png`. Cards use plain Markdown
images. `make check` resizes each source again with the Pillow version pinned in `uv.lock` and compares pixels, so
the repository keeps no hash file. A service whose repository has no cover yet
takes its approved Upwork cover through `--source <id>=<path>`.

## Consequences

- The README renders compactly with no inline HTML.
- A cover changed in a repository fails `make check` until `make covers` runs again, so the index cannot show an old
  cover.
- The copies add about 700 KB to this repository.

## Compliance

`make check` fails when a card cover is missing, is not a 640x480 PNG, has no matching service, or holds pixels
that differ from a fresh resize of the repository cover. `tests/test_checks.py` covers each case.

## Notes

Alternatives considered: a manifest of source SHA-256 hashes (secret scanners flag the hex strings), linking the
full-size covers from each repository (long page, and a broken card while a repository is private) and an HTML grid
(needs an MD033 exception).
