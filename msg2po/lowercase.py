#!/usr/bin/env python3
import os
import argparse
import sys

# po: new translations added through weblate use case sensitive code: pt_BR.po. Keeping them.
EXCLUDE_FILES = ["README.md"]
EXCLUDE_DIRS = [".git", ".svn", ".hg", ".github"]

# parse args
parser = argparse.ArgumentParser(
    description="Lowercase files in selected directory", formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("dir")
args = parser.parse_args()


# https://stackoverflow.com/questions/3075443/python-recursively-remove-capitalisation-from-directory-structure
def lowercase_rename(dir):
    def rename_all(root, items):
        for name in items:
            new_name = name.lower()
            if name == new_name:
                continue
            if (name in EXCLUDE_FILES) or name.endswith(".po"):
                print("{}: reserved name, skip".format(name))
                continue
            path = os.path.join(root, name)
            new_path = os.path.join(root, new_name)

            full_path = os.path.normpath(path)
            split_path = full_path.split(os.sep)
            if len((set(EXCLUDE_DIRS) & set(split_path))) > 0:
                print("{}: reserved dir name in path, skip".format(path))
                continue

            print("renaming {} to {}".format(path, new_path))
            os.rename(path, new_path)

    # starts from the bottom so paths further up remain valid after renaming
    for root, dirs, files in os.walk(dir, topdown=False):
        rename_all(root, dirs)
        rename_all(root, files)


def main():
    if not os.path.isdir(args.dir):
        print("Error: {} is not a directory".format(args.dir))
        sys.exit(1)
    lowercase_rename(args.dir)


if __name__ == "__main__":
    main()
