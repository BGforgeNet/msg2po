#!/usr/bin/env python3

import argparse

from polib import pofile

from msg2po.core import CONFIG, po_make_unique, sort_po, unfuzzy_exact_matches, update_female_entries


def main():
    parser = argparse.ArgumentParser(
        description="Resave PO file using polib API, to correct formatting",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("INPUT_FILE", help="PO file to resave")
    args = parser.parse_args()

    po = pofile(args.INPUT_FILE)
    po = update_female_entries(po)
    po = po_make_unique(po)
    po = unfuzzy_exact_matches(po)
    po = sort_po(po)
    po.save(args.INPUT_FILE, newline=CONFIG.newline_po)


if __name__ == "__main__":
    main()
