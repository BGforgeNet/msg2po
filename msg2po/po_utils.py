# PO file manipulation utilities: sorting, deduplication, female entry management,
# metadata generation, and fuzzy flag cleanup.

from collections import OrderedDict, defaultdict
from datetime import datetime

import polib
from loguru import logger

from msg2po.config import CONFIG

# used for determining empty strings, which are invalid by PO spec
EMPTY_COMMENT = "LEAVE empty space in translation"

CONTEXT_FEMALE = "female"


def metadata(old_metadata=None, pot=False, po=False):
    if old_metadata is None:
        data = {
            "Project-Id-Version": "PACKAGE VERSION",
            "Report-Msgid-Bugs-To": "",
            "Last-Translator": "FULL NAME <EMAIL@ADDRESS>",
            "Language-Team": "LANGUAGE <LL@li.org>",
            "Language": "",
            "MIME-Version": "1.0",
            "Content-Type": "text/plain; charset=UTF-8",
            "Content-Transfer-Encoding": "8bit",
            "X-Generator": f"BGforge/msg2po v.{CONFIG.version}",
        }
        if pot:
            data["POT-Creation-Date"] = datetime.today().strftime("%Y-%m-%d-%H:%M") + "+0000"
        if po:
            data["PO-Revision-Date"] = datetime.today().strftime("%Y-%m-%d-%H:%M") + "+0000"
    else:
        return old_metadata
    return data


def translation_entries(po: polib.POFile):
    """
    returns {filepath: [{"file_index": index_in_file, "po_index": index_in_po}] }
    does not include female entries, as they don't have occurrences
    """
    entries = {}
    for i, entry in enumerate(po):
        for eo in entry.occurrences:
            path = eo[0]
            linenum = eo[1]
            if path in entries:
                entries[path].append({"file_index": int(linenum), "po_index": i})
            else:
                entries[path] = [{"file_index": int(linenum), "po_index": i}]
    return entries


def female_entries(po: polib.POFile) -> dict[tuple[str, str], polib.POEntry]:
    """
    Returns mapping of male occurrences to corresponding female PO entries.

    Female entries with explicit occurrences are scoped to those occurrences.
    Legacy female entries without occurrences are only mapped when they have
    exactly one possible male occurrence; ambiguous global matches are skipped.
    """
    male_occurrences: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for e in po:
        if e.msgctxt == CONTEXT_FEMALE:
            continue
        for occurrence in e.occurrences:
            male_occurrences[e.msgid].append(occurrence)

    entries = {}
    for e in po:
        if e.msgctxt != CONTEXT_FEMALE:
            continue
        if e.occurrences:
            for occurrence in e.occurrences:
                entries[occurrence] = e
            continue

        matches = male_occurrences.get(e.msgid, [])
        if len(matches) == 1:
            entries[matches[0]] = e
        elif len(matches) == 0:
            logger.warning(f"couldn't find a corresponding male counterpart for a female entry: {e}")
        else:
            logger.warning(f"ambiguous female entry without occurrences, skipping auto-match: {e.msgid}")
    return entries


def _occ_sort_key(occ: tuple[str, str]) -> tuple[str, int]:
    """Sort key for occurrence tuples: (filepath, line_number_str) -> (filepath, int)."""
    return (occ[0], int(occ[1]))


def sort_po(po: polib.POFile) -> polib.POFile:
    """Sort PO entries by occurrence (filepath, line number). Returns a new POFile."""
    for e in po:
        e.occurrences = sorted(e.occurrences, key=_occ_sort_key)
    old_metadata = po.metadata
    sorted_entries = sorted(po, key=lambda k: _occ_sort_key(k.occurrences[0]) if k.occurrences else ("zzzzz", 99999))
    po2 = _new_po_with_metadata(old_metadata)
    po2.extend(sorted_entries)
    return po2


def _clone_entry(e: polib.POEntry) -> polib.POEntry:
    """Create a shallow copy of a POEntry, cloning mutable fields."""
    clone = polib.POEntry(
        msgid=e.msgid,
        msgstr=e.msgstr,
        msgctxt=e.msgctxt,
        comment=e.comment,
        tcomment=e.tcomment,
        msgid_plural=e.msgid_plural,
        obsolete=e.obsolete,
        encoding=e.encoding,
    )
    clone.occurrences = list(e.occurrences)
    clone.flags = list(e.flags)
    clone.msgstr_plural = dict(e.msgstr_plural)
    clone.previous_msgctxt = e.previous_msgctxt
    clone.previous_msgid = e.previous_msgid
    clone.previous_msgid_plural = e.previous_msgid_plural
    return clone


