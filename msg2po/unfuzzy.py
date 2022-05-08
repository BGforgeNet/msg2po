#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from polib import pofile
import ruamel.yaml
import os
from msg2po.core import CONFIG

parser = argparse.ArgumentParser(
    description="Unmark PO entries as fuzzy,"
    "if replacing string 1 with string2 in previous msgid results in current msgid",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("INPUT_FILE", help="input PO file")
parser.add_argument("-w", default=False, dest="WRITE", action="store_true", help="save PO file?")
args = parser.parse_args()

yml = os.path.join(os.path.dirname(os.path.realpath(__file__)), "unfuzzy.yml")

input_file = args.INPUT_FILE
write = args.WRITE
po = pofile(input_file)

with open(yml) as yf:
    yaml = ruamel.yaml.YAML()
    replace_list = yaml.load(yf)


def make_replaces(line, replace_list):
    for r in replace_list:
        line = line.replace(r[0], r[1])
    return line


def msgids_equal(id1, id2):
    id1 = make_replaces(id1, replace_list)
    id2 = make_replaces(id2, replace_list)
    if id1 == id2:
        return True
    else:
        return False


def main():
    i = 0
    for e in po.fuzzy_entries():
        if e.previous_msgid:  # some fuzzies are assigned automatically on merge and don't have previous msgids
            e1 = e.msgid
            e2 = e.previous_msgid
            if msgids_equal(e1, e2):
                if write:
                    e.flags.remove("fuzzy")
                    e.previous_msgid = None
                    e.previous_msgid_plural = None
                    e.previous_msgctxt = None
                else:  # preview
                    i = i + 1
                    print(e1)
                    print(e2)

    if write:
        po.save(input_file, newline=CONFIG.newline_po)
    else:
        print(i)


if __name__ == "__main__":
    main()
