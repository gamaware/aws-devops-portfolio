# 0001. Generate the service cards from one catalog file

## Status

Accepted

## Context

The index describes ten services, each with an Upwork offer, a repository, an artifact and a verification scope.
The same facts also appear in each repository's GitHub description and topics. In a hand-written README, a
renamed repository or a new offer ID means edits in two or three places, and nothing notices a missed one.

## Decision

`data/catalog.yaml` holds every service, offer ID, repository name, local folder, artifact path, description and
topic list. `make readme` renders the overview table and the cards between the `BEGIN GENERATED` and
`END GENERATED` markers in `README.md`. Prose outside the markers stays hand-written. An offer marked
`offer_status: pending` renders without a link, and a repository marked `status: in-progress` shows that label on its
card.

## Consequences

- One edit to the catalog changes the table, the card and the expected GitHub settings together.
- Card text lives in YAML, so a reviewer reads it there, not in the README diff alone.
- The catalog is a small schema that `scripts/portfolio_check/model.py` enforces; a service that does not fit it
  needs a schema change and a test.

## Compliance

`make check` renders the cards in memory and fails when `README.md` differs. `tests/test_render.py` covers the card
fields, the pending offer and the in-progress label.

## Notes

Alternatives considered: a hand-written README with a link checker (catches dead links, not stale facts), and a
static site generator (more tooling than one page needs, and GitHub renders the README directly).
