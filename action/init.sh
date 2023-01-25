#!/bin/bash

set -xeu -o pipefail

tra_dir="$(bgforge-config.py translation tra_dir)"
src_lang="$(bgforge-config.py translation src_lang)"
export po_dir_path="$tra_dir/po"
export pot_path="$tra_dir/po/$src_lang.pot"

git config user.name "BGforgeNet/msg2po"
git config user.email "hive@bgforge.net"
