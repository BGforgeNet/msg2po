#!/usr/bin/env python3
# coding: utf-8

import argparse
import bgforge_po

parser = argparse.ArgumentParser(
    description="Convert Fallout MSG to gettext PO", formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("INPUT_FILE", help="input MSG file")
parser.add_argument("OUTPUT_FILE", help="output PO file")
parser.add_argument("-e", dest="enc", default="cp1252", help="source encoding")
parser.add_argument("--no-empty", dest="noempty", action="store_true", default=False, help="skip empty lines")
args = parser.parse_args()

po = bgforge_po.file2po(args.INPUT_FILE, args.enc, args.noempty)
po.save(args.OUTPUT_FILE)
