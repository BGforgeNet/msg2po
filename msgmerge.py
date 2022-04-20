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
from bgforge_po import get_src_lang, get_ext, get_po_dir, sort_po, threads_number, restore_female_entries
import polib

# parse args
parser = argparse.ArgumentParser(
    description="Update POs from POT, keeping female entries",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
# parser.add_argument("DIR", nargs="?", default=default_po_dir, help="directory with PO files")
parser.add_argument("PO", help="PO file", nargs="?", default=None)
parser.add_argument("POT", help="POT file", nargs="?", default=None)
args = parser.parse_args()


def merge(po: str, pot: str):
    print(po)
    cmd = ["msgmerge", "--previous", "--no-wrap", "-U", "-q", "--backup=off", po, pot]
    res = subprocess.run(
        cmd,
        capture_output=True,
        check=True,
        text=True,
    )
    print(res.stdout)
    print(res.stderr)
    po2 = polib.pofile(po)
    po2 = restore_female_entries(po2)
    po2 = sort_po(po2)
    po2.save(po)


def find_files(dir: str, ext: str):
    files = []
    for root, subdir_list, file_list in os.walk(dir):
        for f in file_list:
            if get_ext(f) == ext:
                files.append((os.path.join(root, f)))
    return files


# single file
if (args.PO is not None) and (args.POT is not None):
    po = merge(args.PO, args.POT)
    sys.exit(0)

# multifile, read .bgforge.yml
po_dir = get_po_dir()
po_files = find_files(po_dir, "po")
pot_file = os.path.join(po_dir, get_src_lang() + ".pot")

# extract PO files
threads = threads_number(max=True)
print("Merging PO files in {} with {}, using {} threads".format(po_dir, pot_file, threads))
pool = Pool(threads)
try:
    N = pool.map_async(partial(merge, pot=pot_file), po_files)
    pool.close()
except KeyboardInterrupt:
    pool.terminate()
finally:
    pool.join()
