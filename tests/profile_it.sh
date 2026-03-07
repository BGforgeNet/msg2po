#!/bin/bash

# Profile msg2po e2e roundtrip: poify, unpoify, dir2msgstr.
# Pass --profile to enable cProfile breakdown per command.
# Usage: ./tests/profile_it.sh [--profile]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPOS_DIR="$SCRIPT_DIR/repos"

PROFILE_FLAG=""
if [[ "${1:-}" == "--profile" ]]; then
  PROFILE_FLAG="--profile"
fi

run_cmd() {
  uv run --project "$PROJECT_DIR" "$@" $PROFILE_FLAG
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
time_cmd "poify" run_cmd poify data/text/english
reset_repo "$FO2_DIR"

echo ""
echo "--- unpoify ---"
time_cmd "unpoify" run_cmd unpoify data/text/po
reset_repo "$FO2_DIR"

echo ""
echo "--- dir2msgstr ---"
run_cmd unpoify data/text/po > /dev/null 2>/dev/null
time_cmd "dir2msgstr" run_cmd dir2msgstr --auto --overwrite
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
time_cmd "poify" run_cmd poify ascension/lang/english
reset_repo "$ASC_DIR"

echo ""
echo "--- unpoify ---"
time_cmd "unpoify" run_cmd unpoify ascension/lang/po
reset_repo "$ASC_DIR"

echo ""
echo "--- dir2msgstr ---"
run_cmd unpoify ascension/lang/po > /dev/null 2>/dev/null
time_cmd "dir2msgstr" run_cmd dir2msgstr --auto --overwrite
reset_repo "$ASC_DIR"

echo ""
echo "============================================================"
echo "Done"
echo "============================================================"
