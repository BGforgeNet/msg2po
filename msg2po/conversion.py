# Conversion functions between game translation files and PO format.
# file2po: game file -> PO entries
# po2file: PO entries -> game file
# file2msgstr: game file translations -> PO msgstr fields

from __future__ import annotations

import os
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from msg2po.indexed_po import IndexedPO

import polib
from loguru import logger

from msg2po.common import get_ext
from msg2po.config import CONFIG
from msg2po.core import copycreate, create_dir, get_dir
from msg2po.encoding import encode_custom
from msg2po.formats import FILE_FORMAT
from msg2po.po_utils import CONTEXT_FEMALE, EMPTY_COMMENT, female_entries, metadata, translation_entries
from msg2po.transfile import TRANSFile


def file2po(filepath: str, po_path: str = "", encoding: str | None = None, occurrence_path: str | None = None):
    """Returns PO file object"""
    if encoding is None:
        encoding = CONFIG.encoding
    if occurrence_path is None:
        occurrence_path = filepath

    trans = TRANSFile(filepath=filepath, is_source=True, encoding=encoding)  # load translations

    if po_path == "":
        po = polib.POFile()
        po.metadata = metadata()
    else:
        po = polib.pofile(po_path)

    trans_map = {}
    i = 0  # index in PO object
    for t in trans.entries:
        context = t.context

        # append to occurrences if id and context match
        if (t.value, context) in trans_map:
            e = po[trans_map[(t.value, context)]]
            e.occurrences.append((occurrence_path, t.index))
            continue

        # no matching msgid + msgctxt, add new entry
        entry = polib.POEntry(
            msgid=t.value,
            msgstr="",
            occurrences=[
                (occurrence_path, t.index),
            ],
            msgctxt=t.context,
            comment=t.comment,
        )
        po.append(entry)
        trans_map[(t.value, context)] = i
        i = i + 1

    return po


def check_path_in_po(po, path):
    """Check if extract file is present in po, raise FileNotFoundError if not."""
    present_files = set()
    for entry in po:
        for eo in entry.occurrences:
            present_files.add(eo[0])
    present_files_list = sorted(set(present_files))
    if path not in present_files_list:
        available = "\n".join(present_files_list)
        raise FileNotFoundError(
            f"{path} is not present in selected PO file.\n"
            f"Supply one of present files with --path argument:\n{available}"
        )


