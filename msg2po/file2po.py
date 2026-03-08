#!/usr/bin/env python3
# Single-file conversion: game translation file -> PO entries.

import argparse

from msg2po.config import CONFIG
from msg2po.conversion import file2po
from msg2po.formats import VALID_EXTENSIONS
from msg2po.log import cli_entry, setup_logging


@cli_entry
def main():
    formats = "/".join(VALID_EXTENSIONS)
    parser = argparse.ArgumentParser(
        description=f"Load {formats} into gettext PO msgid's",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("INPUT_SOURCE", help="input source file")
    parser.add_argument("OUTPUT_PO", help="output PO file")
    parser.add_argument("-e", dest="enc", default=f"{CONFIG.encoding}", help="source encoding")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress info messages")
    parser.add_argument("-t", "--timestamps", action="store_true", help="show timestamps in log output")
    args = parser.parse_args()
    setup_logging(verbose=args.verbose, quiet=args.quiet, timestamps=args.timestamps)

    po = file2po(args.INPUT_SOURCE, args.OUTPUT_PO, args.enc)
    po.save(args.OUTPUT_PO, newline=CONFIG.newline_po)


if __name__ == "__main__":
    main()
