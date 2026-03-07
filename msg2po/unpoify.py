#!/usr/bin/env python3

import argparse
import concurrent.futures
import os
import sys

from loguru import logger
from polib import pofile

from msg2po.core import (
    CONFIG,
    LanguageMap,
    cd,
    dir_or_exit,
    female_entries,
    get_enc,
    get_ext,
    po2file,
    translation_entries,
)
from msg2po.log import cli_entry, setup_logging


def extract_po(pf: str, language_map: LanguageMap):
    """
    pf is po file basename
    """
    po_path = os.path.join(CONFIG.po_dirname, pf)
    logger.info(f"processing {po_path}")
    # Open PO once, it's a heavy op
    po = pofile(po_path)
    trans_map = translation_entries(po)
    female_map = female_entries(po)

    dst_dir = language_map.po2slug[pf]

    for ef in sorted(trans_map):
        enc = get_enc(po_path, ef)
        ef_extract_path = os.path.join(dst_dir, ef)
        logger.debug(f"Extracting {ef} from {po_path} into {ef_extract_path} with encoding {enc}")
        po2file(po, ef_extract_path, enc, ef, dst_dir=dst_dir, trans_map=trans_map, female_map=female_map)

    enc = get_enc(po_path)
    logger.info(f"Extracted {po_path} into {dst_dir} with encoding {enc}")


@cli_entry
def main():
    parser = argparse.ArgumentParser(
        description="Unpoify files into parent directory of selected PO dir",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("DIR", nargs="?", default=CONFIG.po_dir, help="directory with PO files")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress info messages")
    parser.add_argument("-t", "--timestamps", action="store_true", help="show timestamps in log output")
    args = parser.parse_args()
    setup_logging(verbose=args.verbose, quiet=args.quiet, timestamps=args.timestamps)

    po_dir = args.DIR
    dir_or_exit(po_dir)

    language_map = LanguageMap()

    # Find PO files
    po_files = [f for _, _, files in os.walk(po_dir) for f in files if get_ext(f) == "po"]

    if not po_files:
        logger.error(f"no PO files found in directory {po_dir}")
        sys.exit(1)

    with cd(CONFIG.tra_dir), concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {executor.submit(extract_po, pf, language_map): pf for pf in po_files}

        for future in concurrent.futures.as_completed(futures):
            pf = futures[future]
            try:
                future.result()
            except ValueError as e:
                logger.error(f"ValueError in file {pf}: {e}")
                executor.shutdown(wait=False, cancel_futures=True)
                sys.exit(1)
            except KeyboardInterrupt:
                logger.warning("Interrupted by user, terminating execution...")
                executor.shutdown(wait=False, cancel_futures=True)
                sys.exit(1)
            except Exception as e:
                logger.error(f"Unhandled exception in file {pf}: {e}")
                executor.shutdown(wait=False, cancel_futures=True)
                sys.exit(1)


if __name__ == "__main__":
    main()
