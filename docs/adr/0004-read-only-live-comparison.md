# ADR 0004: Compare with live GitHub settings only on demand, read-only

## Status

Accepted

## Context

Repository descriptions, topics, visibility and the uploaded social preview live in GitHub settings, not in any file
the offline check can read. They drift when someone edits them in the web interface. Checking them needs a token and
the network, and repositories that are not public yet would fail every CI run.

## Decision

`make test-live` reads each repository through the GitHub GraphQL API with the token from `gh auth token` and
compares visibility, description, topics and the custom social preview flag with the catalog. It only reads, prints
differences and writes nothing. The extra repository keeps its own settings; the comparison covers only its visibility.
This repository creates no AWS resources, so the live test uses no AWS profile.

## Consequences

- The maintainer finds drift in GitHub settings when running the target; pull requests do not.
- Fixing drift stays a manual step: update the repository settings, or update the catalog if the new text is right.

## Compliance

`scripts/portfolio_check/live.py` sends only GraphQL queries, never mutations. `make verify` does not call it, and CI
never runs it.

## Notes

Alternatives considered: running the comparison in CI with a token (fails until every repository is public and adds
a secret for little gain) and setting descriptions and topics from the catalog automatically (a write path the index
does not need).
