#!/usr/bin/env bash
# Shallow-clone every repository listed in data/catalog.yaml into REPOS_ROOT, named by its local folder.
# Used by CI, where the sibling repositories are not checked out. A repository that cannot be cloned is left
# absent; `make check` then fails for a ready repository and skips one marked in progress.
set -euo pipefail

: "${REPOS_ROOT:?set REPOS_ROOT to the folder that receives the clones}"
catalog_cmd=(env PYTHONPATH=scripts uv run --locked python -m portfolio_check)
# The owner comes from data/catalog.yaml unless OWNER overrides it.
OWNER="${OWNER:-$("${catalog_cmd[@]}" owner)}"
mkdir -p "$REPOS_ROOT"

"${catalog_cmd[@]}" siblings | while read -r name local; do
  target="$REPOS_ROOT/$local"
  if [[ -d "$target" ]]; then
    echo "exists  $local"
  elif git clone --quiet --depth 1 "https://github.com/$OWNER/$name.git" "$target"; then
    echo "cloned  $name -> $local"
  else
    echo "missing $name (not cloned)"
  fi
done
