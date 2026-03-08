#!/usr/bin/env python3
# Loads manually edited translation files back into PO msgstr fields.
# Reverse of unpoify: used when translators edit files directly instead of PO.

import argparse
import os
import sys
from typing import Optional

from loguru import logger
from polib import POFile, pofile

from msg2po.common import find_files, get_ext
from msg2po.config import CONFIG
from msg2po.conversion import file2msgstr
from msg2po.core import basename
from msg2po.encoding import get_enc
from msg2po.formats import VALID_EXTENSIONS
from msg2po.indexed_po import IndexedPO
from msg2po.languages import LanguageMap
from msg2po.log import cli_entry, setup_logging
from msg2po.po_utils import po_content_snapshot, po_make_unique


def dir2msgstr(
    src_dir: str,
    po: POFile,
    po_path: str = "",
    overwrite: bool = True,
    extension: str = "",
    same: bool = False,
    indexed_po: Optional[IndexedPO] = None,
):
    """Loads translated strings from files in src_dir into po (mutating it),
    then returns a deduplicated copy via po_make_unique."""
    logger.debug(f"overwrite is {overwrite}")

    skip_files = CONFIG.skip_files

    if indexed_po is None:
        indexed_po = IndexedPO.from_po(po)

    abs_src = os.path.abspath(src_dir)
    for dir_name, _subdir_list, file_list in os.walk(abs_src, topdown=False, followlinks=True):
        for file_name in file_list:
            abs_path = os.path.join(dir_name, file_name)
            rel_name = os.path.relpath(abs_path, abs_src)
            if os.sep != "/":
                rel_name = rel_name.replace(os.sep, "/")
            fext = get_ext(file_name)
            if fext != extension:
                continue
            if dir_name.endswith(CONFIG.female_dir_suffix):
                logger.debug(f"{rel_name} is a file with female strings, skipping")
                continue

            # Skip files as configured
            if rel_name in skip_files:
                logger.debug(f"{rel_name} is in skip_files. Skipping!")
                continue

            enc = get_enc(po_path, file_name)
            logger.info(f"processing {rel_name} with encoding {enc}")
            file2msgstr(
                input_file=abs_path,
                po=po,
                occurrence_path=rel_name,
                encoding=enc,
                overwrite=overwrite,
                same=same,
                indexed_po=indexed_po,
            )
    return po_make_unique(po)


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
        abs_tra = os.path.abspath(CONFIG.tra_dir)
        po_dir_abs = os.path.join(abs_tra, CONFIG.po_dirname)
        po_paths = find_files(po_dir_abs, "po")
        for pf in po_paths:
            rel_pf = os.path.relpath(pf, abs_tra)
            logger.info(f"Loading into {rel_pf}")
            slug = language_map.po2slug[basename(pf)]
            lang_dir = os.path.join(abs_tra, slug)
            po = pofile(pf)
            snapshot = po_content_snapshot(po)
            ipo = IndexedPO.from_po(po)
            for ve in VALID_EXTENSIONS:
                po = dir2msgstr(
                    src_dir=lang_dir,
                    po=po,
                    po_path=pf,
                    overwrite=args.overwrite,
                    extension=ve,
                    same=args.same,
                    indexed_po=ipo,
                )
                logger.info(f"Processed {ve} files in directory {slug}, the result is in {rel_pf}")
            if po_content_snapshot(po) != snapshot:
                po.save(pf, newline=CONFIG.newline_po)


if __name__ == "__main__":
    main()
