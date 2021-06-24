#!/bin/bash

set -xeu -o pipefail

tra_dir="$(bgforge-config.py tra_dir)"
src_lang="$(bgforge-config.py src_lang)"

pot_path="$tra_dir/po/$src_lang.pot"
poify

if [[ "$(git status --porcelain $pot_path | wc -l)" != "0" ]]; then
  echo "poify: changes found, updating POT"
  git config user.name "BGforge GHA poify"
  git config user.email "poify@bgforge.net"
  git add "$pot_path"
  git commit -m "bgforge gha: poify"
  git push
else
  echo "poify: no changes found, pass"
fi
