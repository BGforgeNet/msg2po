#!/bin/bash

set -xeu -o pipefail

# shellcheck source=/dev/null  # for some reason source=init.sh doesn't work
source "$(dirname "$0")/init.sh"
# shellcheck source=/dev/null  # Nothing interesting here
source "$VIRTUALENV_PATH/bin/activate" >/dev/null 2>&1 || true


if [[ "$INPUT_POIFY" == 'true' ]]; then
    echo 'Updating POT'
    poify.py
    # shellcheck disable=SC2154  # from init.sh
    if [[ "$(git status --porcelain "$pot_path" | wc -l)" != "0" ]]; then
        echo 'Updating POs from pot'
        msgmerge.py
    fi
fi

# shellcheck disable=SC2154  # from init.sh
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
