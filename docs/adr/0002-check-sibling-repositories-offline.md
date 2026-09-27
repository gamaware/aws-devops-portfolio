# ADR 0002: Check the sibling repositories offline from local clones

## Status

Accepted

## Context

The portfolio standard fixes the required files, the README section order and the description pattern for every
repository. Each repository checks its own content with `make verify`, but nothing checks that the eleven
repositories still agree with the standard and with this index. Calling the GitHub API for that would need a token
and the network in every run, and would fail for repositories that are not public yet.

## Decision

`make check` reads each repository from a folder next to this one (or from `REPOS_ROOT`), named by the catalog's
`local` field. It checks required files, at least two ADRs, the README section order, the link back to this index,
the artifact path each card names, and the card cover. CI clones the public repositories with
`scripts/clone-siblings.sh` into a temporary folder and runs the same command. A repository marked
`status: in-progress` may be absent and skips the structure checks; a ready repository that is missing fails.

## Consequences

- Contributors run the same check as CI, with no token and no AWS account.
- The check sees the local working copy of each repository, so a change that is not pushed yet passes locally and
  fails in CI until it lands. That is the intended order.
- A folder name that differs from the GitHub name (`terraform-aws-baseline-lab` for `terraform-aws-rescue-lab`)
  needs the `local` field.

## Compliance

`tests/test_checks.py` builds a compliant repository in a temporary folder and breaks one rule per test. The catalog
rejects `local` values that are not plain folder names, so the check cannot read outside `REPOS_ROOT`.

## Notes

Alternatives considered: git submodules (pin old commits and complicate every clone) and the GitHub API for file
checks (needs a token and the network; kept for the settings comparison in ADR 0004).
