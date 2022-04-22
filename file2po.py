#!/usr/bin/env python3
# coding: utf-8

import argparse
from bgforge_po import file2po, CONFIG, VALID_EXTENSIONS

formats = "/".join(VALID_EXTENSIONS)
parser = argparse.ArgumentParser(
    description="Convert {} to gettext PO".format(formats), formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("INPUT_FILE", help="input MSG file")
parser.add_argument("OUTPUT_FILE", help="output PO file")
parser.add_argument("-e", dest="enc", default="cp1252", help="source encoding")
parser.add_argument("--no-empty", dest="noempty", action="store_true", default=False, help="skip empty lines")
args = parser.parse_args()

po = file2po(args.INPUT_FILE, args.enc, args.noempty)
po.save(args.OUTPUT_FILE, newline=CONFIG.newline)
