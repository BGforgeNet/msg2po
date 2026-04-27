# PO line wrapping that matches Weblate's translate-toolkit output.
#
# PROBLEM:
#   Weblate saves PO files through translate-toolkit, which wraps lines
#   differently from polib (used by msg2po). Without this patch, every
#   roundtrip (poify/unpoify/dir2msgstr) re-wraps the entire PO file,
#   producing huge diffs of pure formatting noise.
#
# SOLUTION:
#   Monkey-patch polib to match translate-toolkit's wrapping exactly.
#   Combined with po_content_snapshot() (in po_utils.py), PO files are
#   only saved when actual content changes, never for wrapping-only diffs.
#
# VERSION DEPENDENCY:
#   This module matches translate-toolkit 3.6.2 (Weblate's version as of
#   2026-03). The wrapping behavior differs between translate-toolkit versions:
#   - The wordsep_re regex changed between 3.6.2 and 3.16.3
#   - The wrap width and split threshold logic may also change
#   When upgrading Weblate/translate-toolkit, verify wrapping still matches:
#   1. Save a PO via Weblate (make a trivial translation edit)
#   2. Run poify/unpoify roundtrip
#   3. Check git diff — should be clean (no wrapping changes)
#   If wrapping diverges, compare translate-toolkit's pypo.py PoWrapper class
#   against this module and update _WORDSEP_RE / GettextWrapper accordingly.
#
# KEY DIFFERENCES FROM POLIB DEFAULTS:
#   1. Width 77 instead of 78
#      - Weblate's translate-toolkit uses 77 (po_line_wrap default)
#      - polib uses 78
#   2. Trailing whitespace placement
#      - translate-toolkit: trailing space stays on current line ("word \n")
#      - polib/textwrap: trailing space moves to next line ("word\n ")
#      - This is controlled by the wordsep_re pattern [\w...]+\s+ which
#        groups a word with its trailing whitespace as a single chunk
#   3. Split-into-continuation threshold
#      - translate-toolkit: len(escaped) > width - 6, or multiple \n segments
#      - polib: len(field) > wrapwidth - fieldname_len - 3
#   4. Wrapping algorithm
#      - translate-toolkit: escape -> split on \n -> reattach \n -> wrap each
#      - polib: wrap entire field, then split on \n
#
# POLIB DEPENDENCY:
#   Patches polib._BaseEntry._str_field (private API). May break on polib
#   upgrades. Currently tested with polib 2.x.

import re
import textwrap

import polib

# Default width matching Weblate's translate-toolkit default (po_line_wrap=77)
WRAP_WIDTH = 77

# Word separator regex matching translate-toolkit 3.6.2's PoWrapper.
# Key pattern: [\w\!\'\&\.\,\?=<>%]+\s+ keeps trailing space with the word,
# while plain \s+ handles standalone whitespace between other tokens.
_WORDSEP_RE = re.compile(
    r"""
        (
        \s+|                                  # any whitespace
        [a-z0-9A-Z_-]+/|                      # nicely split long URLs
        \w*\\.\w*|                            # any escape should not be split
        n(?=%)|                               # wrap inside plural equation
        \.(?=\w)|                             # full stop inside word
        [\w\!\'\&\.\,\?=<>%]+\s+|             # space should go with a word
        [^\s\w]*\w+[a-zA-Z]-(?=\w+[a-zA-Z])|  # hyphenated words
        (?<=[\w\!\"\'\&\.\,\?])-{2,}(?=\w)    # em-dash
        )
    """,
    re.VERBOSE,
)


