#!/usr/bin/env bash
# Pull the latest toolkit and reinstall everything, including external components.
#   ./update.sh [claude|codex|agy|both|all] [--replace-legacy]   (default: all)
{
  set -euo pipefail
  cd "$(dirname "$0")"
  TARGET="${1:-all}"
  case "$TARGET" in
    claude|codex|agy|both|all) ;;
    *) sed -n '2,3p' "$0"; exit 2 ;;
  esac
  if [ "$#" -gt 0 ]; then
    shift
  fi
  if git rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1; then
    git pull --ff-only
  else
    echo "no upstream branch configured; skipping git pull"
  fi
  exec ./install.sh "$TARGET" --apply --external "$@"
}
