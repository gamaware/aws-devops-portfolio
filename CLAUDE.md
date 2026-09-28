# CLAUDE.md

Project instructions for Claude Code in `aws-devops-portfolio`.

## Overview

The index of the AWS and DevOps portfolio: one card per Upwork service, each linked to the public repository that
backs it. `data/catalog.yaml` is the single source; `scripts/portfolio_check` renders the cards and checks every
listed repository against the portfolio standard.

## Structure

- `data/catalog.yaml`: services, offer names, repository names (GitHub) and local folders, artifacts, descriptions,
  topics.
- `scripts/portfolio_check/`: `model` (load and validate), `readme` (section order, generated markers), `render`
  (cards), `checks` (offline), `covers` (Pillow resize), `live` (GitHub GraphQL, read-only), `__main__`.
- `assets/`: card covers made by `make covers`. `docs/checks.md` lists every rule.

## Working rules

- Never edit text between `BEGIN GENERATED` and `END GENERATED` in `README.md`; change the catalog and run
  `make readme`.
- Never edit `assets/*.png` by hand; run `make covers`.
- A rule change in `scripts/` needs a test in `tests/`, a row in `docs/checks.md` and, when it changes a decision,
  an ADR.
- Links use GitHub repository names; `local` only names the folder on disk.
- Never run anything against AWS. `make test-live` reads GitHub only, and only when the maintainer asks.

## Verification

`make verify` must pass before every commit: ruff, pytest and `python -m portfolio_check check`. It needs the
sibling repositories next to this one, or `REPOS_ROOT`.

## Git workflow

Conventional commits, feature branches, squash merge. Pre-commit hooks: file hygiene, detect-secrets, gitleaks,
markdownlint, actionlint, zizmor, shellcheck, shellharden, ruff, conventional-pre-commit.

## Claude Code hooks

- `PreToolUse` (`.claude/hooks/protect-files.sh`): blocks edits to card covers, exported images and the secrets
  baseline.
- `PostToolUse` (`.claude/hooks/post-edit.sh`): formats edited shell, Markdown and Python files.

## CI and code review

`.github/workflows/ci.yml` calls the shared workflows in `gamaware/.github` (docs, actions, secrets, security),
clones the listed repositories and runs `make verify`. `.github/workflows/scorecard.yml` runs OpenSSF Scorecard on
`main`. CodeRabbit (`.coderabbit.yaml`) and GitHub Copilot (`.github/copilot-instructions.md`) review every pull
request.
