# PO file manipulation utilities: sorting, deduplication, female entry management,
# metadata generation, and fuzzy flag cleanup.

from collections import OrderedDict
from datetime import datetime

import polib
from natsort import natsorted

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
    i = 0
    for entry in po:
        for eo in entry.occurrences:
            path = eo[0]
            linenum = eo[1]
            if path in entries:
                entries[path].append({"file_index": int(linenum), "po_index": i})
            else:
                entries[path] = [{"file_index": int(linenum), "po_index": i}]
        i = i + 1
    return entries


def female_entries(po: polib.POFile) -> dict[str, polib.POEntry]:
    """
    Returns mapping of male msgids to corresponding female PO entries
    """
    entries = {}
    fe_list = [e for e in po if len(e.occurrences) == 0 and e.msgctxt == CONTEXT_FEMALE]
    for fe in fe_list:
        # first, check male entries without context
        male_entries = [e for e in po if e.msgid == fe.msgid and not e.msgctxt]
        if len(male_entries) > 0:
            me = male_entries[0]
        else:  # then, those with
            male_entries = [e for e in po if e.msgid == fe.msgid and e.msgctxt != CONTEXT_FEMALE]
        if len(male_entries) > 0:
            me = male_entries[0]
            entries[me.msgid] = fe
        else:
            print("WARNING: couldn't find a corresponding male counterpart for a female entry")
            print(fe)
    return entries


def sort_po(po: polib.POFile):
    for e in po:
        e.occurrences = natsorted(e.occurrences, key=lambda k: (k[0], k[1]))
    old_metadata = po.metadata
    po = natsorted(
        po, key=lambda k: k.occurrences[0] if len(k.occurrences) > 0 else ("zzzzz", "99999")
    )  # female empty occurrences hack
    po2 = _new_po_with_metadata(old_metadata)
    po2.extend(po)
    return po2


def po_make_unique(po):
    entries_dict = OrderedDict()
    old_metadata = po.metadata
    for e in po:
        if (e.msgid, e.msgctxt) in entries_dict:
            e0 = entries_dict[(e.msgid, e.msgctxt)]
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
            entries_dict[(e.msgid, e.msgctxt)] = e
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
            print(f"    Unfuzzied entry {e.occurrences}, exact match with previous")
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


def _new_po_with_metadata(old_metadata) -> polib.POFile:
    """Helper to create a new POFile preserving metadata."""
    po = polib.POFile()
    po.metadata = old_metadata
    return po
