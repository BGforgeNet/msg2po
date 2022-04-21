import re
import sys
import collections
import polib
import os
import shutil
from contextlib import contextmanager
from multiprocessing import cpu_count
import natsort
from config import CONFIG
from datetime import datetime

# extensions recognized by file2po, etc
VALID_EXTENSIONS = ["msg", "txt", "sve", "tra"]


# supported file formats
# pattern is used to parse original files
# line_format to write to translated files
# index, value, context, female - order of these tokens in pattern
# dotall - whether file entries are multiline
FILE_FORMAT = {
    "msg": {
        "pattern": "{(\d+)}{([^}]*)}{([^}]*)}",
        "dotall": True,
        "index": 0,
        "value": 2,
        "context": 1,
        "line_format": {
            "default": "{{{index}}}{{}}{{{value}}}\n",
            "context": "{{{index}}}{{{context}}}{{{value}}}\n",
            "female": "separate",
        },
    },
    "sve": {
        "pattern": "(\d+):(.*)",
        "dotall": False,
        "index": 0,
        "value": 1,
        "line_format": {
            "default": "{index}:{value}\n",
            "female": "separate",
        },
    },
    "txt": {
        "pattern": "(\d+):(.*)",
        "dotall": False,
        "index": 0,
        "value": 1,
        "comment": "indexed_txt",
        "line_format": {
            "default": "{index}:{value}\n",
            "female": "separate",
        },
    },
    "tra": {
        "pattern": "@(\d+)\s*?=\s*?~([^~]*?)~(?:\s)?(?:\[([^]]*)\])?(?:~([^~]*)~)?",
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
    },
}


# used for determining empty strings, which are invalid by PO spec
empty_comment = "LEAVE empty space in translation"

# po: new translations added through weblate use case sensitive code: pt_BR.po. Keeping them.
lowercase_exclude = [".git", ".svn", ".hg", "README.md", "po"]

CONTEXT_FEMALE = "female"


# file and dir manipulation
#################################
def get_ext(path):
    try:
        ext = path.rsplit(".", 1)[1].lower()
    except:
        ext = None
    return ext


def basename(path):
    if path.endswith(os.sep):
        path = path[:-1]
    return os.path.abspath(path).rsplit(os.sep, 1)[1]


def parent_dir(path):
    if path.endswith(os.sep):
        path = path[:-1]
    return os.path.abspath(path).rsplit(os.sep, 1)[0]


def strip_ext(filename):
    return filename.rsplit(".", 1)[0]


def get_dir(path):
    return path.rsplit(os.sep, 1)[0]


def create_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


# lowercase directory
def lowercase_rename(root_dir, items):
    for item in items:
        old_name = os.path.join(root_dir, item)
        new_name = os.path.join(root_dir, item.lower())
        if new_name != old_name:
            print("renaming {} to {}".format(old_name, new_name))
            os.rename(old_name, new_name)


def lowercase_recursively(dir):  # this is the function that is actually used
    for dir_name, subdir_list, file_list in os.walk(dir, topdown=False):
        subdir_list[:] = [d for d in subdir_list if d not in lowercase_exclude]
        for sd in subdir_list:
            for dname, sdir_list, file_list in os.walk(sd, topdown=False):
                lowercase_rename(dir_name, file_list)
                lowercase_rename(dir_name, sdir_list)
    # why is this separate?
    children = os.listdir(dir)
    children[:] = [c for c in children if c not in lowercase_exclude]
    with cd(dir):
        for c in children:
            new_c = c.lower()
            if c != new_c:
                print("renaming {} to {}".format(c, new_c))
                os.rename(c, new_c)


def dir_or_exit(d):
    if os.path.isdir(d):
        print("Found directory {}".format(d))
    else:
        print("Directory {} does not exist, cannot continue!".format(d))
        sys.exit(1)


