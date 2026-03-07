#!/usr/bin/env python3

import argparse
import os
import re
import shutil
import sys

import natsort
import polib
from loguru import logger

from msg2po.core import (
    CONFIG,
    VALID_EXTENSIONS,
    basename,
    cd,
    dir_or_exit,
    file2po,
    get_enc,
    get_ext,
    is_indexed,
    metadata,
    parent_dir,
    po_make_unique,
    sort_po,
)
from msg2po.log import cli_entry, setup_logging


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
    poify_dir = poify_dir.rstrip(os.sep + "/")
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
            os.walk(".", topdown=False, followlinks=True), alg=natsort.ns.PATH
        ):
            subdir_list = natsort.natsorted(subdir_list, alg=natsort.ns.PATH)
            file_list = natsort.natsorted(file_list, alg=natsort.ns.PATH)
            for file_name in file_list:
                full_name = os.path.join(dir_name, file_name)

                # convert windows paths to linux style, for consistency in POs
                if os.path.sep == "\\":
                    full_name = full_name.replace("\\", "/")

                full_name = re.sub(r"^\./", "", full_name)  # remove trailing './'

                # skip female cuts
                pretty_dir_name = re.sub(r"^\./", "", dir_name)
                if extract_format == "sfall" and pretty_dir_name == "cuts_female":
                    logger.debug(f"{full_name} is in cuts_female. Skipping!")
                    continue

                if full_name in skip_files:
                    logger.debug(f"{full_name} is in skip_files. Skipping!")
                    continue

                ext = get_ext(file_name)
                if ext not in VALID_EXTENSIONS:
                    continue

                # checked txt is indexed and if it is, process it
                if ext == "txt":
                    if is_indexed(full_name):
                        logger.debug(f"{full_name} is indexed TXT")
                    else:
                        logger.debug(f"{full_name} is TXT, but not indexed. Skipping!")
                        continue

                bname = basename(full_name)
                # non-default encoding?
                if encoding == CONFIG.encoding:
                    enc = get_enc(file_path=bname)
                else:
                    enc = encoding
                logger.info(f"processing {full_name} with encoding {enc}")
                po2 = file2po(full_name, encoding=enc)
                for e2 in po2:
                    po.append(e2)
    po = po_make_unique(po)
    po = sort_po(po)
    clean_po_dir(po_dir)

    if os.path.exists(dst_file):
        old_po = polib.pofile(dst_file)
        po.metadata = old_po.metadata
    else:
        old_po = polib.POFile()
    if po == old_po:
        logger.info(f"No change in source directory {poify_dir}")
        sys.exit(0)
    else:
        po.metadata = metadata(pot=True)

    po.save(dst_file, newline=CONFIG.newline_po)

    logger.info(f"Processed directory {poify_dir}, the result is in {tra_dir}/{po_dir}/{lang}.pot")


def tra_relpath(poify_dir: str) -> str:
    return os.path.relpath(parent_dir(poify_dir))


@cli_entry
def main():
    # parse args
    parser = argparse.ArgumentParser(
        description="Poify files in selected directory", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "DIR",
        nargs="?",
        default=f"{CONFIG.poify_dir}",
        help="source language directory",
    )
    parser.add_argument("-e", dest="enc", help="source encoding", default=f"{CONFIG.encoding}")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress info messages")
    parser.add_argument("-t", "--timestamps", action="store_true", help="show timestamps in log output")
    args = parser.parse_args()
    setup_logging(verbose=args.verbose, quiet=args.quiet, timestamps=args.timestamps)

    # init vars
    poify_dir = args.DIR
    dir_or_exit(poify_dir)

    # so that resulting po has relative occurences
    with cd(parent_dir(os.path.abspath(poify_dir))):
        poify(poify_dir)


if __name__ == "__main__":
    main()
