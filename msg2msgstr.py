#!/usr/bin/env python3
# coding: utf-8


import argparse
from bgforge_po import EPOFile, file2msgstr

parser = argparse.ArgumentParser(
    description="Load Fallout MSG into gettext PO msgstr", formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("INPUT_FILE", help="input MSG file")
parser.add_argument("OUTPUT_FILE", help="output PO file")
parser.add_argument(
    "--path", dest="path", help="load as filename (PO occurrence). If not specified, defaults to input filename"
)
parser.add_argument("-e", dest="encoding", default="cp1252", help="source encoding")
args = parser.parse_args()

input_file = args.INPUT_FILE
output_file = args.OUTPUT_FILE
if args.path is None:
    path = args.INPUT_FILE
else:
    path = args.path
encoding = args.encoding

epo = EPOFile(output_file)
epo = file2msgstr(input_file, epo, path, encoding=encoding)
epo.save(output_file)
