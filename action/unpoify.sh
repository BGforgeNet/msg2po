#!/bin/bash

set -xeu -o pipefail

source "$(dirname "$0")/init.sh"

if [[ "$INPUT_UNPOIFY" == 'true' ]]; then
  echo 'Extracting translations from PO'
  unpoify.py
fi
if [[ "$(git status --porcelain $tra_dir | wc -l)" != "0" ]]; then
  echo "unpoify: changes found, committing"
  git add "$tra_dir"
  git commit -m "unpoify"
else
  echo "unpoify: no changes found, pass"
fi
