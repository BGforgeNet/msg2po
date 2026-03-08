#!/usr/bin/env python3

import argparse
import os
import shutil

import natsort
import polib
from loguru import logger

from msg2po.core import (
    CONFIG,
    VALID_EXTENSIONS,
    ensure_dir_exists,
    file2po,
    get_enc,
    get_ext,
    is_indexed,
    metadata,
    po_make_unique,
    sort_po,
)
from msg2po.log import cli_entry, setup_logging
from msg2po.po_utils import po_content_snapshot


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
    abs_poify_dir = os.path.abspath(poify_dir)
    base_dir = os.path.dirname(abs_poify_dir)
    lang = os.path.basename(abs_poify_dir)

    po_dir = os.path.join(base_dir, CONFIG.po_dirname)
    prepare_po_dir(po_dir)
    dst_file = os.path.join(po_dir, lang + ".pot")

    po = polib.POFile()

    # skip female cuts, they are built from male ones
    extract_format = CONFIG.extract_format
    skip_files = CONFIG.skip_files

    for dir_name, subdir_list, file_list in natsort.natsorted(
        os.walk(abs_poify_dir, topdown=False, followlinks=True), alg=natsort.ns.PATH
    ):
        subdir_list = natsort.natsorted(subdir_list, alg=natsort.ns.PATH)
        file_list = natsort.natsorted(file_list, alg=natsort.ns.PATH)
        for file_name in file_list:
            abs_path = os.path.join(dir_name, file_name)
            # relative to language dir for PO occurrences
            rel_name = os.path.relpath(abs_path, abs_poify_dir)

            # convert windows paths to linux style, for consistency in POs
            if os.path.sep == "\\":
                rel_name = rel_name.replace("\\", "/")

            # skip female cuts
            rel_dir = os.path.relpath(dir_name, abs_poify_dir)
            if extract_format == "sfall" and rel_dir == "cuts_female":
                logger.debug(f"{rel_name} is in cuts_female. Skipping!")
                continue

            if rel_name in skip_files:
                logger.debug(f"{rel_name} is in skip_files. Skipping!")
                continue

            ext = get_ext(file_name)
            if ext not in VALID_EXTENSIONS:
                continue

            # check txt is indexed and if it is, process it
            if ext == "txt":
                if is_indexed(abs_path):
                    logger.debug(f"{rel_name} is indexed TXT")
                else:
                    logger.debug(f"{rel_name} is TXT, but not indexed. Skipping!")
                    continue

            bname = os.path.basename(rel_name)
            # non-default encoding?
            if encoding == CONFIG.encoding:
                enc = get_enc(file_path=bname)
            else:
                enc = encoding
            logger.info(f"processing {rel_name} with encoding {enc}")
            po2 = file2po(abs_path, encoding=enc, occurrence_path=rel_name)
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
    if po_content_snapshot(po) == po_content_snapshot(old_po):
        logger.info(f"No change in source directory {poify_dir}")
        return
    else:
        po.metadata = metadata(pot=True)

    po.save(dst_file, newline=CONFIG.newline_po)

    logger.info(f"Processed directory {poify_dir}, the result is in {os.path.relpath(dst_file)}")


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
    ensure_dir_exists(poify_dir)
    poify(poify_dir)


if __name__ == "__main__":
    main()
