#!/usr/bin/env python3

import argparse
import polib

parser = argparse.ArgumentParser(
    description="Unfuzzy Cassidy lines which were fuzzied by adding sounds",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("INPUT_FILE", help="input PO file")
parser.add_argument("-w", default=False, dest="WRITE", action="store_true", help="save PO file?")
args = parser.parse_args()

input_file = args.INPUT_FILE
write = args.WRITE
po = polib.pofile(input_file)

i = 0
for e in po.fuzzy_entries():
    if e.previous_msgid:  # some fuzzies are assigned automatically on merge and don't have previous msgids
        ctxt = e.msgctxt
        if ctxt and ctxt.startswith("Cas") and (e.msgid != e.msgstr):
            if write:
                e.flags.remove("fuzzy")
                e.previous_msgid = None
                e.previous_msgid_plural = None
                e.previous_msgctxt = None
            else:  # preview
                i = i + 1
                print(e.msgctxt)
                print(e.msgid)
                print(e.msgstr)

if write:
    po.save(input_file)
else:
    print(i)
