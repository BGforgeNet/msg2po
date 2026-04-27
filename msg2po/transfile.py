# Translation file parser. Reads game translation files (MSG, SVE, TXT, TRA)
# into TRANSFile/TRANSEntry structures for conversion to/from PO format.

import os
import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from loguru import logger

from msg2po.common import get_ext
from msg2po.config import CONFIG
from msg2po.core import basename, get_dir
from msg2po.formats import FILE_FORMAT, FileFormat
from msg2po.po_utils import EMPTY_COMMENT


@dataclass(frozen=True)
class TRANSEntry:
    index: str
    value: str
    context: Optional[str] = None
    female: Optional[str] = None
    comment: Optional[str] = None


def _load_lines(filepath: str, pattern: str, dotall: bool, encoding: str) -> list[tuple[str, ...]]:
    """Read a translation file and return regex-matched line tuples."""
    try:
        with open(filepath, encoding=encoding) as fh:
            text = fh.read()
    except UnicodeDecodeError as e:
        raise ValueError(f"Failed to read '{filepath}' with encoding '{encoding}': {e}") from None
    # cp1258 decodes into a mixed normalization form (some precomposed, some
    # combining marks). Normalize to NFC to match PO files (source of truth).
    if encoding == "cp1258":
        text = unicodedata.normalize("NFC", text)
    if dotall:
        return re.findall(pattern, text, re.DOTALL)
    return re.findall(pattern, text)


def _load_female_lines(filepath: str, fformat: FileFormat, encoding: str) -> Optional[list[tuple[str, ...]]]:
    """Load separate female file lines if the format uses separate female files.
    Returns None if no female file exists or format uses inline female."""
    if fformat["line_format"]["female"] != "separate":
        return None

    female_dir = get_dir(filepath) + CONFIG.female_dir_suffix
    female_file = os.path.join(female_dir, basename(filepath))
    if not os.path.isfile(female_file):
        logger.debug(f"female file not found: {female_file}")
        return None

    logger.debug(f"found female file {female_file}")
    lines = _load_lines(female_file, fformat["pattern"], fformat["dotall"], encoding)
    return lines


def _parse_entries(
    lines: list[tuple[str, ...]],
    fformat: FileFormat,
    fext: str,
    filepath: str,
    is_source: bool,
    comment: Optional[str],
    female_lines: Optional[list[tuple[str, ...]]],
) -> list[TRANSEntry]:
    """Parse regex-matched lines into TRANSEntry objects.
    Validates forbidden characters, duplicate indices, and '000' index."""
    entries: list[TRANSEntry] = []
    seen: set[str] = set()
    forbidden_characters = fformat["forbidden_characters"]

    for line in lines:
        index = line[fformat["index"]]
        value = str(line[fformat["value"]])

        for fc in forbidden_characters:
            if fc in value:
                logger.error(f"{fext} strings may not contain '{fc}' character, index: {index}, value: {value}")
                raise ValueError("Invalid translation character")

        if index == "000":
            logger.error(f"{filepath} - invalid entry index '000' found, value: {value}")
            raise ValueError("Invalid entry index")

        # handle empty lines in source files
        entry_comment = comment
        if value == "" and is_source is True:
            value = " "
            entry_comment = EMPTY_COMMENT

        # context
        context: Optional[str] = None
        if "context" in fformat:
            context = line[fformat["context"]]
        if context == "":
            context = None

        # inline female (format has female index in regex, e.g. TRA)
        female: Optional[str] = None
        if "female" in fformat:
            female = str(line[fformat["female"]])
            if female == "":
                female = None
            if female and context:
                raise ValueError(f"Strings with inline female variants may not have context: {line}")

        # separate female files (sfall)
        if not is_source and female_lines is not None and female_lines != lines:
            matching = [fl for fl in female_lines if fl[fformat["index"]] == index]
            if matching:
                female_value = str(matching[0][fformat["value"]])
                if female_value != value:
                    logger.debug(f"found alternative female string for line {index}: {female_value}")
                female = female_value

        if index in seen:
            logger.error(f"{filepath} - duplicate string index '{index}', last value: {value}")
            raise ValueError("Duplicate entry indices")
        seen.add(index)

        if value is not None and value != "":
            entries.append(TRANSEntry(index=index, value=value, context=context, female=female, comment=entry_comment))

    return entries


class TRANSFile:
    """
    Common translation class, holding translation entries of a single file.
    is_source: if set, adds EMPTY_COMMENT to all empty lines.
    This is because PO gettext format doesn't tolerate empty msgids.
    """

    def __init__(self, filepath: str, is_source: bool = False, encoding: Optional[str] = None):
        if encoding is None:
            encoding = CONFIG.encoding
        self.encoding = encoding
        fext = get_ext(filepath)
        self.fformat: FileFormat = FILE_FORMAT[fext]
        self.filepath = filepath

        lines = _load_lines(filepath, self.fformat["pattern"], self.fformat["dotall"], encoding)

        female_lines = None
        if not is_source:
            female_lines = _load_female_lines(filepath, self.fformat, encoding)
            if female_lines is not None:
                if female_lines == lines:
                    logger.debug("female lines are identical")
                else:
                    logger.debug("female lines are different")

        self.entries = _parse_entries(
            lines, self.fformat, fext, filepath, is_source, self.fformat.get("comment"), female_lines
        )


def is_indexed(txt_filename: str, encoding: Optional[str] = None) -> bool:
    """Check if a TXT file is fully indexed (all non-empty lines match index:value pattern)."""
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
