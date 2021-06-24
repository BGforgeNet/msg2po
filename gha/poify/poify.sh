#!/bin/bash

set -xeu -o pipefail


# action_root="$(realpath ../../)"
# pip3 install -r "$action_root/requirements.txt"
# export PATH="$PATH:$action_root"
# echo $PATH
ls -la
pwd

git status

tra_dir="$(bgforge-config.py tra_dir)"
src_lang="$(bgforge-config.py src_lang)"

pot_path="$tra_dir/po/$src_lang.pot"
poify
git status
git diff

if [[ "$(git status --porcelain '$pot_path' | wc -l)" != "0" ]]; then
  echo "poify: changes found, updating POT"
  git config user.name "BGforge GHA poify"
  git config user.email "poify@bgforge.net"
  git add "$pot_path"
  git commit -m "bgforge gha: poify"
  origin="https://${GITHUB_ACTION}:${GITHUB_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
  echo "Pushing to repo..."
  git fetch $origin ${GITHUB_HEAD_REF}
  git merge FETCH_HEAD -m "Merging in remote"
  git push $origin HEAD:${GITHUB_HEAD_REF}
else
  echo "poify: no changes found, pass"
fi
