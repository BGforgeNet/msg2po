#!/usr/bin/env python3
"""
Update POs from POT. Behaves like
msgmerge -v --previous --no-wrap -U -N --backup=off lang1.po lang0.pot
Except that it allows string with "female" context to remain in PO,
if there's a corresponding male entry without such context.
"""

import argparse
import os
import subprocess
import sys
from functools import partial
from multiprocessing import Pool

from loguru import logger
from polib import pofile

from msg2po.common import find_files
from msg2po.config import CONFIG
from msg2po.log import cli_entry, setup_logging
from msg2po.po_utils import normalize_po, po_content_snapshot


def merge(po_path: str, pot_path: str):
    logger.info(po_path)
    exit_code = 0
    cmd = ["msgmerge", "--previous", "--no-wrap", "-U", "-q", "--backup=off", po_path, pot_path]
    res = subprocess.run(
        cmd,
        capture_output=True,
        check=True,
        text=True,
    )
    if res.stdout.strip():
        logger.debug(res.stdout.strip())
    if res.stderr.strip():
        logger.debug(res.stderr.strip())
    if res.returncode != 0:
        exit_code = res.returncode
        logger.error(f"msgmerge failed for {po_path}")
    # Normalize (restore female entries, dedup, sort) and save only if
    # entries actually changed. Avoids re-wrapping the entire file, which
    # would conflict with Weblate's wrapping.
    po2 = pofile(po_path)
    snapshot = po_content_snapshot(po2)
    po2 = normalize_po(po2)
    if po_content_snapshot(po2) != snapshot:
        po2.save(fpath=po_path, newline=CONFIG.newline_po)
    return exit_code


@cli_entry
def main():
    parser = argparse.ArgumentParser(
        description="Update POs from POT, keeping female entries. Requires Gettext msgmerge in PATH",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("PO", help="PO file", nargs="?", default=None)
    parser.add_argument("POT", help="POT file", nargs="?", default=None)
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress info messages")
    parser.add_argument("-t", "--timestamps", action="store_true", help="show timestamps in log output")
    args = parser.parse_args()
    setup_logging(verbose=args.verbose, quiet=args.quiet, timestamps=args.timestamps)

    # single file
    if (args.PO is not None) and (args.POT is not None):
        res = merge(args.PO, args.POT)
        if res != 0:
            logger.error(f"msgmerge failed for {args.PO}")
            sys.exit(1)
        sys.exit(0)

    # multifile, read .bgforge.yml
    po_dir = CONFIG.po_dir
    po_files = find_files(po_dir, "po")
    pot_file = os.path.join(po_dir, CONFIG.src_lang + ".pot")

    logger.info(f"Merging PO files in {po_dir} with {pot_file}")
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
            logger.error("one of msgmerge invocations failed.")
            sys.exit(1)


if __name__ == "__main__":
    main()
