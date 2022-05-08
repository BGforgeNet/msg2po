#!/usr/bin/env python3
# coding: utf-8

import os
import argparse
import re
import sys
from msg2po.core import (
    VALID_EXTENSIONS,
    LanguageMap,
    cd,
    female_entries,
    find_files,
    get_ext,
    get_enc,
    file2msgstr,
    po_make_unique,
    CONFIG,
    basename,
)
from polib import pofile, POFile

# parse args
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
args = parser.parse_args()


def dir2msgstr(src_dir: str, po: POFile, po_path: str = "", overwrite: bool = True, extension: str = ""):
    """
    src_dir is relative
    overwrite means ovewrite existing entries if any
    """
    print("overwrite is " + str(overwrite))

    with cd(src_dir):
        female_map = female_entries(po)

        for dir_name, subdir_list, file_list in os.walk(".", topdown=False, followlinks=True):
            for file_name in file_list:
                full_name = os.path.join(dir_name, file_name)
                full_name = re.sub("^\./", "", full_name)  # remove trailing './'
                fext = get_ext(file_name)
                if fext != extension:
                    continue
                if dir_name.endswith(CONFIG.female_dir_suffix):
                    print("{} is a file with female strings, skipping".format(full_name))
                    continue

                enc = get_enc(po_path, file_name)
                print("processing {} with encoding {}".format(full_name, enc))
                po = file2msgstr(
                    input_file=full_name,
                    po=po,
                    occurence_path=full_name,
                    encoding=enc,
                    overwrite=overwrite,
                    same=args.same,
                    female_map=female_map
                )
    po = po_make_unique(po)
    return po


def main():
    if not args.auto and ((args.output_file is None) or (args.file_ext is None)):
        print("ERROR: you must either use auto mode or specify output PO and file extension")
        sys.exit(1)

    if not args.auto:
        output_file = args.output_file
        po = pofile(output_file)
        po = dir2msgstr(
            src_dir=args.src_dir, po=po, po_path=output_file, overwrite=args.overwrite, extension=args.file_ext
        )
        po.save(output_file, newline=CONFIG.newline_po)
        print("Processed directory {}, the result is in {}".format(args.src_dir, output_file))

    if args.auto:
        language_map = LanguageMap()
        with cd(CONFIG.tra_dir):
            po_paths = find_files(CONFIG.po_dirname, "po")
            for pf in po_paths:
                print("Loading into {}".format(pf))
                lang_dir = language_map.po2slug[basename(pf)]
                po = pofile(pf)
                for ve in VALID_EXTENSIONS:
                    po = dir2msgstr(src_dir=lang_dir, po=po, po_path=pf, overwrite=args.overwrite, extension=ve)
                    po.save(pf, newline=CONFIG.newline_po)
                    print("Processed {} files in directory {}, the result is in {}".format(ve, lang_dir, pf))


if __name__ == "__main__":
    main()