def po_make_unique(po: polib.POFile) -> polib.POFile:
    """Deduplicate PO entries by (msgid, msgctxt), merging occurrences. Returns a new POFile.

    Non-duplicate entries are shared (not cloned) between input and output.
    Duplicate entries are cloned before merging to avoid mutating the originals.
    """
    entries_dict = OrderedDict()
    cloned = set()  # keys that have been cloned (due to duplicates)
    old_metadata = po.metadata
    for e in po:
        key = (e.msgid, e.msgctxt)
        if key in entries_dict:
            # Clone on first duplicate to avoid mutating the original entry
            if key not in cloned:
                entries_dict[key] = _clone_entry(entries_dict[key])
                cloned.add(key)
            e0 = entries_dict[key]
            e0.occurrences.extend(e.occurrences)

            if e.comment is not None:
                if e0.comment is None:
                    e0.comment = e.comment
                elif e0.comment != e.comment:
                    e0.comment = e0.comment + "; " + e.comment

            if e.tcomment is not None:
                if e0.tcomment is None:
                    e0.tcomment = e.tcomment
                elif e0.tcomment != e.tcomment:
                    e0.tcomment = e0.tcomment + "; " + e.tcomment

            for f in e.flags:
                if f not in e0.flags:
                    e0.flags.append(f)

            if e.previous_msgctxt and not e0.previous_msgctxt:
                e0.previous_msgctxt = e.previous_msgctxt
            if e.previous_msgid and not e0.previous_msgid:
                e0.previous_msgid = e.previous_msgid
            if e.previous_msgid_plural and not e0.previous_msgid_plural:
                e0.previous_msgid_plural = e.previous_msgid_plural

        else:
            entries_dict[key] = e
    po2 = _new_po_with_metadata(old_metadata)
    for _key, value in list(entries_dict.items()):
        po2.append(value)
    return po2


def update_female_entries(po: polib.POFile):
    """
    (Un)obsoletes and if necessary (un)fuzzies female strings that have a corresponding male counterpart.
    (Male = no context)
    """
    # this also includes fuzzies
    male_entries = {x.msgid: x for x in po if ((x.msgctxt != CONTEXT_FEMALE) and (not x.obsolete))}
    # and this is for matching male strings that were changed
    fuzzy_male_entries = {
        x.previous_msgid: x
        for x in po
        if ((x.previous_msgid is not None) and (x.msgctxt != CONTEXT_FEMALE) and (not x.obsolete))
    }

    for e in po.obsolete_entries():
        if e.msgctxt != CONTEXT_FEMALE:
            continue

        # if exact male match found, unobsolete
        if e.msgid in male_entries:
            male_entry = male_entries[e.msgid]
            # if it's fuzzy, doing the same for female
            e.previous_msgid = male_entry.previous_msgid
            e.flags = male_entry.flags
            e.obsolete = False

        # else, check if a fuzzy male match exists, and fix female to have the same attributes
        elif e.msgid in fuzzy_male_entries:
            male_entry = fuzzy_male_entries[e.msgid]
            e.msgid = male_entry.msgid
            e.previous_msgid = male_entry.previous_msgid
            if "fuzzy" not in e.flags:
                e.flags.append("fuzzy")
            e.obsolete = False

    # and delete female entries with no non-obsolete male match
    new_entries = [x for x in po if not (x.obsolete and (x.msgctxt == CONTEXT_FEMALE))]
    po2 = _new_po_with_metadata(po.metadata)
    for e in new_entries:
        po2.append(e)
    return po2


def unfuzzy_exact_matches(po: polib.POFile):
    """
    For some reason msgmerge won't clear fuzzy flag if source string is changed, then changed back:
    #: game/g_map_hotkey.msg:1
    #, fuzzy
    #| msgid "Nah... I think I'm gonna take the ladder."
    msgid "Nah... I think I'm gonna take the ladder."
    msgstr "Naa... Penso che prendero' la scala."

    This function unfuzzies such entries.
    """
    for e in po.fuzzy_entries():
        if (e.previous_msgid == e.msgid) and (e.previous_msgctxt == e.msgctxt):
            logger.info(f"Unfuzzied entry {e.occurrences}, exact match with previous")
            e.flags.remove("fuzzy")
            e.previous_msgid = None
            e.previous_msgctxt = None
    return po


def normalize_po(po: polib.POFile) -> polib.POFile:
    """
    Standard PO normalization pipeline: deduplicate, update female entries,
    unfuzzy exact matches, and sort.
    """
    po = po_make_unique(po)
    po = update_female_entries(po)
    po = unfuzzy_exact_matches(po)
    po = sort_po(po)
    return po


def po_content_snapshot(po: polib.POFile) -> set:
    """Snapshot PO entry content for change detection, ignoring formatting and order.

    Used together with po_wrap.py to avoid unnecessary PO re-saves: even if
    wrapping differs between polib and Weblate's translate-toolkit, we only
    save when entry data actually changes. This includes occurrences, since
    stale source locations must still trigger a rewrite.
    """
    return {
        (
            e.msgid,
            e.msgctxt,
            e.msgstr,
            tuple(sorted(e.msgstr_plural.items())),
            tuple(sorted(e.occurrences)),
            tuple(e.flags),
            e.obsolete,
        )
        for e in po
    }


def _new_po_with_metadata(old_metadata) -> polib.POFile:
    """Helper to create a new POFile preserving metadata."""
    po = polib.POFile()
    po.metadata = old_metadata
    return po
