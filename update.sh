#!/usr/bin/env bash
# Pull the latest toolkit and reinstall everything, including external components.
#   ./update.sh [claude|codex|both]     (default: both)
set -euo pipefail
cd "$(dirname "$0")"
if git rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1; then
  git pull --ff-only
else
  echo "no upstream branch configured; skipping git pull"
fi
./install.sh "${1:-both}" --apply --external
