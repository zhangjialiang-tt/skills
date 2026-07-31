#!/usr/bin/env bash
# Deterministic test entry for inkos-story-steward.
# Usage: bash inkos-story-steward/scripts/run_tests.sh
# Requirements: Python 3.11+, pytest, PyYAML
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Compile check ==="
python -m compileall "$SCRIPT_DIR" -q

echo "=== Unit tests ==="
python -m pytest -q "$SKILL_DIR/tests"

echo "=== Smoke: red zone classification ==="
python "$SCRIPT_DIR/classify_path.py" books/test-book/chapters/index.json && {
  echo "FAIL: expected exit 1 for red zone"; exit 1
} || true

echo "=== Smoke: enforce without allow ==="
python "$SCRIPT_DIR/verify_diff.py" --mode enforce --files books/test/story/book_rules.md && {
  echo "FAIL: expected exit 1 without --allow"; exit 1
} || true

echo "=== All checks passed ==="
