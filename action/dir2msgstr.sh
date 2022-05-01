#!/bin/bash

set -xeu -o pipefail

source "$(dirname "$0")/init.sh"

if [[ "$INPUT_DIR2MSGSTR" == 'true' ]]; then
  echo "Loading updated translations"
  dir2msgstr.py --auto --overwrite
fi
if [[ "$(git status --porcelain $tra_dir | wc -l)" != "0" ]]; then
  echo "dir2msgstr: changes found, committing"
  git add "$tra_dir"
  git commit -m "$commit_name: load external translations"
else
  echo "dir2msgstr: no changes found, pass"
fi
