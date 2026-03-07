#!/usr/bin/env python3

import argparse

from msg2po.core import CONFIG, VALID_EXTENSIONS, file2po

formats = "/".join(VALID_EXTENSIONS)
parser = argparse.ArgumentParser(
    description=f"Load {formats} into gettext PO msgid's",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("INPUT_SOURCE", help="input source file")
parser.add_argument("OUTPUT_PO", help="output PO file")
parser.add_argument("-e", dest="enc", default=f"{CONFIG.encoding}", help="source encoding")
args = parser.parse_args()


def main():
    po = file2po(args.INPUT_SOURCE, args.OUTPUT_PO, args.enc)
    po.save(args.OUTPUT_PO, newline=CONFIG.newline_po)


if __name__ == "__main__":
    main()
