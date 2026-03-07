#!/usr/bin/env python3

import argparse
import os

import ruamel.yaml
from polib import pofile

from msg2po.core import CONFIG
from msg2po.log import cli_entry, setup_logging


def load_replacements():
    if os.path.isfile("unfuzzy.yml"):
        yml = "unfuzzy.yml"
    else:
        yml = os.path.join(os.path.dirname(os.path.realpath(__file__)), "unfuzzy.yml")
    with open(yml, encoding="utf-8") as yf:
        yaml = ruamel.yaml.YAML()
        replace_list = yaml.load(yf)
    return replace_list


def make_replaces(line, replace_list):
    for r in replace_list:
        line = line.replace(r[0], r[1])
    return line


def msgids_equal(id1, id2, replace_list):
    id1 = make_replaces(id1, replace_list)
    id2 = make_replaces(id2, replace_list)
    return id1 == id2


@cli_entry
def main():
    parser = argparse.ArgumentParser(
        description="Unmark PO entries as fuzzy, "
        "if replacing string1 with string2 in previous msgid results in current msgid",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("INPUT_FILE", help="input PO file")
    parser.add_argument("-w", default=False, dest="WRITE", action="store_true", help="save PO file?")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress info messages")
    parser.add_argument("-t", "--timestamps", action="store_true", help="show timestamps in log output")
    args = parser.parse_args()
    setup_logging(verbose=args.verbose, quiet=args.quiet, timestamps=args.timestamps)

    input_file = args.INPUT_FILE
    write = args.WRITE
    po = pofile(input_file)

    i = 0
    replace_list = load_replacements()
    for e in po.fuzzy_entries():
        if e.previous_msgid:  # some fuzzies are assigned automatically on merge and don't have previous msgids
            e1 = e.msgid
            e2 = e.previous_msgid
            if msgids_equal(e1, e2, replace_list):
                if write:
                    e.flags.remove("fuzzy")
                    e.previous_msgid = None
                    e.previous_msgid_plural = None
                    e.previous_msgctxt = None
                else:  # preview
                    i = i + 1
                    print(f"OLD SOURCE:  {e1}")
                    print(f"NEW SOURCE:  {e2}")
                    print(f"TRANSLATION: {e.msgstr}")
                    print("")

    if write:
        po.save(input_file, newline=CONFIG.newline_po)
    else:
        print(i)


if __name__ == "__main__":
    main()
