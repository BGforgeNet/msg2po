# Central module for msg2po. Contains file format definitions, TRANSFile/TRANSEntry
# classes for parsing game translation files, and conversion functions (file2po,
# po2file, file2msgstr).

import os
import re
import shutil
import unicodedata
from collections import OrderedDict
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, TypedDict

import polib
from loguru import logger

from msg2po.common import find_files, get_ext
from msg2po.config import CONFIG

# Re-export from encoding module for backwards compatibility
from msg2po.encoding import TRANSLITERATION_RULES_VIETNAMESE, encode_custom, get_enc, transliterate  # noqa: F401

# Re-export from po_utils module for backwards compatibility
from msg2po.po_utils import (  # noqa: F401
    CONTEXT_FEMALE,
    EMPTY_COMMENT,
    female_entries,
    metadata,
    normalize_po,
    po_make_unique,
    sort_po,
    translation_entries,
    unfuzzy_exact_matches,
    update_female_entries,
)

# extensions recognized by file2po, etc
VALID_EXTENSIONS = ["msg", "txt", "sve", "tra"]


class LineFormat(TypedDict, total=False):
    default: str
    context: str
    female: str


class FileFormat(TypedDict, total=False):
    pattern: str
    dotall: bool
    index: int
    value: int
    context: int
    female: int
    comment: str
    line_format: LineFormat
    forbidden_characters: list[str]


# supported file formats
# pattern is used to parse original files
# line_format to write to translated files
# index, value, context, female - order of these tokens in pattern
# dotall - whether file entries are multiline
FILE_FORMAT: dict[str, FileFormat] = {
    "msg": {
        "pattern": r"{(\d+)}{([^}]*)}{([^}]*)}",
        "dotall": True,
        "index": 0,
        "value": 2,
        "context": 1,
        "line_format": {
            "default": "{{{index}}}{{}}{{{value}}}\n",
            "context": "{{{index}}}{{{context}}}{{{value}}}\n",
            "female": "separate",
        },
        "forbidden_characters": ["{", "}"],
    },
    "sve": {
        "pattern": r"(\d+):(.*)",
        "dotall": False,
        "index": 0,
        "value": 1,
        "line_format": {
            "default": "{index}:{value}\n",
            "female": "separate",
        },
        "forbidden_characters": [],
    },
    "txt": {
        "pattern": r"(\d+):(.*)",
        "dotall": False,
        "index": 0,
        "value": 1,
        "comment": "indexed_txt",
        "line_format": {
            "default": "{index}:{value}\n",
            "female": "separate",
        },
        "forbidden_characters": [],
    },
    "tra": {
        "pattern": r"@(\d+)\s*?=\s*?~([^~]*?)~(?:\s)?(?:\[([^]]*)\])?(?:~([^~]*)~)?",
        "dotall": True,
        "index": 0,
        "value": 1,
        "context": 2,
        "female": 3,
        "line_format": {
            "default": "@{index} = ~{value}~\n",
            "context": "@{index} = ~{value}~ [{context}]\n",
            "female": "@{index} = ~{value}~ ~{female}~\n",
        },
        "forbidden_characters": [],
    },
}


# file and dir manipulation
#################################


def basename(path):
    return Path(path).resolve().name


def parent_dir(path):
    return str(Path(path).resolve().parent)


def strip_ext(filename):
    return Path(filename).stem


def get_dir(path: str):
    return str(Path(path).parent)


def create_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def dir_or_exit(d):
    if Path(d).is_dir():
        logger.debug(f"Found directory {d}")
    else:
        raise FileNotFoundError(f"Directory '{d}' does not exist. Check the path and try again.")


@contextmanager
def cd(newdir):
    if not newdir:
        raise ValueError("cannot change to empty directory path")
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


def copycreate(src_file, dst_file):
    Path(dst_file).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src_file, dst_file)


################################


def file2po(filepath: str, po_path: str = "", encoding: Optional[str] = None):
    """Returns PO file object"""
    if encoding is None:
        encoding = CONFIG.encoding

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
            e.occurrences.append((filepath, t.index))
            continue

        # no matching msgid + msgctxt, add new entry
        entry = polib.POEntry(
            msgid=t.value,
            msgstr="",
            occurrences=[
                (filepath, t.index),
            ],
            msgctxt=t.context,
            comment=t.comment,
        )
        po.append(entry)
        trans_map[(t.value, context)] = i
        i = i + 1

    return po


