#!/usr/bin/env python3

import argparse
import os
import sys

from loguru import logger

from msg2po.log import cli_entry, setup_logging

# po: new translations added through weblate use case sensitive code: pt_BR.po. Keeping them.
EXCLUDE_FILES = ["README.md"]
EXCLUDE_DIRS = [".git", ".svn", ".hg", ".github"]


# https://stackoverflow.com/questions/3075443/python-recursively-remove-capitalisation-from-directory-structure
def lowercase_rename(dir):
    def rename_all(root, items):
        for name in items:
            new_name = name.lower()
            if name == new_name:
                continue
            if (name in EXCLUDE_FILES) or name.endswith(".po"):
                logger.debug(f"{name}: reserved name, skip")
                continue
            path = os.path.join(root, name)
            new_path = os.path.join(root, new_name)

            full_path = os.path.normpath(path)
            split_path = full_path.split(os.sep)
            if len(set(EXCLUDE_DIRS) & set(split_path)) > 0:
                logger.debug(f"{path}: reserved dir name in path, skip")
                continue

            logger.info(f"renaming {path} to {new_path}")
            os.rename(path, new_path)

    # starts from the bottom so paths further up remain valid after renaming
    for root, dirs, files in os.walk(dir, topdown=False):
        rename_all(root, dirs)
        rename_all(root, files)


@cli_entry
def main():
    parser = argparse.ArgumentParser(
        description="Lowercase files in selected directory", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("dir")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress info messages")
    parser.add_argument("-t", "--timestamps", action="store_true", help="show timestamps in log output")
    args = parser.parse_args()
    setup_logging(verbose=args.verbose, quiet=args.quiet, timestamps=args.timestamps)

    if not os.path.isdir(args.dir):
        logger.error(f"{args.dir} is not a directory")
        sys.exit(1)
    lowercase_rename(args.dir)


if __name__ == "__main__":
    main()
