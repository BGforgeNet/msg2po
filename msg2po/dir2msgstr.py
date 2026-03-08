#!/usr/bin/env python3

import argparse
import os
import re
import sys
from collections import OrderedDict
from typing import Optional

import polib
from loguru import logger
from polib import POFile, pofile

from msg2po.core import (
    CONFIG,
    VALID_EXTENSIONS,
    LanguageMap,
    basename,
    build_occurrence_dict,
    cd,
    female_entries,
    file2msgstr,
    find_files,
    get_enc,
    get_ext,
    po_make_unique,
)
from msg2po.log import cli_entry, setup_logging
from msg2po.po_utils import po_content_snapshot


def dir2msgstr(
    src_dir: str,
    po: POFile,
    po_path: str = "",
    overwrite: bool = True,
    extension: str = "",
    same: bool = False,
    female_map: Optional[dict[str, "polib.POEntry"]] = None,
    entries_dict: Optional["OrderedDict"] = None,
):
    """
    src_dir is relative
    overwrite means overwrite existing entries if any
    """
    logger.debug(f"overwrite is {overwrite}")

    skip_files = CONFIG.skip_files

    if female_map is None:
        female_map = female_entries(po)
    if entries_dict is None:
        entries_dict = build_occurrence_dict(po)

    with cd(src_dir):
        for dir_name, _subdir_list, file_list in os.walk(".", topdown=False, followlinks=True):
            for file_name in file_list:
                full_name = os.path.join(dir_name, file_name)
                full_name = re.sub(r"^\./", "", full_name)  # remove trailing './'
                fext = get_ext(file_name)
                if fext != extension:
                    continue
                if dir_name.endswith(CONFIG.female_dir_suffix):
                    logger.debug(f"{full_name} is a file with female strings, skipping")
                    continue

                # Skip files as configured
                if full_name in skip_files:
                    logger.debug(f"{full_name} is in skip_files. Skipping!")
                    continue

                enc = get_enc(po_path, file_name)
                logger.info(f"processing {full_name} with encoding {enc}")
                po = file2msgstr(
                    input_file=full_name,
                    po=po,
                    occurrence_path=full_name,
                    encoding=enc,
                    overwrite=overwrite,
                    same=same,
                    female_map=female_map,
                    entries_dict=entries_dict,
                )
    po = po_make_unique(po)
    return po


@cli_entry
def main():
    parser = argparse.ArgumentParser(
        description="Load strings from files in selected dir into PO msgstr's",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--auto",
        dest="auto",
        default=False,
        action="store_true",
        help="automatically find POs and language dirs, process all valid extensions",
        required=False,
    )
    parser.add_argument("-s", dest="src_dir", default=".", help="directory to load", required=False)
    parser.add_argument("-o", dest="output_file", default=None, help="existing PO file", required=False)
    parser.add_argument("--ext", dest="file_ext", default=None, help="load files with this extension", required=False)
    parser.add_argument(
        "--same",
        dest="same",
        default=False,
        action="store_true",
        help="load translations that are identical to original strings",
    )
    parser.add_argument(
        "--overwrite", dest="overwrite", default=False, action="store_true", help="overwrite existing translations"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress info messages")
    parser.add_argument("-t", "--timestamps", action="store_true", help="show timestamps in log output")
    args = parser.parse_args()
    setup_logging(verbose=args.verbose, quiet=args.quiet, timestamps=args.timestamps)

    if not args.auto and ((args.output_file is None) or (args.file_ext is None)):
        logger.error("you must either use auto mode or specify output PO and file extension")
        sys.exit(1)

    if not args.auto:
        output_file = args.output_file
        po = pofile(output_file)
        snapshot = po_content_snapshot(po)
        po = dir2msgstr(
            src_dir=args.src_dir,
            po=po,
            po_path=output_file,
            overwrite=args.overwrite,
            extension=args.file_ext,
            same=args.same,
        )
        if po_content_snapshot(po) != snapshot:
            po.save(output_file, newline=CONFIG.newline_po)
        logger.info(f"Processed directory {args.src_dir}, the result is in {output_file}")

    if args.auto:
        language_map = LanguageMap()
        with cd(CONFIG.tra_dir):
            po_paths = find_files(CONFIG.po_dirname, "po")
            for pf in po_paths:
                logger.info(f"Loading into {pf}")
                lang_dir = language_map.po2slug[basename(pf)]
                po = pofile(pf)
                snapshot = po_content_snapshot(po)
                female_map = female_entries(po)
                occ_dict = build_occurrence_dict(po)
                for ve in VALID_EXTENSIONS:
                    po = dir2msgstr(
                        src_dir=lang_dir,
                        po=po,
                        po_path=pf,
                        overwrite=args.overwrite,
                        extension=ve,
                        same=args.same,
                        female_map=female_map,
                        entries_dict=occ_dict,
                    )
                    logger.info(f"Processed {ve} files in directory {lang_dir}, the result is in {pf}")
                if po_content_snapshot(po) != snapshot:
                    po.save(pf, newline=CONFIG.newline_po)


if __name__ == "__main__":
    main()
