# Encoding detection and transcoding for game translation files.
# Handles per-language encoding lookup, Vietnamese transliteration,
# and console/UTF-8 filename overrides.

import re
import unicodedata
from pathlib import Path

from msg2po.config import CONFIG

TRANSLITERATION_RULES_VIETNAMESE = {
    "a\u0306": "\u0103",  # ă
    "A\u0306": "\u0102",  # Ă
    "a\u0323\u0306": "\u0103\u0323",  # ặ
    "A\u0323\u0306": "\u0102\u0323",  # Ặ
    "a\u0302": "\u00e2",  # â
    "A\u0302": "\u00c2",  # Â
    "a\u0323\u0302": "\u00e2\u0323",  # ậ
    "A\u0323\u0302": "\u00c2\u0323",  # Ậ
    "e\u0302": "\u00ea",  # ê
    "E\u0302": "\u00ca",  # Ê
    "e\u0323\u0302": "\u00ea\u0323",  # ệ
    "E\u0323\u0302": "\u00ca\u0323",  # Ệ
    "o\u0302": "\u00f4",  # ô
    "O\u0302": "\u00d4",  # Ô
    "o\u0323\u0302": "\u00f4\u0323",  # ộ
    "O\u0323\u0302": "\u00d4\u0323",  # Ộ
    "o\u031b": "\u01a1",  # ơ
    "O\u031b": "\u01a0",  # Ơ
    "u\u031b": "\u01b0",  # ư
    "U\u031b": "\u01af",  # Ư
}

ENCODINGS = {
    "schinese": "cp936",
    "tchinese": "cp950",
    "czech": "cp1250",
    "hungarian": "cp1250",
    "japanese": "cp932",
    "korean": "cp949",
    "polish": "cp1250",
    "polski": "cp1250",
    "russian": "cp1251",
    "ukrainian": "cp1251",
    "vietnamese": "cp1258",
}

ANSI_ENCODINGS = {
    #  'czech': 'cp852',
    #  'polish': 'cp852',
    #  'polski': 'cp852',
    "russian": "cp866",
    "ukrainian": "cp866",
    #  'french': 'cp850',
    #  'francais': 'cp850',
    #  'german': 'cp850',
    #  'deutsch': 'cp850',
    #  'italian': 'cp850',
    #  'italiano': 'cp850',
    #  'spanish': 'cp850',
    #  'espanol': 'cp850',
    #  'castilian': 'cp850',
    #  'castellano': 'cp850',
}

CONSOLE_FILENAMES = [
    "setup.tra",
    "install.tra",
]

UTF_FILENAMES = [
    "ee.tra",
]


def get_enc(lang_path: str = "", file_path: str = ""):
    """
    Infers encoding based on dir/PO name and file path.
    lang_path can be PO path or translation path, only basename is used.
    """
    # language_slug imported here to avoid circular dependency (it lives in core)
    from msg2po.core import language_slug

    filename = Path(file_path).resolve().name

    # All utf-8, maybe except console
    if CONFIG.all_utf8 is True:
        if not CONFIG.ansi_console:
            return "utf-8"
        if filename not in CONSOLE_FILENAMES:
            return "utf-8"

    # Configured encoding
    encoding = CONFIG.encoding
    lang = language_slug(lang_path)

    # Try known encodings
    if lang in ENCODINGS:
        encoding = ENCODINGS[lang]

    if filename in CONSOLE_FILENAMES:
        # Always utf-8 for console, unless explicitly disabled
        if not CONFIG.ansi_console:
            return "utf-8"
        # Otherwise, try known ansi encodings
        if lang in ANSI_ENCODINGS:
            return ANSI_ENCODINGS[lang]

    if filename in UTF_FILENAMES:
        encoding = "utf-8"

    utf_name = re.compile(r".*_ee\.tra$")
    if utf_name.match(filename):
        encoding = "utf-8"

    return encoding


def transliterate(text, rules):
    """
    For Vietnamese encoding handling.
    """
    text = unicodedata.normalize("NFD", text)
    for decomposed, precomposed in rules.items():
        text = text.replace(decomposed, precomposed)
    return text


# Not sure if this works correctly.
# Linked answer uses PyICU, but that requires building c++ extensions, might be hard on windows.
# So we're using transliterate instead.
def encode_vietnamese(text: str) -> str:
    """
    Vietnamese requires special handling.
    See https://stackoverflow.com/questions/58661415/python-how-can-i-print-cp1258-vietnamese-characters-correctly/78176520#78176520
    """
    text = transliterate(text, TRANSLITERATION_RULES_VIETNAMESE)
    return text.encode("cp1258", "replace").decode("cp1258")


def encode_custom(text: str, encoding: str = "utf-8") -> str:
    """
    Encodes and decodes the given text using the specified encoding,
    replacing invalid characters.
    If encoding is 'cp1258', it uses the encode_vietnamese function.
    """
    if encoding == "cp1258":
        return encode_vietnamese(text)
    else:
        # Graceful fallback for replace, can't really protect against invalid characters being entered in Weblate?
        return text.encode(encoding, "replace").decode(encoding)
