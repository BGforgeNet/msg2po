#!/bin/bash

set -xeu -o pipefail

# shellcheck source=/dev/null  # for some reason source=init.sh doesn't work
source "$(dirname "$0")/init.sh"

if [[ "$INPUT_SINGLE_COMMIT" == "true" ]]; then
    if [[ "$(git status --porcelain | wc -l)" == "0" ]]; then
        echo "single commit: no changes found"
    else
        echo "single commit: changes found"
        git add .
        # shellcheck disable=SC2154  # from init.sh
        git commit -m "$commit_message_base full chain"
    fi
fi

if [[ "$INPUT_PUSH" == "true" ]]; then
    if git status --porcelain --branch | grep ahead; then
        echo "Pushing changes"
        git push
    else
        echo "Nothing to push"
    fi
fi