# returns list of extensions for which a separate female package should be prepared
def separate_file_formats():
    extensions = []
    for ff in FILE_FORMAT:
        if "female" in FILE_FORMAT[ff]["line_format"] and FILE_FORMAT[ff]["line_format"]["female"] == "separate":
            extensions.append(ff)
    return extensions


# check if need to make female package
def need_female_package(file_list):
    need_female = False
    ext_list = separate_file_formats()
    for f in file_list:
        ext = get_ext(f)
        if ext in ext_list:
            need_female = True
            break
    return need_female


@contextmanager
def cd(newdir):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)


def threads_number(max=False):
    if max:
        return cpu_count()
    tnum = cpu_count() - 2
    if tnum < 1:
        tnum = 1
    return tnum


def get_enc(po_path: str = "", file_path: str = ""):
    """
    Returns encoding based on PO and file path
    """
    ENCODINGS = {
        "schinese": "cp936",
        "tchinese": "cp950",
        "czech": "cp1250",
        "japanese": "cp932",
        "korean": "cp949",
        "polish": "cp1250",
        "polski": "cp1250",
        "russian": "cp1251",
        "ukrainian": "cp1251",
    }

    DOS_ENCODINGS = {
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

    DOS_FILENAMES = [
        "setup.tra",
        "install.tra",
    ]

    UTF_FILENAMES = [
        "ee.tra",
    ]

    encoding = CONFIG.encoding
    lang = strip_ext(basename(po_path))
    filename = basename(file_path)
    if lang in ENCODINGS:
        encoding = ENCODINGS[lang]

    if filename in DOS_FILENAMES:
        try:
            encoding = DOS_ENCODINGS[lang]
        except:
            pass

    if filename in UTF_FILENAMES:
        encoding = "utf-8"

    utf_name = re.compile(".*_ee.tra$")
    if utf_name.match(filename):
        encoding = "utf-8"

    return encoding


################################


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
            "X-Generator": "bgforge_po v.{}".format(CONFIG.version),
        }
        if pot:
            data["POT-Creation-Date"] = datetime.today().strftime("%Y-%m-%d-%H:%M") + "+0000"
        if po:
            data["PO-Revision-Date"] = datetime.today().strftime("%Y-%m-%d-%H:%M") + "+0000"
    else:
        return old_metadata
    return data


# returns PO file object
def file2po(filepath, encoding=CONFIG.encoding):

    trans = TRANSFile(filepath=filepath, is_source=True, encoding=encoding)  # load translations

    po = polib.POFile()
    po.metadata = metadata()

    trans_map = {}
    i = 0  # index in PO object
    for t in trans:
        index = t["index"]
        value = t["value"]
        context = t["context"]
        comment = t["comment"]

        # append to occurrences if id and context match
        if (value, context) in trans_map:
            e = po[trans_map[(value, context)]]
            e.occurrences.append((filepath, index))
            continue

        # no matching msgid + msgctxt, add new entry
        entry = polib.POEntry(
            msgid=value,
            msgstr="",
            occurrences=[
                (filepath, index),
            ],
            msgctxt=context,
            comment=comment,
        )
        po.append(entry)
        trans_map[(value, context)] = i
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
        print("{} is not present in selected PO file".format(path))
        print("supply one of present files with --path argument:")
        for pf in present_files_list:
            print(pf)
        sys.exit(1)


# return dict of dicts mapping filepaths to entries/occurrences where they are present
# {} file_path: {unit_index: entry_index, unit2_index: entry2_index, ...},  }
# entry_index is index in PO file (list)
def get_po_occurrence_map(po):
    ocmap = {}
    i = 0
    for entry in po:
        if entry.msgctxt == "female":  # pass female strings
            continue

        for eo in entry.occurrences:
            if eo[0] in ocmap:
                ocmap[eo[0]][int(eo[1])] = i
            else:
                ocmap[eo[0]] = {int(eo[1]): i}
        i = i + 1
    return ocmap


