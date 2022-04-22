#!/bin/bash

set -xeu -o pipefail

tra_dir="$(bgforge-config.py translation tra_dir)"
src_lang="$(bgforge-config.py translation src_lang)"
pot_path="$tra_dir/po/$src_lang.pot"


if [[ "$INPUT_POIFY" == 'true' ]]; then
  echo 'updating POT'
  poify.py
fi
if [[ "$INPUT_MSGMERGE" == 'true' ]]; then
  echo 'updating PO files from POT'
  msgmerge.py
fi
if [[ "$INPUT_UNPOIFY" == 'true' ]]; then
  echo 'extracting translations from PO'
  unpoify.py
fi
if [[ "$INPUT_COMMIT" != 'true' ]]; then
  echo "commit disabled, pass"
  exit 0
fi

git config user.name "BGforge Weblate GHA"
git config user.email "weblate@bgforge.net"

if [[ "$INPUT_SEPARATE_COMMITS" != 'true' ]]; then # combined
  if [[ "$(git status --porcelain $tra_dir | wc -l)" != "0" ]]; then
    echo "poify/unpoify: changes found, committing"
    git add "$tra_dir"
    git commit -m "BGforge GHA: poify/unpoify"
  fi
else
  if [[ "$(git status --porcelain $pot_path | wc -l)" != "0" ]]; then  # poify
    echo "poify: changes found, committing"
    git add "$pot_path"
    git commit -m "BGforge GHA: poify"
  else
    echo "poify: no changes found, pass"
  fi
  if [[ "$(git status --porcelain $tra_dir | wc -l)" != "0" ]]; then # unpoify
    echo "unpoify: changes found, committing"
    git add "$tra_dir"
    git commit -m "BGforge GHA: unpoify"
  else
    echo "unpoify: no changes found, pass"
  fi
fi

if git status --porcelain --branch | grep ahead; then
  git push
fi
