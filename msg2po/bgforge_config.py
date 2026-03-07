#!/usr/bin/env python3

# This script is needed for shell wrappers to read values from .bgforge.yml.

import sys

import ruamel.yaml

from msg2po.config import CONFIG


def main():
    stanza = sys.argv[1]
    if stanza == "paths-filter":
        paths_filter()
        sys.exit(0)

    key = sys.argv[2]
    try:
        value = CONFIG._config[stanza][key]
        print(value)
    except (KeyError, TypeError):
        print(f"config {stanza}:{key} not found")
        sys.exit(1)


# for github action https://github.com/AurorNZ/paths-filter
def paths_filter():
    yaml = ruamel.yaml.YAML()
    tra_dir = CONFIG.tra_dir
    src_lang = CONFIG.src_lang
    unpoify = [f"{tra_dir}/po/*.po"]
    if CONFIG.extract_format == "sfall":  # fallout
        poify = [
            f"{tra_dir}/{src_lang}/*/*.msg",
            f"{tra_dir}/{src_lang}/*/*.sve",
            f"{tra_dir}/{src_lang}/*/*.txt",
        ]
        dir2msgstr = [
            f"{tra_dir}/*/*/*.msg",
            f"{tra_dir}/*/*/*.sve",
            f"{tra_dir}/*/*/*.txt",
            f"!{tra_dir}/{src_lang}/*/*.msg",
            f"!{tra_dir}/{src_lang}/*/*.sve",
            f"!{tra_dir}/{src_lang}/*/*.txt",
        ]
    else:
        poify = [f"{tra_dir}/{src_lang}/**/*.tra"]
        dir2msgstr = [
            f"{tra_dir}/**/*.tra",
            f"!{tra_dir}/{src_lang}/**/*.tra",
        ]
    paths = {"poify": poify, "unpoify": unpoify, "dir2msgstr": dir2msgstr}
    yaml.dump(paths, sys.stdout)


if __name__ == "__main__":
    main()
