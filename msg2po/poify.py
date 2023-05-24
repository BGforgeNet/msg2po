#!/usr/bin/env python3
# coding: utf-8

import os
import sys
import argparse
import polib
import shutil
import re
from msg2po.core import (
    VALID_EXTENSIONS,
    dir_or_exit,
    get_enc,
    cd,
    basename,
    metadata,
    file2po,
    get_ext,
    po_make_unique,
    sort_po,
    parent_dir,
    is_indexed,
    CONFIG,
)
import natsort


# prepare po dir
def prepare_po_dir(d):
    if not os.path.isdir(d):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
    tmp_dir = os.path.join(d, "tmp")
    if not os.path.isdir(tmp_dir):
        shutil.rmtree(tmp_dir, ignore_errors=True)
        os.makedirs(tmp_dir)


def clean_po_dir(d):
    tmp_dir = os.path.join(d, "tmp")
    shutil.rmtree(tmp_dir, ignore_errors=True)


def poify(poify_dir: str, encoding: str = CONFIG.encoding):
    """
    poify_dir is path to source language directory
    """
    language_dir = os.path.basename(poify_dir)
    po_dir = CONFIG.po_dirname
    prepare_po_dir(po_dir)
    tra_dir = tra_relpath(poify_dir)
    # process with po_tool
    with cd(language_dir):
        # Final PO
        lang = basename(language_dir)
        dst_file = os.path.join(po_dir, lang + ".pot")
        po = polib.POFile()

        # skip female cuts, they are built from male ones
        extract_format = CONFIG.extract_format

        skip_files = CONFIG.skip_files

        for dir_name, subdir_list, file_list in natsort.natsorted(
            os.walk(".", topdown=False, followlinks=True), alg=natsort.PATH
        ):
            subdir_list = natsort.natsorted(subdir_list, alg=natsort.PATH)
            file_list = natsort.natsorted(file_list, alg=natsort.PATH)
            for file_name in file_list:
                full_name = os.path.join(dir_name, file_name)

                # convert windows paths to linux style, for consistency in POs
                if os.path.sep == "\\":
                    full_name = full_name.replace("\\", "/")

                full_name = re.sub("^\./", "", full_name)  # remove trailing './'

                # skip female cuts
                pretty_dir_name = re.sub("^\./", "", dir_name)
                if extract_format == "sfall" and pretty_dir_name == "cuts_female":
                    print("{} is in cuts_female. Skipping!".format(full_name))
                    continue

                if full_name in skip_files:
                    print("{} is in skip_files. Skipping!".format(full_name))
                    continue

                ext = get_ext(file_name)
                if ext not in VALID_EXTENSIONS:
                    continue

                # checked txt is indexed and if it is, process it
                if ext == "txt":
                    if is_indexed(full_name):
                        print("{} is indexed TXT".format(full_name))
                    else:
                        print("{} is TXT, but not indexed. Skipping!".format(full_name))
                        continue

                bname = basename(full_name)
                # non-default encoding?
                if encoding == CONFIG.encoding:
                    enc = get_enc(file_path=bname)
                else:
                    enc = encoding
                print("processing {} with encoding {}".format(full_name, enc))
                po2 = file2po(full_name, encoding=enc)
                for e2 in po2:
                    po.append(e2)
    po = po_make_unique(po)
    po = sort_po(po)
    clean_po_dir(po_dir)

    old_po = polib.pofile(dst_file)
    po.metadata = old_po.metadata
    if po == old_po:
        print("No change in source directory {}".format(poify_dir))
        sys.exit(0)
    else:
        po.metadata = metadata(pot=True)

    po.save(dst_file, newline=CONFIG.newline_po)

    print("Processed directory {}, the result is in {}/{}/{}.pot".format(poify_dir, tra_dir, po_dir, lang))


def tra_relpath(poify_dir: str) -> str:
    return os.path.relpath(parent_dir(poify_dir))


def main():
    # parse args
    parser = argparse.ArgumentParser(
        description="Poify files in selected directory", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "DIR",
        nargs="?",
        default="{}".format(CONFIG.poify_dir),
        help="source language directory",
    )
    parser.add_argument("-e", dest="enc", help="source encoding", default="{}".format(CONFIG.encoding))
    args = parser.parse_args()

    # init vars
    poify_dir = args.DIR
    dir_or_exit(poify_dir)

    # so that resulting po has relative occurences
    with cd(parent_dir(os.path.abspath(poify_dir))):
        poify(poify_dir)


if __name__ == "__main__":
    main()
