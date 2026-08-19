#!/usr/bin/env bash
set -euo pipefail

if ! command -v jp2a >/dev/null 2>&1; then
  echo "jp2a is required" >&2
  exit 1
fi

if ! command -v fastfetch >/dev/null 2>&1; then
  echo "fastfetch is required" >&2
  exit 1
fi

if [[ ! -s .cache/github-avatar.jpg || ! -s .cache/metrics.json ]]; then
  echo "Run scripts/fetch_github_metrics.py first" >&2
  exit 1
fi

jp2a \
  --colors \
  --background=dark \
  --width=58 \
  .cache/github-avatar.jpg \
  | fastfetch \
      --config ./github-fastfetch.jsonc \
      --logo-type file-raw \
      --logo - \
      --pipe false \
  | python3 scripts/ansi_to_svg.py github-terminal.svg
