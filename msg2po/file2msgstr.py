#!/usr/bin/env python3
# coding: utf-8

import argparse
from msg2po.core import file2msgstr, CONFIG, VALID_EXTENSIONS
from polib import pofile

formats = "/".join(VALID_EXTENSIONS)
parser = argparse.ArgumentParser(
    description="Load {} into gettext PO msgstr".format(formats), formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("INPUT_FILE", help="input file")
parser.add_argument("OUTPUT_FILE", help="output PO file")
parser.add_argument(
    "--path", dest="path", help="load as filename (PO occurrence). If not specified, defaults to input filename"
)
parser.add_argument("-e", dest="encoding", default="cp1252", help="source encoding")
parser.add_argument(
    "overwrite", dest="overwrite", default=False, action="store_true", help="overwrite existing msgstr's"
)
parser.add_argument(
    "--same",
    dest="same",
    default=False,
    action="store_true",
    help="load translations that are identical to original strings",
)
args = parser.parse_args()

input_file = args.INPUT_FILE
output_file = args.OUTPUT_FILE
if args.path is None:
    path = args.INPUT_FILE
else:
    path = args.path


def main():
    po = pofile(output_file)
    po = file2msgstr(input_file, po, path, encoding=args.encoding, overwrite=args.overwrite, same=args.same)
    po.save(output_file, newline=CONFIG.newline_po)


if __name__ == "__main__":
    main()