def po2file(
    po: polib.POFile,
    output_file: str,
    encoding: str,
    occurrence_path: str,
    dst_dir=None,
    indexed_po: IndexedPO | None = None,
) -> None:
    """
    Extract and write to disk a single file from POFile.
    output_file is the file path to write to.
    occurrence_path is the relative path used for PO occurrence matching.
    dst_dir is the destination language directory. Used in unpoify and po2file.
    indexed_po provides precomputed indexes; if None, indexes are computed on demand.
    """
    if indexed_po is not None:
        trans_map = indexed_po.trans_map
        female_map = indexed_po.female_map
    else:
        check_path_in_po(po, occurrence_path)
        trans_map = translation_entries(po)
        female_map = female_entries(po)

    # create parent directory
    create_dir(get_dir(output_file))

    ext = get_ext(output_file)
    ff = FILE_FORMAT[ext]
    line_format = ff["line_format"]

    context = ""
    resulting_entries = []
    extract_fuzzy = CONFIG.extract_fuzzy

    for file_trans in trans_map[occurrence_path]:
        file_index = file_trans["file_index"]
        po_index = file_trans["po_index"]
        entry = po[po_index]

        if entry.msgstr == "" or "fuzzy" in entry.flags and not extract_fuzzy:  # if not translated, keep msgid
            value = entry.msgid
        else:
            value = entry.msgstr  # either translated or fuzzy+extract_fuzzy

        # empty lines detected by comment
        if entry.comment == EMPTY_COMMENT:
            value = ""

        # context
        context = entry.msgctxt

        # female strings
        female = None
        if entry.msgid in female_map:
            fe_entry = female_map[entry.msgid]
            if fe_entry.msgstr == "" or "fuzzy" in fe_entry.flags and not extract_fuzzy:
                female = fe_entry.msgid
            else:
                female = fe_entry.msgstr

        resulting_entries.append({"index": file_index, "value": value, "female": female, "context": context})

    # combined occurrences may mess up order, restoring
    resulting_entries = sorted(resulting_entries, key=lambda k: k["index"])

    lines = []
    lines_female = []

    for res in resulting_entries:
        # get line format
        lfrm = get_line_format(res, ext)

        # add line to common/male package
        line = lfrm.format(index=res["index"], value=res["value"], context=res["context"], female=res["female"])
        # TODO: get rid of replace, handle improper characters in weblate
        lines.append(encode_custom(line, encoding))

        # add string to female package if needed
        if "female" in line_format and line_format["female"] == "separate":
            if res["female"] is not None:
                female_line = lfrm.format(index=res["index"], value=res["female"], context=res["context"])
            else:
                female_line = lfrm.format(index=res["index"], value=res["value"], context=res["context"])
            lines_female.append(encode_custom(female_line, encoding))

    # write main package
    with open(output_file, "w", encoding=encoding, newline=CONFIG.newline_tra) as file:
        file.writelines(lines)

    # explicitly disabled female?
    no_female = CONFIG.no_female

    if ("female" in line_format) and line_format["female"] == "separate" and dst_dir is not None and not no_female:
        # are translations the same? If yes, skipping copying "dialog" in sfall
        same = False
        if lines_female == lines:
            same = True

        # what's out path?
        female_file = get_female_filepath(output_file, dst_dir, same)

        # If need to create the file
        if same:  # if female translation is the same?
            if female_file is None:  # don't need to copy, automatic fallback
                logger.debug(f"Female strings are same, not copying - sfall will fallback to male {occurrence_path}")
                return
            else:
                logger.debug(f"Female strings are same, copying to {female_file}")
                copycreate(output_file, female_file)
        else:  # if it's different, extract separately
            if female_file is None:
                logger.warning(
                    f"female strings are different, but female file is not supported for path {occurrence_path}"
                )
                return
            else:
                logger.debug(f"Also extracting female counterpart into {female_file}")
                create_dir(get_dir(female_file))  # create dir if not exists
                with open(female_file, "w", encoding=encoding, newline=CONFIG.newline_tra) as file2:
                    file2.writelines(lines_female)


def get_female_filepath(path: str, dst_dir: str, same: bool = True) -> str | None:
    """Determine female file path based on format and sfall conventions."""
    # default: just add _female suffix
    female_path: str | None = path.replace(dst_dir + os.sep, dst_dir + CONFIG.female_dir_suffix + os.sep)
    if CONFIG.extract_format == "sfall":
        female_path = None  # default for sfall: don't copy, it will fallback to male
        if "cuts" in path.split(os.sep):  # cuts dont' fallback
            female_path = path.replace(os.sep + "cuts" + os.sep, os.sep + "cuts_female" + os.sep)
        if "dialog" in path.split(os.sep) and not same:  # dialog, female translation differs
            female_path = path.replace(os.sep + "dialog" + os.sep, os.sep + "dialog_female" + os.sep)
    return female_path


def get_line_format(e, ext: str):
    """
    Takes translation entry in format {'index': index, 'value': value, 'female': female, 'context': context}
    And file extension.
    Returns corresponding string with placeholders from line_format.
    """
    ff = FILE_FORMAT[ext]
    line_format = ff["line_format"]

    forbidden_characters = ff["forbidden_characters"]
    for fc in forbidden_characters:
        if fc in e["value"]:
            logger.error(f"{ext} strings may not contain '{fc}' character, entry: {e}")
            raise ValueError("Invalid translation character")

    if e["context"] is not None:  # entry with context
        lfrm = line_format["context"]
    elif (
        "female" in e and e["female"] is not None and "female" in line_format and line_format["female"] != "separate"
    ):  # format with native support for female strings
        lfrm = line_format["female"]
    else:  # no context and no female, or format without native support for female strings
        lfrm = line_format["default"]
    return lfrm


def build_occurrence_dict(po: polib.POFile) -> OrderedDict:
    """Build a dict mapping (filepath, line_number) to PO entry for fast lookup."""
    entries_dict = OrderedDict()
    for e in po:
        for eo in e.occurrences:
            entries_dict[(eo[0], eo[1])] = e
    return entries_dict