def po2file(epo, output_file, encoding, occurrence_path, dst_dir=None, newline="\r\n", occurrence_map=None):
    """
    Extract and write to disk a single file from EPO object
    epo is EPO object
    output_file is path relative to dst_dir
    dst_dir is actually dst language. Used only in unpoify
    """
    if occurrence_map is None:  # when extracting single file with po2tra/po2msg, etc
        # check if file is present in po, exit if not
        check_path_in_po(epo.po, occurrence_path)
        occurrence_map = get_po_occurrence_map(epo.po)

    # create parent directory
    create_dir(get_dir(output_file))

    ext = get_ext(output_file)
    ff = FILE_FORMAT[ext]
    line_format = ff["line_format"]

    po = epo.po

    context = ""
    resulting_entries = []
    extract_fuzzy = CONFIG.extract_fuzzy  # extract fuzzy? config flag

    for i in occurrence_map[occurrence_path]:
        entry = po[occurrence_map[occurrence_path][i]]
        index = i
        if entry.msgstr == "":  # if not translated, keep msgid
            value = entry.msgid
        elif "fuzzy" in entry.flags and not extract_fuzzy:  # skip fuzzy?
            value = entry.msgid
        else:
            value = entry.msgstr  # either translated or fuzzy+extract_fuzzy

        # empty lines detected by comment
        if entry.comment == empty_comment:
            value = ""

        # context
        context = entry.msgctxt
        # female strings
        if entry.msgid in epo.female_strings:
            female = epo.female_strings[entry.msgid]
        else:
            female = None

        resulting_entries.append({"index": index, "value": value, "female": female, "context": context})

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
        lines.append(line.encode(encoding, "replace").decode(encoding))

        # add string to female package if needed
        if "female" in line_format and line_format["female"] == "separate":
            if res["female"] is not None:
                female_line = lfrm.format(index=res["index"], value=res["female"], context=res["context"])
            else:
                female_line = lfrm.format(index=res["index"], value=res["value"], context=res["context"])
            lines_female.append(female_line.encode(encoding, "replace").decode(encoding))

    # write main package
    with open(output_file, "w", encoding=encoding, newline=newline) as file:
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

        if female_file is False:  # don't need to copy, automatic fallback
            print("Female strings are same, not copying - sfall will fallback to male {}".format(output_file))
            return True  # cutoff the rest of the function

        # If need to create the file
        if same:  # if female translation is the same?
            print("Female strings are same, copying to {}".format(female_file))
            copycreate(output_file, female_file)
        else:  # if it's different, extract separately
            print("Also extracting female counterpart into {}".format(female_file))
            create_dir(get_dir(female_file))  # create dir if not exists
            with open(female_file, "w", encoding=encoding, newline=newline) as file2:
                file2.writelines(lines_female)


# nasty hack for sfall's female strings placement
def get_female_filepath(path, dst_dir, same):
    # default: just add _female suffix
    female_path = path.replace(dst_dir + os.sep, dst_dir + CONFIG.female_dir_suffix + os.sep)
    if CONFIG.extract_format == "sfall":
        female_path = False  # default for sfall: don't copy, it will fallback to male
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
    if e["context"] is not None:  # entry with context
        lfrm = line_format["context"]
    elif (
        "female" in e and e["female"] is not None and "female" in line_format and line_format["female"] != "separate"
    ):  # format with native support for female strings
        lfrm = line_format["female"]
    else:  # no context and no female, or format without native support for female strings
        lfrm = line_format["default"]
    return lfrm


def copycreate(src_file, dst_file):
    dirname = os.path.dirname(dst_file)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    shutil.copyfile(src_file, dst_file)


