# Changelog

All notable changes to this repository. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and releases use [Semantic Versioning](https://semver.org/) for the catalog schema and the `make` targets.

## Unreleased

### Added

- `data/catalog.yaml` with the ten services, their Upwork offers and repositories, and one extra repository.
- `scripts/portfolio_check`: catalog validation, README section-order rules, card rendering, the offline check
  across every listed repository, cover copies and a read-only GitHub comparison.
- Service cards in `README.md` generated from the catalog, with 640x480 covers in `assets/`.
- Tests for every rule, `make verify`, `make test-live`, and `scripts/clone-siblings.sh` for CI.
- ADRs, the context diagram, the check reference, the social preview and CI calling the shared workflows pinned to
  a commit SHA.

### Fixed

- The catalog rejects repeated YAML keys, a `more` value that is not a list, and `standard: false` on a service.
- The social preview check decodes the whole PNG; an unreadable cover or a missing README is reported as `FAIL`
  instead of stopping the run.
- README section checks track fence length and character, so a longer fence can hold a triple-backtick example.
- CI runs weekly and checks links to the portfolio repositories; Scorecard no longer publishes results or requests an
  id-token; `scripts/clone-siblings.sh` takes the owner from the catalog.
