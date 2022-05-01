#!/bin/bash

set -xeu -o pipefail

tra_dir="$(bgforge-config.py translation tra_dir)"
src_lang="$(bgforge-config.py translation src_lang)"
po_dir_path="$tra_dir/po"
pot_path="$tra_dir/po/$src_lang.pot"

commit_name="BGforge GHA"
git config user.name "BGforge/msg2po action"
git config user.email "weblate@bgforge.net"