# check if extract file is present in po, exit with error if not
def check_path_in_po(po, path):
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
    trans_map=None,
    female_map=None,
):
    """
    Extract and write to disk a single file from POFile
    output_file is path relative to dst_dir
    dst_dir is actually dst language. Used in unpoify and po2file.
    """
    if trans_map is None:  # when extracting single file with po2tra/po2msg, etc
        # check if file is present in po, exit if not
        check_path_in_po(po, occurrence_path)
        trans_map = translation_entries(po)
    if female_map is None:
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
                logger.debug(f"Female strings are same, not copying - sfall will fallback to male {output_file}")
                return True  # cutoff the rest of the function
            else:
                logger.debug(f"Female strings are same, copying to {female_file}")
                copycreate(output_file, female_file)
        else:  # if it's different, extract separately
            if female_file is None:
                logger.warning(f"female strings are different, but female file is not supported for path {output_file}")
                return True
            else:
                logger.debug(f"Also extracting female counterpart into {female_file}")
                create_dir(get_dir(female_file))  # create dir if not exists
                with open(female_file, "w", encoding=encoding, newline=CONFIG.newline_tra) as file2:
                    file2.writelines(lines_female)


# nasty hack for sfall's female strings placement
def get_female_filepath(path: str, dst_dir: str, same: bool = True) -> Optional[str]:
    # default: just add _female suffix
    female_path: Optional[str] = path.replace(dst_dir + os.sep, dst_dir + CONFIG.female_dir_suffix + os.sep)
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
    And file extension
    Returns corresponding string with placeholders from line_format
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
    encoding: Optional[str] = None,
    overwrite: bool = True,
    same: bool = False,
    female_map: Optional[dict[str, polib.POEntry]] = None,
    entries_dict: Optional[OrderedDict] = None,
):
    """returns PO file object"""
    if encoding is None:
        encoding = CONFIG.encoding

    trans = TRANSFile(filepath=input_file, is_source=False, encoding=encoding)  # load translations

    if entries_dict is None:
        entries_dict = build_occurrence_dict(po)
    if female_map is None:
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

    return po


# check if TXT file is indexed
def is_indexed(txt_filename: str, encoding: Optional[str] = None) -> bool:
    if encoding is None:
        encoding = CONFIG.encoding
    try:
        with open(txt_filename, encoding=encoding) as f:
            # count non-empty lines
            num_lines = sum(1 for line in f if line.rstrip())

        # count lines that are indexed
        pattern = FILE_FORMAT["txt"]["pattern"]
        with open(txt_filename, encoding=encoding) as f:
            text = f.read()
    except UnicodeDecodeError as e:
        raise ValueError(f"Failed to read '{txt_filename}' with encoding '{encoding}': {e}") from None
    indexed_lines = re.findall(pattern, text)
    num_indexed_lines = len(indexed_lines)
    return num_lines == num_indexed_lines


class TRANSEntry:
    def __init__(self):
        self.index = None
        self.value = None
        self.context = None
        self.female = None
        self.comment = None


