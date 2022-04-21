#!/usr/bin/env python3
# coding: utf-8

import os
import argparse
import sys
from multiprocessing import Pool as ThreadPool
from bgforge_po import (
    CONFIG,
    dir_or_exit,
    cd,
    EPOFile,
    get_po_occurrence_map,
    simple_lang_slug,
    get_enc,
    po2file,
    get_ext,
    threads_number,
)

# parse args
parser = argparse.ArgumentParser(
    description="Unpoify files into parent directory of selected PO dir",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("DIR", nargs="?", default=CONFIG.po_dir, help="directory with PO files")
args = parser.parse_args()

# init vars
po_dir = args.DIR
dir_or_exit(po_dir)


# pf is po file basename
def extract_po(pf):
    po_path = os.path.join(po_dir, pf)
    print("processing {}".format(po_path))

    epo = EPOFile(po_path)  # open once
    occurrence_map = get_po_occurrence_map(epo.po)

    dst_dir = simple_lang_slug(pf)  # lang

    for ef in sorted(occurrence_map):
        enc = get_enc(po_path, ef)
        ef_extract_path = os.path.join(dst_dir, ef)
        print("Extracting {} from {} into {} with encoding {}".format(ef, po_path, ef_extract_path, enc))
        po2file(epo, ef_extract_path, enc, ef, dst_dir=dst_dir, occurrence_map=occurrence_map)

    print("Extracted {} into {} with encoding {}".format(po_path, dst_dir, enc))


with cd(CONFIG.tra_dir):
    po_dir = CONFIG.po_dirname  # "po"

    # find PO files
    po_files = []
    for dir_name, subdir_list, file_list in os.walk(po_dir):
        for f in file_list:
            if get_ext(f) == "po":
                po_files.append(f)
    if po_files == []:
        print("no PO files found in directory {}".format(po_dir))
        sys.exit(1)

    # extract PO files
    threads_number = threads_number()
    print("Processing files with {} threads".format(threads_number))
    pool = ThreadPool(threads_number)
    try:
        pool.map(extract_po, po_files)
        pool.close()
    except KeyboardInterrupt:
        pool.terminate()
    finally:
        pool.join()
