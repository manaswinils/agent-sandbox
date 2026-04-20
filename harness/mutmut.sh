#!/usr/bin/env bash
# harness/mutmut.sh — Behaviour Harness: Mutation Testing
# Runs mutmut on app.py to validate test quality.
# Mutation score < 60% triggers a warning (non-blocking).
# Called by pipeline Stage 3 TEST after pytest.

set -uo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

THRESHOLD=60

if ! command -v mutmut &>/dev/null; then
    echo "[mutmut] mutmut not installed — skipping mutation testing"
    exit 0
fi

echo "=== [mutmut] Running mutation tests on app.py ==="
mutmut run --paths-to-mutate app.py --tests-dir tests/ 2>&1 || true

# Get results
RESULTS=$(mutmut results 2>&1 || true)
echo "$RESULTS"

# Parse mutation score
KILLED=$(echo "$RESULTS" | grep -oP '(?<=Killed: )\d+' || echo "0")
SURVIVED=$(echo "$RESULTS" | grep -oP '(?<=Survived: )\d+' || echo "0")
TOTAL=$((KILLED + SURVIVED))

if [ "$TOTAL" -eq 0 ]; then
    echo "[mutmut] No mutations generated — check that app.py has testable code"
    exit 0
fi

SCORE=$(( (KILLED * 100) / TOTAL ))
echo ""
echo "=== [mutmut] Mutation score: ${SCORE}% (${KILLED}/${TOTAL} killed) ==="

if [ "$SCORE" -lt "$THRESHOLD" ]; then
    echo "⚠️  [mutmut] Score ${SCORE}% is below threshold ${THRESHOLD}% — tests may be low quality"
    exit 1
else
    echo "✅ [mutmut] Score ${SCORE}% meets threshold ${THRESHOLD}%"
    exit 0
fi