# returns PO file object
def file2msgstr(input_file, epo, path, encoding=CONFIG.encoding, overwrite=True):
    trans = TRANSFile(filepath=input_file, encoding=encoding)  # load translations

    # map entries to occurrences for faster access, part 1
    entries_dict = collections.OrderedDict()
    po = epo.po
    for e in po:
        for eo in e.occurrences:
            entries_dict[(eo[0], eo[1])] = e

    for t in trans:
        index = t["index"]
        value = t["value"]
        context = t["context"]
        female = t["female"]

        if value is not None and value != "":
            if (path, index) in entries_dict:
                # map entries to occurrences for faster access, part 2
                e2 = entries_dict[(path, index)]

                # if overwrite is disabled and translation exists, skip
                if e2.msgstr is not None and e2.msgstr != "" and overwrite is False and e2.msgstr != value:
                    print(
                        "INFO: overwrite disabled,"
                        "translation already exists for {}, skipping:\n   ORIG: {}\n    OLD: {}\n    NEW: {}".format(
                            e2.occurrences[0], e2.msgid, e2.msgstr, value
                        )
                    )
                    continue

                if e2.msgstr is not None and e2.msgstr != "" and e2.msgstr != value:
                    print(
                        "WARN: different translations found for {}."
                        "Replacing first string with second:\n      {}\n      {}".format(
                            e2.occurrences, e2.msgstr, value
                        )
                    )

                if e2.msgid == value:
                    print(
                        "WARN: string and translation are the same for {}. Using it regardless:\n      {}".format(
                            e2.occurrences, e2.msgid
                        )
                    )
                e2.msgstr = value

                e2.msgctxt = context

                if female is not None:
                    epo.female_strings[e2.msgid] = female

            else:
                print("WARN: no msgid found for {}:{}, skipping string\n      {}".format(path, index, value))
    return epo


# check if TXT file is indexed
def is_indexed(txt_filename: str, encoding=CONFIG.encoding):
    f = open(txt_filename, "r", encoding=encoding)
    # count non-empty lines
    num_lines = sum(1 for line in f if line.rstrip())
    f.close()

    # count lines that are indexed
    pattern = FILE_FORMAT["txt"]["pattern"]
    f = open(txt_filename, "r", encoding=encoding)
    text = f.read()
    indexed_lines = re.findall(pattern, text)
    num_indexed_lines = len(indexed_lines)
    f.close()
    if num_lines == num_indexed_lines:
        return True
    else:
        return False


def sort_po(po: polib.POFile):
    for e in po:
        e.occurrences = natsort.natsorted(e.occurrences, key=lambda k: (k[0], k[1]))
    metadata = po.metadata
    po = natsort.natsorted(
        po, key=lambda k: k.occurrences[0] if len(k.occurrences) > 0 else ("zzz", "999")
    )  # female empty occurences hack
    po2 = polib.POFile()
    po2.metadata = metadata
    po2.extend(po)
    return po2


def po_make_unique(po):
    entries_dict = collections.OrderedDict()
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
    po2 = polib.POFile()
    po2.metadata = old_metadata
    for key, value in list(entries_dict.items()):
        po2.append(value)
    return po2


