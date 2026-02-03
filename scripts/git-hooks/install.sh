#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$ROOT/.githooks"

if [[ ! -d "$HOOKS_DIR" ]]; then
  echo "ERROR: $HOOKS_DIR not found" >&2
  exit 1
fi

chmod +x "$HOOKS_DIR/pre-commit"

git config core.hooksPath "$HOOKS_DIR"

echo "Installed git hooks from $HOOKS_DIR"
