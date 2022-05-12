#!/usr/bin/env python3
# coding: utf-8
"""
Update POs from POT. Behaves like
msgmerge -v --previous --no-wrap -U -N --backup=off lang1.po lang0.pot
Except that it allows string with "female" context to remain in PO,
if there's a corresponding male entry without such context.
"""

from functools import partial
import os
import argparse
import subprocess
import sys
from multiprocessing import Pool
from msg2po.core import sort_po, update_female_entries, CONFIG, find_files, unfuzzy_exact_matches
from polib import pofile

# parse args
parser = argparse.ArgumentParser(
    description="Update POs from POT, keeping female entries. Requires Gettext msgmerge in PATH",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)

parser.add_argument("PO", help="PO file", nargs="?", default=None)
parser.add_argument("POT", help="POT file", nargs="?", default=None)
args = parser.parse_args()


def merge(po_path: str, pot_path: str):
    print(po_path)
    exit_code = 0
    cmd = ["msgmerge", "--previous", "--no-wrap", "-U", "-q", "--backup=off", po_path, pot_path]
    res = subprocess.run(
        cmd,
        capture_output=True,
        check=True,
        text=True,
    )
    print(res.stdout)
    print(res.stderr)
    if res.returncode != 0:
        exit_code = res.returncode
        print("ERROR: msgmerge failed for {}".format(po_path))
    po2 = pofile(po_path)
    po2 = update_female_entries(po2)
    po2 = sort_po(po2)
    po2 = unfuzzy_exact_matches(po2)
    po2.save(fpath=po_path, newline=CONFIG.newline_po)
    return exit_code


def main():
    # single file
    if (args.PO is not None) and (args.POT is not None):
        res = merge(args.PO, args.POT)
        if res != 0:
            print("ERROR: msgmerge failed for {}".format(args.PO))
            sys.exit(1)
        sys.exit(0)

    # multifile, read .bgforge.yml
    po_dir = CONFIG.po_dir
    po_files = find_files(po_dir, "po")
    pot_file = os.path.join(po_dir, CONFIG.src_lang + ".pot")

    print("Merging PO files in {} with {}".format(po_dir, pot_file))
    pool = Pool()
    try:
        r = pool.map_async(partial(merge, pot_path=pot_file), po_files)
        pool.close()
        codes = r.get()
    except KeyboardInterrupt:
        pool.terminate()
    finally:
        pool.join()

    for c in codes:
        if c != 0:
            print("ERROR: one of msgmerge invocations failed.")
            sys.exit(1)


if __name__ == "__main__":
    main()