class GettextWrapper(textwrap.TextWrapper):
    """
    TextWrapper that keeps trailing whitespace on the current line.
    Reimplements _wrap_chunks to match gettext wrapping convention:
    greedily fills lines, treating trailing whitespace as part of the
    preceding word.
    """

    wordsep_re = _WORDSEP_RE

    def __init__(self, width=WRAP_WIDTH):
        super().__init__(
            width=width,
            drop_whitespace=False,
            break_long_words=False,
            expand_tabs=False,
            replace_whitespace=False,
        )

    def _wrap_chunks(self, chunks):
        """Greedily fill lines, keeping trailing spaces on current line."""
        lines = []
        chunks.reverse()

        while chunks:
            cur_line = []
            cur_len = 0

            while chunks:
                chunk = chunks[-1]
                chunk_len = len(chunk)
                if cur_len + chunk_len <= self.width:
                    cur_line.append(chunks.pop())
                    cur_len += chunk_len
                else:
                    break

            if not cur_line and chunks:
                # Force at least one chunk per line (long word)
                cur_line.append(chunks.pop())

            if cur_line:
                lines.append("".join(cur_line))
        return lines


def apply_to_polib():
    """
    Monkey-patch polib to match Weblate's wrapping:
    - wrapwidth 77 (instead of 78)
    - Trailing whitespace on current line (gettext convention)
    Call this once at import time.
    """

    def _str_field_patched(self, fieldname, delflag, plural_index, field, wrapwidth=78):
        # Default 78 matches polib's original signature; the wrapwidth-77 override
        # is applied via POFile.wrapwidth in the __init__ patch below, so callers
        # always pass an explicit value and this default is unused.
        raw_lines = field.splitlines(True)
        if len(raw_lines) > 1 and all(line.endswith("\n") for line in raw_lines):
            # Multi-line field where every line ends with \n (metadata header).
            # Preserve original lines as-is, no wrapping needed.
            lines = [""] + raw_lines
        else:
            escaped_field = polib.escape(field)

            # Split threshold matches translate-toolkit's quoteforpo:
            # split into "" + continuation when content is long or multi-line
            segments = escaped_field.split("\\n")
            num_segments = len(segments)
            needs_split = num_segments > 2 or (num_segments == 2 and segments[1]) or len(segments[0]) > wrapwidth - 6
            if wrapwidth > 0 and needs_split:
                # Match translate-toolkit's quoteforpo algorithm:
                # 1. Split escaped text on \n boundaries (already done above)
                # 2. Re-attach \n to end of each segment (except last)
                # 3. Wrap each segment individually
                wrapper = GettextWrapper(width=wrapwidth)
                for i in range(num_segments - 1):
                    segments[i] = segments[i] + "\\n"
                lines = [""]
                for segment in segments:
                    wrapped = wrapper.wrap(segment)
                    for w in wrapped:
                        lines.append(polib.unescape(w))
            else:
                lines = [field]

        if fieldname.startswith("previous_"):
            fieldname = fieldname[9:]

        ret = [f'{delflag}{fieldname}{plural_index} "{polib.escape(lines.pop(0))}"']
        for line in lines:
            ret.append(f'{delflag}"{polib.escape(line)}"')
        return ret

    # Monkey-patching polib internals. ty rejects these assignments because the
    # class-level / module-level attributes are typed against the originals;
    # the replacement signatures are compatible at runtime.
    polib._BaseEntry._str_field = _str_field_patched  # ty: ignore[invalid-assignment]

    # Override default wrapwidth from 78 to 77 for all POFile instances
    _original_pofile = polib.pofile

    def _pofile_patched(pofile, **kwargs):
        po = _original_pofile(pofile, **kwargs)
        if po.wrapwidth == 78:
            po.wrapwidth = WRAP_WIDTH
        return po

    polib.pofile = _pofile_patched  # ty: ignore[invalid-assignment]

    _original_init = polib.POFile.__init__

    def _pofile_init_patched(self, *args, **kwargs):
        _original_init(self, *args, **kwargs)
        if self.wrapwidth == 78:
            self.wrapwidth = WRAP_WIDTH

    polib.POFile.__init__ = _pofile_init_patched  # ty: ignore[invalid-assignment]
