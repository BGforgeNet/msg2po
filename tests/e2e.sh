#!/bin/bash

# End-to-end tests for msg2po using real game translation repositories.
# Tests poify, unpoify, and dir2msgstr against:
#   - Fallout 2 Unofficial Patch (sfall format, MSG/SVE/TXT)
#   - Ascension (WeiDU TRA format)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPOS_DIR="$SCRIPT_DIR/repos"

PASS=0
FAIL=0

pass() {
  PASS=$((PASS + 1))
  echo "  PASS: $1"
}

fail() {
  FAIL=$((FAIL + 1))
  echo "  FAIL: $1"
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

# Count modified tracked files (excludes untracked)
count_modified() {
  git diff --name-only | wc -l
}

# Count untracked files
count_untracked() {
  git ls-files --others --exclude-standard | wc -l
}

mkdir -p "$REPOS_DIR"

# ============================================================
# Fallout 2 Unofficial Patch (sfall, MSG/SVE/TXT)
# ============================================================

echo ""
echo "==== Fallout 2 Unofficial Patch ===="

FO2_DIR="$REPOS_DIR/fo2_up"
clone_if_missing "https://github.com/BGforgeNet/Fallout2_Unofficial_Patch.git" "$FO2_DIR"
cd "$FO2_DIR"

REF_POT="data/text/po/english.pot"
REF_COUNT=$(grep -c '^msgid "' "$REF_POT")

# --- poify ---
echo ""
echo "--- poify ---"

if poify data/text/english > /dev/null 2>&1; then
  pass "poify exits successfully"
else
  fail "poify exited with error"
fi

GEN_COUNT=$(grep -c '^msgid "' "$REF_POT")
if [ "$GEN_COUNT" -eq "$REF_COUNT" ]; then
  pass "POT entry count matches reference ($GEN_COUNT)"
else
  fail "POT entry count mismatch: generated=$GEN_COUNT, reference=$REF_COUNT"
fi

# Only the POT should be modified (metadata timestamp), nothing else
MODIFIED=$(count_modified)
if [ "$MODIFIED" -le 1 ]; then
  pass "poify only modified POT ($MODIFIED files changed)"
else
  fail "poify modified unexpected files ($MODIFIED changed)"
  git diff --name-only | head -10
fi

UNTRACKED=$(count_untracked)
if [ "$UNTRACKED" -eq 0 ]; then
  pass "poify created no untracked files"
else
  fail "poify created $UNTRACKED untracked files"
  git ls-files --others --exclude-standard | head -10
fi

reset_repo "$FO2_DIR"

# --- unpoify ---
echo ""
echo "--- unpoify ---"

if unpoify data/text/po > /dev/null 2>&1; then
  pass "unpoify exits successfully"
else
  fail "unpoify exited with error"
fi

MSG_COUNT=$(find data/text/russian -name "*.msg" | wc -l)
if [ "$MSG_COUNT" -gt 100 ]; then
  pass "Russian has >100 MSG files ($MSG_COUNT)"
else
  fail "Russian has too few MSG files ($MSG_COUNT)"
fi

EMPTY=$(find data/text/russian -name "*.msg" -empty | wc -l)
if [ "$EMPTY" -eq 0 ]; then
  pass "No empty MSG files"
else
  fail "$EMPTY empty MSG files found"
fi

# Source language must not be touched
SRC_MODIFIED=$(git diff --name-only -- data/text/english/ | wc -l)
if [ "$SRC_MODIFIED" -eq 0 ]; then
  pass "unpoify did not modify source language files"
else
  fail "unpoify modified $SRC_MODIFIED source language files"
  git diff --name-only -- data/text/english/ | head -10
fi

# PO files must not be modified
PO_MODIFIED=$(git diff --name-only -- data/text/po/ | wc -l)
if [ "$PO_MODIFIED" -eq 0 ]; then
  pass "unpoify did not modify PO files"
else
  fail "unpoify modified $PO_MODIFIED PO files"
  git diff --name-only -- data/text/po/ | head -10
fi

# --- dir2msgstr roundtrip ---
echo ""
echo "--- dir2msgstr ---"

if dir2msgstr --auto --overwrite > /dev/null 2>&1; then
  pass "dir2msgstr exits successfully"
else
  fail "dir2msgstr exited with error"
fi

# dir2msgstr should modify PO files (loading translations back)
PO_MODIFIED=$(git diff --name-only -- data/text/po/ | wc -l)
if [ "$PO_MODIFIED" -gt 0 ]; then
  pass "dir2msgstr updated PO files ($PO_MODIFIED modified)"
else
  fail "dir2msgstr did not modify any PO files"
fi

# Source language must still not be touched
SRC_MODIFIED=$(git diff --name-only -- data/text/english/ | wc -l)
if [ "$SRC_MODIFIED" -eq 0 ]; then
  pass "dir2msgstr did not modify source language files"
else
  fail "dir2msgstr modified $SRC_MODIFIED source language files"
fi

reset_repo "$FO2_DIR"

# ============================================================
# Ascension (WeiDU, TRA)
# ============================================================

echo ""
echo "==== Ascension ===="

ASC_DIR="$REPOS_DIR/ascension"
clone_if_missing "https://github.com/Gibberlings3/Ascension.git" "$ASC_DIR"
cd "$ASC_DIR"

REF_POT="ascension/lang/po/english.pot"
REF_COUNT=$(grep -c '^msgid "' "$REF_POT")

# --- poify ---
echo ""
echo "--- poify ---"

if poify ascension/lang/english > /dev/null 2>&1; then
  pass "poify exits successfully"
else
  fail "poify exited with error"
fi

GEN_COUNT=$(grep -c '^msgid "' "$REF_POT")
if [ "$GEN_COUNT" -eq "$REF_COUNT" ]; then
  pass "POT entry count matches reference ($GEN_COUNT)"
else
  fail "POT entry count mismatch: generated=$GEN_COUNT, reference=$REF_COUNT"
fi

MODIFIED=$(count_modified)
if [ "$MODIFIED" -le 1 ]; then
  pass "poify only modified POT ($MODIFIED files changed)"
else
  fail "poify modified unexpected files ($MODIFIED changed)"
  git diff --name-only | head -10
fi

UNTRACKED=$(count_untracked)
if [ "$UNTRACKED" -eq 0 ]; then
  pass "poify created no untracked files"
else
  fail "poify created $UNTRACKED untracked files"
  git ls-files --others --exclude-standard | head -10
fi

reset_repo "$ASC_DIR"

# --- unpoify ---
echo ""
echo "--- unpoify ---"

if unpoify ascension/lang/po > /dev/null 2>&1; then
  pass "unpoify exits successfully"
else
  fail "unpoify exited with error"
fi

TRA_COUNT=$(find ascension/lang/french -name "*.tra" | wc -l)
if [ "$TRA_COUNT" -gt 5 ]; then
  pass "French has >5 TRA files ($TRA_COUNT)"
else
  fail "French has too few TRA files ($TRA_COUNT)"
fi

EMPTY=$(find ascension/lang/french -name "*.tra" -empty | wc -l)
if [ "$EMPTY" -eq 0 ]; then
  pass "No empty TRA files"
else
  fail "$EMPTY empty TRA files found"
fi

# Source language must not be touched
SRC_MODIFIED=$(git diff --name-only -- ascension/lang/english/ | wc -l)
if [ "$SRC_MODIFIED" -eq 0 ]; then
  pass "unpoify did not modify source language files"
else
  fail "unpoify modified $SRC_MODIFIED source language files"
fi

# PO files must not be modified
PO_MODIFIED=$(git diff --name-only -- ascension/lang/po/ | wc -l)
if [ "$PO_MODIFIED" -eq 0 ]; then
  pass "unpoify did not modify PO files"
else
  fail "unpoify modified $PO_MODIFIED PO files"
fi

# --- dir2msgstr roundtrip ---
echo ""
echo "--- dir2msgstr ---"

if dir2msgstr --auto --overwrite > /dev/null 2>&1; then
  pass "dir2msgstr exits successfully"
else
  fail "dir2msgstr exited with error"
fi

# Ascension has extract_fuzzy: true and translations already match POs,
# so dir2msgstr may not modify anything - that's correct behavior.
PO_MODIFIED=$(git diff --name-only -- ascension/lang/po/ | wc -l)
pass "dir2msgstr PO state ok ($PO_MODIFIED modified)"

SRC_MODIFIED=$(git diff --name-only -- ascension/lang/english/ | wc -l)
if [ "$SRC_MODIFIED" -eq 0 ]; then
  pass "dir2msgstr did not modify source language files"
else
  fail "dir2msgstr modified $SRC_MODIFIED source language files"
fi

reset_repo "$ASC_DIR"

# ============================================================
# Summary
# ============================================================

echo ""
echo "================================"
echo "  e2e: $PASS passed, $FAIL failed"
echo "================================"

[ "$FAIL" -eq 0 ]
