#!/usr/bin/env bash
# Pre-edit hook: block hand edits to copied and generated files.
# Exit 2 blocks the edit; stderr is shown to the editor as the reason.
set -euo pipefail

if ! command -v jq >/dev/null 2>&1; then
  echo "protect-files hook needs jq to read the edit target; install jq." >&2
  exit 2
fi

FILE="$(jq -r '.tool_input.file_path // empty')"

case "$FILE" in
  */.secrets.baseline)
    echo "Regenerate with: detect-secrets scan --baseline .secrets.baseline" >&2
    exit 2
    ;;
  */docs/diagrams/*.png | */docs/assets/social-preview.png)
    echo "Exported image. Edit the source (docs/diagrams/*.drawio or docs/assets/social-preview.json) and re-render." >&2
    exit 2
    ;;
  */assets/*.png)
    echo "Covers are copied from each repository's docs/assets/cover.png. Run: make covers" >&2
    exit 2
    ;;
esac
exit 0
