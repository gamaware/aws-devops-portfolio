.DEFAULT_GOAL := help
SHELL := bash
.SHELLFLAGS := -euo pipefail -c

UV ?= uv
RUN := $(UV) run --locked
PY := PYTHONPATH=scripts $(RUN) python -m portfolio_check
# Folder that holds the sibling repositories; defaults to the parent of this repository.
REPOS_ROOT ?= $(abspath ..)

.PHONY: help setup lint test check verify readme covers test-live clean

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

setup: ## Install the pinned Python toolchain into .venv
	$(UV) sync --locked

lint: ## Ruff lint and format check
	$(RUN) ruff check scripts tests
	$(RUN) ruff format --check scripts tests

test: ## Unit tests for the catalog model, README rules, cards and checks
	$(RUN) pytest

check: ## Check the catalog, this README and every listed repository (offline)
	REPOS_ROOT="$(REPOS_ROOT)" $(PY) check

verify: lint test check ## Ruff, pytest and the catalog check; CI also runs the shared lint and security workflows
	@echo "verify: all checks passed"

readme: ## Regenerate the service cards in README.md from data/catalog.yaml
	$(PY) readme

covers: ## Copy each repository cover into assets/ at card size (pass SOURCES="--source id=path" to override)
	REPOS_ROOT="$(REPOS_ROOT)" $(PY) covers $(SOURCES)

test-live: ## Manual only: compare the catalog with live GitHub settings (read-only, needs gh auth)
	GITHUB_TOKEN="$$(gh auth token)" $(PY) live

clean: ## Remove caches
	rm -rf .pytest_cache .ruff_cache
