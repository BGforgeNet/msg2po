#!/bin/bash

set -xeu -o pipefail

source "$(dirname "$0")/init.sh"

if [[ "$INPUT_POIFY" == 'true' ]]; then
  echo 'Updating POT'
  poify.py
  if [[ "$(git status --porcelain "$pot_path" | wc -l)" != "0" ]]; then
    echo 'Updating POs from pot'
    msgmerge.py
  fi
fi

if [[ "$(git status --porcelain "$po_dir_path" | wc -l)" != "0" ]]; then
  echo "poify: changes found"

  if [[ "$INPUT_SINGLE_COMMIT" == "true" ]]; then
    echo "single commit enabled, no commit"
  else
    if [[ "$INPUT_POIFY_COMMIT" == "true" ]]; then
      echo "poify: committing"
      git add "$po_dir_path"
      git commit -m "$commit_message_base poify and merge"
    fi
  fi

  if [[ "$INPUT_POIFY_TRIGGER_UNPOIFY" == 'true' ]]; then
    echo 'Instant unpoify'
    INPUT_UNPOIFY="true" "$(dirname "$0")"/unpoify.sh
  fi

else
  echo "poify: no changes found, pass"
fi
