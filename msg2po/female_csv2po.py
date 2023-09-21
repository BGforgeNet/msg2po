#!/usr/bin/env python3
# coding: utf-8

import argparse
from msg2po.core import CONFIG, sort_po, unfuzzy_exact_matches
import csv
from collections import OrderedDict
import polib

parser = argparse.ArgumentParser(
    description="Load female csv into Gettext PO", formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("INPUT_CSV", help="input CSV file")
parser.add_argument("OUTPUT_PO", help="output PO file")
args = parser.parse_args()


def load_csv(path):
    female_strings = OrderedDict()
    with open(path, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            female_strings[row[0]] = row[1]
    sorted_strings = OrderedDict(sorted(female_strings.items()))
    return sorted_strings


def main():
    female_strings = load_csv(args.INPUT_CSV)

    po = polib.pofile(args.OUTPUT_PO)
    for fs in female_strings:
        entry = polib.POEntry(msgid=fs, msgstr=female_strings[fs], msgctxt="female")
        po.append(entry)
    po = sort_po(po)
    po = unfuzzy_exact_matches(po)
    po.save(args.OUTPUT_PO, newline=CONFIG.newline_po)


if __name__ == "__main__":
    main()
