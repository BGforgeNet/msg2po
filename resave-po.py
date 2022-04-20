#!/usr/bin/env python3
# coding: utf-8

import argparse
import polib

from bgforge_po import sort_po, restore_female_entries

parser = argparse.ArgumentParser(
    description="Resave PO file using polib API, to correct formatting",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("INPUT_FILE", help="PO file to resave")
args = parser.parse_args()

po = polib.pofile(args.INPUT_FILE)

po = restore_female_entries(po)
po2 = sort_po(po)

po2.save(args.INPUT_FILE)
