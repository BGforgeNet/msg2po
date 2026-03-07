#!/bin/bash

# Profile msg2po e2e roundtrip: poify, unpoify, dir2msgstr.
# Uses built-in --profile flag for cProfile output.
# Usage: ./tests/profile_it.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPOS_DIR="$SCRIPT_DIR/repos"

run_cmd() {
  uv run --project "$PROJECT_DIR" "$@"
}

time_cmd() {
  local label="$1"
  shift
  local start end elapsed
  start=$(date +%s%N)
  "$@"
  end=$(date +%s%N)
  elapsed=$(( (end - start) / 1000000 ))
  printf "\n  %-20s %6dms\n" "$label" "$elapsed"
}

reset_repo() {
  cd "$1"
  git checkout -q .
  git clean -fd -q
}

# ============================================================
echo "============================================================"
echo "Fallout 2 Unofficial Patch (MSG/SVE/TXT, ~900 files)"
echo "============================================================"

FO2_DIR="$REPOS_DIR/fo2_up"
cd "$FO2_DIR"

echo ""
echo "--- poify ---"
time_cmd "poify" run_cmd poify --profile data/text/english
reset_repo "$FO2_DIR"

echo ""
echo "--- unpoify ---"
time_cmd "unpoify" run_cmd unpoify --profile data/text/po
reset_repo "$FO2_DIR"

echo ""
echo "--- dir2msgstr ---"
run_cmd unpoify data/text/po > /dev/null 2>/dev/null
time_cmd "dir2msgstr" run_cmd dir2msgstr --profile --auto --overwrite
reset_repo "$FO2_DIR"

# ============================================================
echo ""
echo "============================================================"
echo "Ascension (TRA, ~26 files)"
echo "============================================================"

ASC_DIR="$REPOS_DIR/ascension"
cd "$ASC_DIR"

echo ""
echo "--- poify ---"
time_cmd "poify" run_cmd poify --profile ascension/lang/english
reset_repo "$ASC_DIR"

echo ""
echo "--- unpoify ---"
time_cmd "unpoify" run_cmd unpoify --profile ascension/lang/po
reset_repo "$ASC_DIR"

echo ""
echo "--- dir2msgstr ---"
run_cmd unpoify ascension/lang/po > /dev/null 2>/dev/null
time_cmd "dir2msgstr" run_cmd dir2msgstr --profile --auto --overwrite
reset_repo "$ASC_DIR"

echo ""
echo "============================================================"
echo "Done"
echo "============================================================"
