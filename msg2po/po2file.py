#!/usr/bin/env python3
# Single-file conversion: PO entries -> game translation file.

import argparse

from polib import pofile

from msg2po.conversion import po2file
from msg2po.formats import VALID_EXTENSIONS
from msg2po.log import cli_entry, setup_logging


@cli_entry
def main():
    formats = "/".join(VALID_EXTENSIONS)
    parser = argparse.ArgumentParser(
        description=f"Extract {formats} from gettext PO", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("INPUT_FILE", help="input PO file")
    parser.add_argument("OUTPUT_FILE", help="output translation file")
    parser.add_argument("-e", dest="encoding", help="output encoding", default="cp1252")
    parser.add_argument("--path", dest="path", help="file occurrence in PO (relative path) - defaults to output name")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress info messages")
    parser.add_argument("-t", "--timestamps", action="store_true", help="show timestamps in log output")
    args = parser.parse_args()
    setup_logging(verbose=args.verbose, quiet=args.quiet, timestamps=args.timestamps)

    path = args.path if args.path is not None else args.OUTPUT_FILE

    po = pofile(args.INPUT_FILE)
    po2file(po, args.OUTPUT_FILE, args.encoding, path)


if __name__ == "__main__":
    main()
