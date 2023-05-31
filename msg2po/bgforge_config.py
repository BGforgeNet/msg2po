#!/usr/bin/env python3
# coding: utf-8

# this script is needed for shell wrappers

import sys
from msg2po.config import CONFIG
import ruamel.yaml

stanza = sys.argv[1]
if stanza != "paths-filter":
    key = sys.argv[2]


def main():
    if stanza == "paths-filter":
        paths_filter()
        sys.exit(0)
    try:
        value = CONFIG._config[stanza][key]
        print(value)
    except:
        print("config {}:{} not found".format(stanza, key))
        sys.exit(1)


# for github action https://github.com/AurorNZ/paths-filter
def paths_filter():
    yaml = ruamel.yaml.YAML()
    tra_dir = CONFIG.tra_dir
    src_lang = CONFIG.src_lang
    unpoify = ["{}/po/*.po".format(tra_dir)]
    if CONFIG.extract_format == "sfall":  # fallout
        poify = [
            "{}/{}/*/*.msg".format(tra_dir, src_lang),
            "{}/{}/*/*.sve".format(tra_dir, src_lang),
            "{}/{}/*/*.txt".format(tra_dir, src_lang),
        ]
        dir2msgstr = [
            "{}/*/*/*.msg".format(tra_dir),
            "{}/*/*/*.sve".format(tra_dir),
            "{}/*/*/*.txt".format(tra_dir),
            "!{}/{}/*/*.msg".format(tra_dir, src_lang),
            "!{}/{}/*/*.sve".format(tra_dir, src_lang),
            "!{}/{}/*/*.txt".format(tra_dir, src_lang),
        ]
    else:
        poify = ["{}/{}/**/*.tra".format(tra_dir, src_lang)]
        dir2msgstr = [
            "{}/**/*.tra".format(tra_dir),
            "!{}/{}/**/*.tra".format(tra_dir, src_lang),
        ]
    paths = {"poify": poify, "unpoify": unpoify, "dir2msgstr": dir2msgstr}
    yaml.dump(paths, sys.stdout)


if __name__ == "__main__":
    main()
