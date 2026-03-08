#!/bin/bash

# Run all tests: linting, type checking, unit tests, and E2E tests.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

echo "==== ruff check ===="
uv run ruff check
echo ""

echo "==== ruff format ===="
uv run ruff format --check
echo ""

echo "==== ty check ===="
uv run ty check
echo ""

echo "==== pytest ===="
uv run pytest -x -q
echo ""

echo "==== e2e ===="
"$SCRIPT_DIR/e2e.sh"
