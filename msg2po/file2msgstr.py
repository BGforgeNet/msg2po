#!/usr/bin/env python3

import argparse

from polib import pofile

from msg2po.core import CONFIG, VALID_EXTENSIONS, file2msgstr
from msg2po.log import cli_entry, setup_logging


@cli_entry
def main():
    formats = "/".join(VALID_EXTENSIONS)
    parser = argparse.ArgumentParser(
        description=f"Load {formats} into gettext PO msgstr", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("INPUT_FILE", help="input file")
    parser.add_argument("OUTPUT_FILE", help="output PO file")
    parser.add_argument(
        "--path", dest="path", help="load as filename (PO occurrence). If not specified, defaults to input filename"
    )
    parser.add_argument("-e", dest="encoding", default="cp1252", help="source encoding")
    parser.add_argument("--overwrite", default=False, action="store_true", help="overwrite existing msgstr's")
    parser.add_argument(
        "--same",
        dest="same",
        default=False,
        action="store_true",
        help="load translations that are identical to original strings",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress info messages")
    parser.add_argument("-t", "--timestamps", action="store_true", help="show timestamps in log output")
    args = parser.parse_args()
    setup_logging(verbose=args.verbose, quiet=args.quiet, timestamps=args.timestamps)

    input_file = args.INPUT_FILE
    output_file = args.OUTPUT_FILE
    path = args.path if args.path is not None else args.INPUT_FILE

    po = pofile(output_file)
    po = file2msgstr(input_file, po, path, encoding=args.encoding, overwrite=args.overwrite, same=args.same)
    po.save(output_file, newline=CONFIG.newline_po)


if __name__ == "__main__":
    main()
