#!/bin/bash

set -xeu -o pipefail

source "$(dirname "$0")/init.sh"

if [[ "$INPUT_DIR2MSGSTR" == 'true' ]]; then
  echo "Loading updated translations"
  dir2msgstr.py --auto --overwrite
fi

if [[ "$(git status --porcelain "$tra_dir" | wc -l)" != "0" ]]; then
  echo "dir2msgstr: changes found, could be from unpoify"

  if [[ "$INPUT_SINGLE_COMMIT" == "true" ]]; then
    echo "single commit enabled, no commit, but we perform unpoify again"
    unpoify.py
  else
    if [[ "$INPUT_DIR2MSGSTR_COMMIT" == "true" ]]; then
      echo "dir2msgstr: committing"
      git add "$tra_dir"
      git commit -m "$commit_message_base load external translations"
    fi
  fi

else
  echo "dir2msgstr: no changes found, pass"
fi
