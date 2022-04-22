#!/usr/bin/env python3
# coding: utf-8

import argparse
from bgforge_po import file2msgstr, CONFIG, VALID_EXTENSIONS
from polib import pofile

formats = "/".join(VALID_EXTENSIONS)
parser = argparse.ArgumentParser(
    description="Load {}into gettext PO msgstr".format(formats), formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("INPUT_FILE", help="input file")
parser.add_argument("OUTPUT_FILE", help="output PO file")
parser.add_argument(
    "--path", dest="path", help="load as filename (PO occurrence). If not specified, defaults to input filename"
)
parser.add_argument("-e", dest="encoding", default="cp1252", help="source encoding")
parser.add_argument("--no-overwrite", dest="no_overwrite", action="store_true", help="don't overwrite existing msgstrs")
args = parser.parse_args()

input_file = args.INPUT_FILE
output_file = args.OUTPUT_FILE
if args.path is None:
    path = args.INPUT_FILE
else:
    path = args.path
encoding = args.encoding
overwrite = True
if args.no_overwrite:
    overwrite = False

po = pofile(output_file)
po = file2msgstr(input_file, po, path, encoding=encoding, overwrite=overwrite)
po.save(output_file, newline=CONFIG.newline)
