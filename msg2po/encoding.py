# Encoding detection and transcoding for game translation files.
# Handles per-language encoding lookup, Vietnamese transliteration,
# and console/UTF-8 filename overrides.

import re
import unicodedata
from pathlib import Path

from msg2po.config import CONFIG


def _build_cp1258_transliteration_rules() -> dict[str, str]:
    """
    Build transliteration rules from the cp1258 encoding table.
    cp1258 uses a mix of precomposed characters and combining marks.
    This finds all precomposed characters that cp1258 can encode as single bytes,
    plus Vietnamese-specific multi-char sequences (vowel + dot below + diacritic).
    After NFD decomposition, these rules recompose exactly the characters that
    cp1258 expects precomposed, leaving tone marks as combining characters.
    """
    rules = {}
    for byte_val in range(0x80, 0x100):
        try:
            char = bytes([byte_val]).decode("cp1258")
            nfd = unicodedata.normalize("NFD", char)
            if len(nfd) > 1:
                rules[nfd] = char
        except (UnicodeDecodeError, ValueError):
            pass

    # Vietnamese vowel + dot below + diacritic sequences.
    # These appear in NFD as base + combining_mark + dot_below,
    # but cp1258 encodes them as precomposed_vowel + dot_below.
    viet_dot_below = {
        "a\u0323\u0306": "\u0103\u0323",  # ặ
        "A\u0323\u0306": "\u0102\u0323",  # Ặ
        "a\u0323\u0302": "\u00e2\u0323",  # ậ
        "A\u0323\u0302": "\u00c2\u0323",  # Ậ
        "e\u0323\u0302": "\u00ea\u0323",  # ệ
        "E\u0323\u0302": "\u00ca\u0323",  # Ệ
        "o\u0323\u0302": "\u00f4\u0323",  # ộ
        "O\u0323\u0302": "\u00d4\u0323",  # Ộ
    }
    rules.update(viet_dot_below)
    return rules


TRANSLITERATION_RULES_VIETNAMESE = _build_cp1258_transliteration_rules()

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


_UTF_NAME_RE = re.compile(r".*_ee\.tra$")


def get_enc(lang_path: str = "", file_path: str = "") -> str:
    """
    Infers encoding based on dir/PO name and file path.
    lang_path can be PO path or translation path, only basename is used.
    """
    from msg2po.languages import language_slug

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

    if _UTF_NAME_RE.match(filename):
        encoding = "utf-8"

    return encoding


def transliterate(text, rules):
    """
    Converts NFC Unicode text to the mixed normalization form that cp1258 expects.
    NFD decomposes everything, then rules selectively recompose characters that
    cp1258 can encode as single bytes. Longer sequences are matched first.
    """
    text = unicodedata.normalize("NFD", text)
    for decomposed, precomposed in sorted(rules.items(), key=lambda x: len(x[0]), reverse=True):
        text = text.replace(decomposed, precomposed)
    return text


def encode_vietnamese(text: str) -> str:
    """
    Vietnamese cp1258 uses a mix of precomposed vowels and combining tone marks.
    Python's cp1258 codec decodes into this exact mixed form, so text that originated
    from cp1258 round-trips correctly without any normalization.

    For text from other sources (e.g. PO files with NFC Unicode), we must first
    decompose to NFD, then recompose only the vowels that cp1258 expects precomposed,
    leaving tone marks as combining characters.

    See https://stackoverflow.com/questions/58661415/python-how-can-i-print-cp1258-vietnamese-characters-correctly/78176520#78176520
    """
    text = transliterate(text, TRANSLITERATION_RULES_VIETNAMESE)
    return text.encode("cp1258", "replace").decode("cp1258")


def encode_custom(text: str, encoding: str = "utf-8") -> str:
    """
    Encodes and decodes the given text using the specified encoding,
    replacing invalid characters.
    If encoding is 'cp1258', it uses the encode_vietnamese function.
    UTF-8 is a passthrough since all Python strings are valid UTF-8.
    """
    if encoding == "utf-8":
        return text
    if encoding == "cp1258":
        return encode_vietnamese(text)
    # Graceful fallback for replace, can't really protect against invalid characters being entered in Weblate?
    return text.encode(encoding, "replace").decode(encoding)
