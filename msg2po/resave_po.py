#!/usr/bin/env python3

import argparse

from polib import pofile

from msg2po.config import CONFIG
from msg2po.log import cli_entry, setup_logging
from msg2po.po_utils import normalize_po


@cli_entry
def main():
    parser = argparse.ArgumentParser(
        description="Resave PO file using polib API, to correct formatting",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("INPUT_FILE", help="PO file to resave")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress info messages")
    parser.add_argument("-t", "--timestamps", action="store_true", help="show timestamps in log output")
    args = parser.parse_args()
    setup_logging(verbose=args.verbose, quiet=args.quiet, timestamps=args.timestamps)

    po = pofile(args.INPUT_FILE)
    po = normalize_po(po)
    po.save(args.INPUT_FILE, newline=CONFIG.newline_po)


if __name__ == "__main__":
    main()
