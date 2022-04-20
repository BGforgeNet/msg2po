#!/usr/bin/env python3
# coding: utf-8

import os
import argparse
import sys
import bgforge_po
from multiprocessing import Pool as ThreadPool


default_po_dir = bgforge_po.get_po_dir()

# parse args
parser = argparse.ArgumentParser(
    description="Unpoify files into parent directory of selected PO dir",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("DIR", nargs="?", default=default_po_dir, help="directory with PO files")
args = parser.parse_args()

# init vars
po_dir = args.DIR
bgforge_po.dir_or_exit(po_dir)
tra_dir = bgforge_po.parent_dir(po_dir)


# pf is po file basename
def extract_po(pf):
    po_path = os.path.join(po_dir, pf)
    print("processing {}".format(po_path))

    epo = bgforge_po.epofile(po_path)  # open once
    occurrence_map = bgforge_po.get_po_occurrence_map(epo.po)

    dst_dir = bgforge_po.output_lang_slug(pf)  # lang

    for ef in sorted(occurrence_map):
        enc = bgforge_po.get_enc(po_path, ef)
        ef_extract_path = os.path.join(dst_dir, ef)
        print("Extracting {} from {} into {} with encoding {}".format(ef, po_path, ef_extract_path, enc))
        bgforge_po.po2file(epo, ef_extract_path, enc, ef, dst_dir=dst_dir, occurrence_map=occurrence_map)

    print("Extracted {} into {} with encoding {}".format(po_path, dst_dir, enc))


with bgforge_po.cd(tra_dir):
    po_dir = bgforge_po.po_dirname  # "po"

    # find PO files
    po_files = []
    for dir_name, subdir_list, file_list in os.walk(po_dir):
        for f in file_list:
            if bgforge_po.get_ext(f) == "po":
                po_files.append(f)
    if po_files == []:
        print("no PO files found in directory {}".format(po_dir))
        sys.exit(1)

    # extract PO files
    threads_number = bgforge_po.threads_number()
    print("Processing files with {} threads".format(threads_number))
    pool = ThreadPool(threads_number)
    try:
        pool.map(extract_po, po_files)
        pool.close()
    except KeyboardInterrupt:
        pool.terminate()
    finally:
        pool.join()
