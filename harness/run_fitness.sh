#!/usr/bin/env bash
# harness/run_fitness.sh — Architecture Fitness Harness runner
# Executes all fitness functions from harness/fitness.py.
# Exit code 0 = all constraints satisfied; non-zero = violations found.

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== [fitness] Running architecture fitness functions ==="
python harness/fitness.py
