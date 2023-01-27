#!/bin/bash

set -xeu -o pipefail

source "$(dirname "$0")/init.sh"

if [[ "$INPUT_UNPOIFY" == 'true' ]]; then
  echo 'Extracting translations from PO'
  unpoify.py
fi

if [[ "$(git status --porcelain "$tra_dir" | wc -l)" != "0" ]]; then
  echo "unpoify: changes found"

  if [[ "$INPUT_SINGLE_COMMIT" == "true" ]]; then
    echo "single commit enabled, no commit"
  else
    if [[ "$INPUT_UNPOIFY_COMMIT" == "true" ]]; then
      echo "unpoify: committing"
      git add "$tra_dir"
      git commit -m "$commit_message_base unpoify"
    fi
  fi

else
  echo "unpoify: no changes found, pass"
fi
