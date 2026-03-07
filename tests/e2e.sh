#!/bin/bash

# End-to-end tests for msg2po using real game translation repositories.
# Tests poify, unpoify, and dir2msgstr against:
#   - Fallout 2 Unofficial Patch (sfall format, MSG/SVE/TXT)
#   - Ascension (WeiDU TRA format)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPOS_DIR="$SCRIPT_DIR/repos"

# Run msg2po CLI commands via uv from the project root
run_cmd() {
  uv run --project "$PROJECT_DIR" "$@"
}

PASS=0

pass() {
  PASS=$((PASS + 1))
  echo "  PASS: $1"
}

fail() {
  echo "  FAIL: $1"
  exit 1
}

clone_if_missing() {
  local url="$1" dest="$2"
  if [ ! -d "$dest" ]; then
    echo "Cloning $url..."
    git clone --depth 1 "$url" "$dest"
  fi
}

reset_repo() {
  cd "$1" && git checkout -q . && git clean -fd -q
}

check_clean() {
  local status
  status=$(git status --porcelain)
  if [ -z "$status" ]; then
    pass "git status is clean"
  else
    echo "$status" | head -10
    fail "git status is dirty"
  fi
}

mkdir -p "$REPOS_DIR"

# ============================================================
# Fallout 2 Unofficial Patch (sfall, MSG/SVE/TXT)
# ============================================================

echo ""
echo "==== Fallout 2 Unofficial Patch ===="

FO2_DIR="$REPOS_DIR/fo2_up"
clone_if_missing "https://github.com/BGforgeNet/Fallout2_Unofficial_Patch.git" "$FO2_DIR"
reset_repo "$FO2_DIR"
cd "$FO2_DIR"

REF_POT="data/text/po/english.pot"
REF_COUNT=$(grep -c '^msgid "' "$REF_POT")

# --- poify ---
echo ""
echo "--- poify ---"

run_cmd poify data/text/english > /dev/null || fail "poify exited with error"
pass "poify exits successfully"

GEN_COUNT=$(grep -c '^msgid "' "$REF_POT")
if [ "$GEN_COUNT" -eq "$REF_COUNT" ]; then
  pass "POT entry count matches reference ($GEN_COUNT)"
else
  fail "POT entry count mismatch: generated=$GEN_COUNT, reference=$REF_COUNT"
fi

check_clean

# --- unpoify ---
echo ""
echo "--- unpoify ---"

run_cmd unpoify data/text/po > /dev/null || fail "unpoify exited with error"
pass "unpoify exits successfully"
check_clean

# --- dir2msgstr ---
echo ""
echo "--- dir2msgstr ---"

run_cmd dir2msgstr --auto --overwrite > /dev/null || fail "dir2msgstr exited with error"
pass "dir2msgstr exits successfully"
check_clean

# ============================================================
# Ascension (WeiDU, TRA)
# ============================================================

echo ""
echo "==== Ascension ===="

ASC_DIR="$REPOS_DIR/ascension"
clone_if_missing "https://github.com/Gibberlings3/Ascension.git" "$ASC_DIR"
reset_repo "$ASC_DIR"
cd "$ASC_DIR"

REF_POT="ascension/lang/po/english.pot"
REF_COUNT=$(grep -c '^msgid "' "$REF_POT")

# --- poify ---
echo ""
echo "--- poify ---"

run_cmd poify ascension/lang/english > /dev/null || fail "poify exited with error"
pass "poify exits successfully"

GEN_COUNT=$(grep -c '^msgid "' "$REF_POT")
if [ "$GEN_COUNT" -eq "$REF_COUNT" ]; then
  pass "POT entry count matches reference ($GEN_COUNT)"
else
  fail "POT entry count mismatch: generated=$GEN_COUNT, reference=$REF_COUNT"
fi

check_clean

# --- unpoify ---
echo ""
echo "--- unpoify ---"

run_cmd unpoify ascension/lang/po > /dev/null || fail "unpoify exited with error"
pass "unpoify exits successfully"
check_clean

# --- dir2msgstr ---
echo ""
echo "--- dir2msgstr ---"

run_cmd dir2msgstr --auto --overwrite > /dev/null || fail "dir2msgstr exited with error"
pass "dir2msgstr exits successfully"
check_clean

reset_repo "$ASC_DIR"

# ============================================================
# Summary
# ============================================================

echo ""
echo "================================"
echo "  e2e: $PASS passed"
echo "================================"