def file2msgstr(
    input_file: str,
    po: polib.POFile,
    occurrence_path: str,
    encoding: str | None = None,
    overwrite: bool = True,
    same: bool = False,
    indexed_po: IndexedPO | None = None,
) -> None:
    """Loads translated strings from input_file into po, mutating it in place."""
    if encoding is None:
        encoding = CONFIG.encoding

    trans = TRANSFile(filepath=input_file, is_source=False, encoding=encoding)  # load translations

    if indexed_po is not None:
        entries_dict = indexed_po.occ_dict
        female_map = indexed_po.female_map
    else:
        entries_dict = build_occurrence_dict(po)
        female_map = female_entries(po)

    # newly added female entries, without PO counterpart
    new_female_entries = []

    for t in trans.entries:
        index = t.index
        value = t.value
        context = t.context
        female_value = t.female

        if (value is None) or (value == ""):
            logger.warning(f"no msgid found for {occurrence_path}:{index}, skipping string: {value}")
            continue

        if (occurrence_path, index) in entries_dict:
            # map entries to occurrences for faster access, part 2
            e: polib.POEntry = entries_dict[(occurrence_path, index)]

            if female_value:
                # female entries have no occurrences, checking if female translation already present
                if e.msgid in female_map:
                    fe: polib.POEntry = female_map[e.msgid]
                    if fe and (fe.msgstr != female_value):
                        logger.info(
                            f"female translation change: ORIG: {e.msgid} | OLD: {fe.msgstr} | NEW: {female_value}"
                        )
                        skip = False
                        if not overwrite:
                            logger.debug("Female translation already exists, overwrite disabled, skipping")
                            skip = True
                        if not skip and (e.msgid == female_value):
                            if same:
                                logger.info(f"source and female translation are the same, using regardless: {e.msgid}")
                            else:
                                logger.info(f"source and female translation are the same for {e.occurrences}, skipping")
                                skip = True
                        if not skip:
                            fe.msgstr = female_value
                            if "fuzzy" in fe.flags:
                                logger.debug("Unfuzzied female entry")
                                fe.flags.remove("fuzzy")
                                fe.previous_msgid = None
                elif e.msgstr != female_value:
                    logger.info(
                        f"new female translation detected: ORIG: {e.msgid} | MALE: {e.msgstr} | FEMALE: {female_value}"
                    )
                    fe = polib.POEntry(msgid=e.msgid, msgstr=female_value, msgctxt=CONTEXT_FEMALE)
                    new_female_entries.append(fe)

            # translation is the same
            if e.msgstr == value and e.msgctxt == context:
                logger.debug(f"translation is the same for {e.occurrences}")
                if "fuzzy" in e.flags:
                    if CONFIG.extract_fuzzy:
                        logger.debug(f"{e.occurrences} is fuzzy. Keeping fuzzy flag.")
                        continue
                    else:
                        logger.debug(
                            f"{e.occurrences} is fuzzy, but extract_fuzzy is not set. "
                            "Assuming manual translation change to the same value, clearing fuzzy flag."
                        )
                else:
                    continue

            # translation is the same as source
            if e.msgid == value and not same:
                logger.debug(f"string and new translation are the same for {e.occurrences}, skipping: {e.msgid}")
                continue

            # if translation already exists and different, and overwrite is disabled, cutoff
            if e.msgstr is not None and e.msgstr != "" and e.msgstr != value and not overwrite:
                logger.debug(f"translation already exists for {e.occurrences}, overwrite disabled, skipping")
                continue

            # finally, all checks passed
            logger.info(f"translation update for {e.occurrences}: ORIG: {e.msgid} | OLD: {e.msgstr} | NEW: {value}")
            e.msgstr = value
            e.msgctxt = context
            if "fuzzy" in e.flags or e.previous_msgid:
                logger.debug("Unfuzzied entry")
                e.previous_msgid = None
                if "fuzzy" in e.flags:
                    e.flags.remove("fuzzy")

    # add newly found female entries
    for nfe in new_female_entries:
        po.append(nfe)
