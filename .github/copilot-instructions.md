# Copilot code review instructions

This repository is the index of a public AWS and DevOps portfolio: one card per Upwork service offer, each backed by
a public repository. When reviewing pull requests:

- Check that `README.md` text between `BEGIN GENERATED` and `END GENERATED` markers comes from `make readme`
  and `data/catalog.yaml`, not from hand edits.
- Check that any change to `data/catalog.yaml` or `scripts/` keeps `make verify` passing and updates
  `docs/checks.md` when a rule changes.
- Flag claims of production use, measured client savings, or findings attributed to a real organization.
- Flag any real AWS account ID, ARN, IP address, email address or client name.
- Flag suppressed lint rules; fix violations instead of suppressing them.
- Workflows: `permissions: {}` at the top, SHA-pinned actions, no `pull_request_target`, no cloud credentials.
