#!/usr/bin/env python3
# coding: utf-8

import argparse
from bgforge_po import check_indexed, EPOFile, file2msgstr
import sys

parser = argparse.ArgumentParser(
    description="Load indexed TXT into gettext PO msgstr", formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("INPUT_FILE", help="input TXT/SVE file")
parser.add_argument("OUTPUT_FILE", help="output PO file")
parser.add_argument(
    "--path", dest="path", help="load as filename (PO occurrence). If not specified, defaults to input filename"
)
parser.add_argument("-e", dest="encoding", default="cp1252", help="source encoding")
args = parser.parse_args()

input_file = args.INPUT_FILE
output_file = args.OUTPUT_FILE
if args.path is None:
    path = input_file
else:
    path = args.path
encoding = args.encoding

if not check_indexed(input_file):
    print(("{} is NOT an indexed TXT. Can't process, exiting!".format(input_file)))
    sys.exit(1)

epo = EPOFile(output_file)
epo = file2msgstr(input_file, epo, path, encoding=encoding)
epo.save(output_file)
