#!/bin/bash

set -xeu -o pipefail

tra_dir="$(bgforge-config.py tra_dir)"

unpoify

if [[ "$(git status --porcelain $tra_dir | wc -l)" != "0" ]]; then
  echo "unpoify: changes found, extracting translations"
  git config user.name "BGforge GHA unpoify"
  git config user.email "unpoify@bgforge.net"
  git add "$tra_dir"
  git commit -m "bgforge gha: unpoify"
  git push
else
  echo "unpoify: no changes found, pass"
fi
