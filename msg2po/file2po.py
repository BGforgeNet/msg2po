#!/usr/bin/env python3
# coding: utf-8

import argparse
from msg2po.core import file2po, CONFIG, VALID_EXTENSIONS

formats = "/".join(VALID_EXTENSIONS)
parser = argparse.ArgumentParser(
    description="Load {} into gettext PO msgid's".format(formats),
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("INPUT_SOURCE", help="input source file")
parser.add_argument("OUTPUT_PO", help="output PO file")
parser.add_argument("-e", dest="enc", default="{}".format(CONFIG.encoding), help="source encoding")
args = parser.parse_args()


def main():
    po = file2po(args.INPUT_SOURCE, args.OUTPUT_PO, args.enc)
    po.save(args.OUTPUT_PO, newline=CONFIG.newline_po)


if __name__ == "__main__":
    main()
