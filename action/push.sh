#!/bin/bash

set -xeu -o pipefail

source "$(dirname "$0")/init.sh"

if [[ "$INPUT_PUSH" == 'true' ]]; then
  if git status --porcelain --branch | grep ahead; then
    echo "Pushing changes"
    git push
  else
    echo "Nothing to push"
  fi
fi
