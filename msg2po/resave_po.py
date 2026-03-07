#!/usr/bin/env python3

import argparse

from polib import pofile

from msg2po.config import CONFIG
from msg2po.po_utils import normalize_po


def main():
    parser = argparse.ArgumentParser(
        description="Resave PO file using polib API, to correct formatting",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("INPUT_FILE", help="PO file to resave")
    args = parser.parse_args()

    po = pofile(args.INPUT_FILE)
    po = normalize_po(po)
    po.save(args.INPUT_FILE, newline=CONFIG.newline_po)


if __name__ == "__main__":
    main()
