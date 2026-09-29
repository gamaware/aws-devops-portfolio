# Checks

`make check` runs `python -m portfolio_check check`. Each line of its output starts with `pass`, `FAIL` or `skip`,
and the run fails on any `FAIL`. The rules come from the portfolio standard (README template, required files and
cohesion rules).

## Catalog rules

These need only `data/catalog.yaml` (`scripts/portfolio_check/model.py`).

| Rule | Source |
| --- | --- |
| Service IDs, offer names, repository names and local folders are unique | Catalog integrity |
| No mapping repeats a key (YAML loaders would keep only the last value) | Catalog integrity |
| `more`, when present, is a list; only its repositories may set `standard: false` | Catalog integrity |
| Service IDs, repository names and local folders are lowercase words joined by hyphens, so no path leaves `assets/` or `REPOS_ROOT` | Catalog integrity; ADR 0002 |
| `profile_url` is an Upwork freelancer profile; every card links it as "*service* on Upwork" | Upwork links |
| Artifact paths are relative and stay inside the repository | Catalog integrity |
| Descriptions read "Demonstrates *capability* through *artifact*; verified *scope*." within 350 characters | Standard, cohesion rules; GitHub limit |
| At most 10 topics, each lowercase letters, digits and hyphens, 50 characters at most | Standard; GitHub topic rules |
| Topics include `aws`, `devops`, `portfolio` and the type topic (`lab` or `sample-deliverable`) | Standard, cohesion rules |

## This repository

| Rule | Source |
| --- | --- |
| `README.md`, `LICENSE`, `CHANGELOG.md` and at least two ADRs exist | Standard, layout |
| The README sections follow the standard order | Standard, README template |
| The cards between the generated markers match `make readme` output | ADR 0001 |
| `docs/assets/social-preview.png` is a 1280x640 PNG that decodes completely | Standard, social preview |
| Every card cover is a 640x480 PNG with the pixels of the current repository cover, and every cover belongs to a service | ADR 0003 |

## Each listed repository

The check reads each repository from `REPOS_ROOT/<local>`, where `REPOS_ROOT` defaults to the parent folder of this repository.

| Rule | Applies to |
| --- | --- |
| The folder exists | Ready repositories; the check skips an absent in-progress one |
| `README.md`, `LICENSE`, `CHANGELOG.md` and `docs/assets/cover.png` exist | Ready repositories |
| `docs/adr/` holds at least two `NNNN-title.md` records | Ready repositories |
| The README's level-two headings follow the standard order, opening with "What this proves" or "Executive summary", with an optional closing "License" | Ready repositories |
| The README links to `https://github.com/gamaware/aws-devops-portfolio` | Ready repositories |
| The artifact path on the card exists (a folder when the path ends in `/`) | Ready repositories |
| `README.md` and `LICENSE` exist | The extra repository under "More" |

## Covers

`make covers` rebuilds `assets/<service id>.png` from each repository's `docs/assets/cover.png`. `make check` resizes
the source again with the Pillow version pinned in `uv.lock` and compares pixels, and asks for `make covers` when they
differ.

## Live comparison

`make test-live` compares the catalog with GitHub (visibility, description, topics and the custom social preview
flag) through the GraphQL API. It only reads, and only the maintainer runs it; see ADR 0004.