class TRANSFile:
    """
    Common translation class, holding translation entries of a single file
    is_source: if set, adds EMPTY_COMMENT to all empty lines
    This is because PO gettext format doesn't tolerate empty msgids
    """

    def __init__(self, filepath: str, is_source: bool = False, encoding: Optional[str] = None):
        self.entries: list[TRANSEntry] = []
        if encoding is None:
            encoding = CONFIG.encoding
        self.encoding = encoding
        fext = get_ext(filepath)
        self.fformat: FileFormat = FILE_FORMAT[fext]
        self.pattern: str = self.fformat["pattern"]
        self.dotall: bool = self.fformat["dotall"]
        self.filepath = filepath
        self.forbidden_characters: list[str] = self.fformat["forbidden_characters"]
        self.comment: Optional[str] = self.fformat.get("comment")

        self.lines = self.load_lines(filepath)

        # enabled for file2msgstr, disabled for file2po
        if not is_source:
            self.lines_female = None
            if self.fformat["line_format"]["female"] == "separate":
                female_dir = get_dir(filepath) + CONFIG.female_dir_suffix
                female_file = os.path.join(female_dir, basename(filepath))
                if os.path.isfile(female_file):
                    logger.debug(f"found female file {female_file}")
                    self.lines_female = self.load_lines(female_file)
                else:
                    logger.debug(f"female file not found: {female_file}")

            if self.lines_female is not None:
                if self.lines_female == self.lines:
                    logger.debug("female lines are identical")
                else:
                    logger.debug("female lines are different")

        # protection against duplicate indexes, part 1
        seen: set[str] = set()

        for line in self.lines:
            entry = TRANSEntry()

            # index and value
            index = line[self.fformat["index"]]
            entry.value = str(line[self.fformat["value"]])

            for fc in self.forbidden_characters:
                if fc in entry.value:
                    logger.error(f"{fext} strings may not contain '{fc}' character, entry: {entry}")
                    raise ValueError("Invalid translation character")

            # fail on invalid '000' entries in MSG files
            if index == "000":
                logger.error(f"{filepath} - invalid entry index '000' found, entry: {entry}")
                raise ValueError("Invalid entry index")

            entry.index = line[self.fformat["index"]]

            # comment
            # 1. generic comment for all entries in file
            entry.comment = self.comment
            # 2. handle empty lines in source files
            if entry.value == "" and is_source is True:
                entry.value = " "
                entry.comment = EMPTY_COMMENT

            # context
            if "context" in self.fformat:
                entry.context = line[self.fformat["context"]]
            if entry.context == "":
                entry.context = None

            # female
            if fext == "tra" and "female" in self.fformat:  # TRA file specific
                entry.female = str(line[self.fformat["female"]])
                if entry.female == "":
                    entry.female = None

                if entry.female and entry.context:
                    raise ValueError(f"TRA strings with female variants may not have context: {line}")

            # sfall female extraction
            if not is_source and (self.lines_female is not None) and self.lines_female != self.lines:
                matching = [fl for fl in self.lines_female if fl[self.fformat["index"]] == entry.index]
                if matching:
                    female_line = matching[0]
                    entry.female = str(female_line[self.fformat["value"]])
                    if entry.female != entry.value:
                        logger.debug(f"found alternative female string for line {entry.index}: {entry.female}")

            # protection against duplicate indexes, part 2
            if entry.index in seen:
                logger.error(f"{filepath} - duplicate string index '{entry.index}', last value: {entry.value}")
                raise ValueError("Duplicate entry indices")
            else:
                seen.add(index)

            # produce the final list of strings
            if entry.value is not None and entry.value != "":
                self.entries.append(entry)

    def load_lines(self, filepath: str):
        try:
            with open(filepath, encoding=self.encoding) as fh:
                text = fh.read()
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to read '{filepath}' with encoding '{self.encoding}': {e}") from None
        # cp1258 decodes into a mixed normalization form (some precomposed, some
        # combining marks). Normalize to NFC to match PO files (source of truth).
        if self.encoding == "cp1258":
            text = unicodedata.normalize("NFC", text)
        if self.dotall:
            lines = re.findall(self.pattern, text, re.DOTALL)
        else:
            lines = re.findall(self.pattern, text)
        return lines


def language_slug(po_filename):
    """
    Allows to extract PO files into simplified language names: pt_BR.po -> portuguese/1.msg.
    Working with language codes is not convenient in mods.
    A temporary hack until a better solution is found.
    """
    slug_map = {
        "cs": "czech",
        "de": "german",
        "fr": "french",
        "it": "italian",
        "hu": "hungarian",
        "pl": "polish",
        "pt": "portuguese",
        "pt_br": "portuguese",
        "es": "spanish",
        "ru": "russian",
        "sv": "swedish",
        "tchinese": "tchinese",
        "uk": "ukrainian",
        "vi": "vietnamese",
    }
    slug = strip_ext(basename(po_filename)).lower()
    if CONFIG.simple_languages:
        slug = slug_map.get(slug, slug)
    return slug


class LanguageMap:
    """
    map PO basenames to language dir names, for unpoify and dir2msgstr
    This is because languages added through Weblate use codes like pt_BR, see find_files
    """

    def __init__(self):
        po_files = find_files(CONFIG.po_dir, "po")
        self.slug2po = {}
        self.po2slug = {}
        for pf in po_files:
            pf = basename(pf)
            slug = language_slug(pf)
            self.slug2po[slug] = pf
            self.po2slug[pf] = slug
