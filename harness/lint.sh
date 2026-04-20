#!/usr/bin/env bash
# harness/lint.sh — Maintainability Harness: Computational Sensor
# Runs ruff (lint + format check) and mypy (type checking) on the repo.
# Exit code 0 = clean; non-zero = issues found.
# Called by the pipeline Stage 2.5 LINT after IMPLEMENT and before TEST.

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

ERRORS=0

echo "=== [lint] ruff linter ==="
if command -v ruff &>/dev/null; then
    ruff check . --exclude harness,tests,__pycache__,.git,venv,.venv 2>&1 || ERRORS=$((ERRORS+1))
else
    echo "[lint] ruff not installed — skipping"
fi

echo ""
echo "=== [lint] ruff format check ==="
if command -v ruff &>/dev/null; then
    ruff format --check . --exclude harness,tests,__pycache__,.git,venv,.venv 2>&1 || ERRORS=$((ERRORS+1))
else
    echo "[lint] ruff not installed — skipping"
fi

echo ""
echo "=== [lint] mypy type check ==="
if command -v mypy &>/dev/null; then
    mypy app.py --ignore-missing-imports --no-error-summary 2>&1 || ERRORS=$((ERRORS+1))
else
    echo "[lint] mypy not installed — skipping"
fi

echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo "✅ [lint] All checks passed."
    exit 0
else
    echo "⚠️  [lint] $ERRORS check(s) failed. See output above."
    exit 1
fi