class TRANSFile(list):
    """
    Common translation class, holding translation entries as a list of dictionaries
    entry format:
      index
      value
      context
      female
      comment
    All set to None if not present
    """

    def __init__(self, *args, **kwargs):
        list.__init__(self)
        # the opened file handle
        filepath = kwargs.get("filepath", None)
        is_source = kwargs.get(
            "is_source", False
        )  # distinguish source TRAs to allow empty comment to be set on empty strings
        # the file encoding
        encoding = kwargs.get("encoding", CONFIG.encoding)
        fext = get_ext(filepath)

        text = open(filepath, "r", encoding=encoding).read()

        self.fformat = FILE_FORMAT[fext]
        pattern = self.fformat["pattern"]
        dotall = self.fformat["dotall"]
        try:  # comment for all entries in file
            self.comment = self.fformat["comment"]
        except:
            pass

        if dotall is True:
            lines = re.findall(pattern, text, re.DOTALL)
        else:
            lines = re.findall(pattern, text)

        # protection again duplicate indexes, part 1
        seen = []

        for line in lines:
            entry = {}

            # index and value
            index = line[self.fformat["index"]]
            entry["value"] = str(line[self.fformat["value"]])

            # skip invalid '000' entries in MSG files
            if fext == "msg" and index == "000":
                print(
                    "WARN: {} - invalid entry number found, skipping:\n     {{000}}{{}}{{{}}}".format(
                        filepath, entry["value"]
                    )
                )
                continue

            entry["index"] = line[self.fformat["index"]]

            # comment
            # 1. generic comment for all entries in file
            try:
                entry["comment"] = self.fformat["comment"]
            except:
                entry["comment"] = None
            # 2. handle empty lines in source files
            if entry["value"] == "":
                if is_source is True:
                    entry["value"] = " "
                    entry["comment"] = empty_comment

            # context
            try:
                entry["context"] = line[self.fformat["context"]]
            except:
                entry["context"] = None
            if entry["context"] == "":
                entry["context"] = None

            # female
            entry["female"] = None  # default
            if fext == "tra":  # TRA file specific
                try:
                    entry["female"] = str(line[self.fformat["female"]])
                except:
                    pass
                if entry["female"] == "":
                    entry["female"] = None

            # protection against duplicate indexes, part 2
            if (entry["index"]) in seen:
                print(
                    "WARN: duplicate string definition found {}:{}, using new value:\n      {}".format(
                        filepath, entry["index"], entry["value"]
                    )
                )
                self[:] = [entry if x["index"] == entry["index"] else x for x in self]
                continue
            else:
                seen.append(index)

            # produce the final list of strings
            if entry["value"] is not None and entry["value"] != "":
                self.append(entry)


class EPOFile(polib.POFile):
    """
    Extended PO file class, handling female mgctxt entries
    """

    def __init__(self, *args):
        po = args[0]
        self.female_strings = {}
        if po:
            self.po = polib.pofile(po)
            self.load_female()
        else:
            self.po = polib.POFile()
            self.po.metadata = metadata(po=True)

    def load_female(self):
        female_entries = [e for e in self.po if e.msgctxt == "female"]
        for fe in female_entries:
            extract_fuzzy = CONFIG.extract_fuzzy  # extract fuzzy? config flag
            if "fuzzy" in fe.flags and not extract_fuzzy:  # skip fuzzy?
                value = fe.msgid
            else:
                value = fe.msgstr  # either translated or fuzzy+extract_fuzzy
            self.female_strings[fe.msgid] = value

    def save(self, output_file):
        self.po.save(output_file)


def simple_lang_slug(po_filename):
    """
    Allows to extract PO files into simplified language names: pt_BR.po -> portuguese/1.msg.
    Working with language codes is not convenient in mods.
    A temporary hack until a better solution is found.
    """
    slug_map = {
        "de": "german",
        "fr": "french",
        "pt_br": "portuguese",
        "it": "italian",
        "pl": "polish",
        "es": "spanish",
        "ru": "russian",
        "uk": "ukrainian",
    }
    slug = strip_ext(po_filename).lower()
    if CONFIG.simple_languages:
        try:
            slug = slug_map[slug]
        except:
            pass
    return slug


def restore_female_entries(po: polib.POFile):
    """
    Unobsoletes and if necessary (un)fuzzies female strings that have a corresponding male counterpart.
    (Male = no context)
    """
    male_entries = {x.msgid: x for x in po if not x.previous_msgid and (x.msgctxt is None)}
    fuzzy_male_entries = {x.previous_msgid: x for x in po if x.previous_msgid and (x.msgctxt is None)}
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

        # if a fuzzy male string was found, fixing female to have the same attributes
        if (e.msgid not in male_entries) and (e.msgid in fuzzy_male_entries):
            male_entry = fuzzy_male_entries[e.msgid]
            e.msgid = male_entry.msgid
            e.previous_msgid = male_entry.previous_msgid
            if "fuzzy" not in e.flags:
                e.flags.append("fuzzy")
            e.obsolete = False
    return po
