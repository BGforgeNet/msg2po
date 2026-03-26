#!/bin/bash

set -xeu -o pipefail

# Activate uv-managed venv so direct script calls (poify.py, etc.) can import dependencies.
# shellcheck source=/dev/null
source "$GITHUB_ACTION_PATH/.venv/bin/activate"

tra_dir="$(bgforge_config.py translation tra_dir)"
src_lang="$(bgforge_config.py translation src_lang)"
export po_dir_path="$tra_dir/po"
export pot_path="$tra_dir/po/$src_lang.pot"

git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
git config core.autocrlf false

export commit_message_base="BGforgeNet/msg2po:"
