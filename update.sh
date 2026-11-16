#!/usr/bin/env bash
# Pull the latest toolkit and reinstall everything, including external components.
#   ./update.sh [claude|codex|agy|both|all] [--replace-legacy] [--no-external] [--yes]   (default: all)
# Externals install their latest release. Before installing, this lists what each one changed
# since the last update (needs an authenticated `gh`) and asks to continue; --yes skips the
# question. Read release notes that change behaviour: a release can contradict a toolkit rule,
# which the toolkit then guards rather than pins. Vendored skills (toolkit/vendored.json) arrive
# with `git pull`; they change only when a maintainer runs scripts/vendor_sync.py --update.
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
  YES=0
  NO_EXTERNAL=0
  ARGS=()
  for a in "$@"; do
    if [ "$a" = "--yes" ]; then YES=1; else ARGS+=("$a"); fi
    if [ "$a" = "--no-external" ]; then NO_EXTERNAL=1; fi
  done
  if git rev-parse --abbrev-ref '@{u}' >/dev/null 2>&1; then
    git pull --ff-only
  else
    echo "no upstream branch configured; skipping git pull"
  fi
  STAMP="$HOME/.toolkit-last-update"
  SINCE="$(cat "$STAMP" 2>/dev/null || true)"
  if [ "$NO_EXTERNAL" -eq 0 ]; then
    if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
      echo "External components: changes since ${SINCE:-the last 30 days}"
      python3 scripts/upstream_drift.py --externals ${SINCE:+--since "$SINCE"} || true
    else
      echo "gh not available or not signed in: cannot list external changes; read their release notes first"
    fi
    if [ "$YES" -eq 0 ]; then
      if [ -t 0 ]; then
        read -r -p "Install these versions? [y/N] " reply
        case "$reply" in y|Y|yes) ;; *) echo "stopped; nothing installed"; exit 1 ;; esac
      else
        echo "no terminal to confirm on: rerun with --yes to install without the review prompt"
        exit 1
      fi
    fi
  fi
  ./install.sh "$TARGET" --apply ${ARGS[@]+"${ARGS[@]}"}
  date +%F > "$STAMP"
}
