# Language slug mapping and PO-to-directory resolution.

import functools

from msg2po.common import find_files
from msg2po.config import CONFIG
from msg2po.core import basename, strip_ext

_SLUG_MAP = {
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


@functools.lru_cache(maxsize=64)
def language_slug(po_filename: str) -> str:
    """
    Allows to extract PO files into simplified language names: pt_BR.po -> portuguese/1.msg.
    Working with language codes is not convenient in mods.
    A temporary hack until a better solution is found.
    """
    slug = strip_ext(basename(po_filename)).lower()
    if CONFIG.simple_languages:
        slug = _SLUG_MAP.get(slug, slug)
    return slug


class LanguageMap:
    """
    Map PO basenames to language dir names, for unpoify and dir2msgstr.
    This is because languages added through Weblate use codes like pt_BR, see find_files.
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
