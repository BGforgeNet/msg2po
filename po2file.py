#!/usr/bin/env python3
# coding: utf-8

import argparse
from bgforge_po import po2file, VALID_EXTENSIONS
from polib import POFile

formats = "/".join(VALID_EXTENSIONS)
parser = argparse.ArgumentParser(
    description="Extract {} from gettext PO".format(formats), formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("INPUT_FILE", help="input PO file")
parser.add_argument("OUTPUT_FILE", help="output translation file")
parser.add_argument("-e", dest="encoding", help="output encoding", default="cp1252")
parser.add_argument("--path", dest="path", help="file occurrence in PO (relative path) - defaults to output name")
args = parser.parse_args()

if args.path is None:
    path = args.OUTPUT_FILE
else:
    path = args.path

po = POFile(args.INPUT_FILE)
po2file(po, args.OUTPUT_FILE, args.encoding, path)
