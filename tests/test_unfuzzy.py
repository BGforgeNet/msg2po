# Tests for unfuzzy logic.
# The pure functions from unfuzzy.py are reimplemented here for isolated testing.
# unfuzzy_exact_matches is tested via po_utils.

import os

import polib
import ruamel.yaml

from msg2po.po_utils import unfuzzy_exact_matches


# Reimplementations of the pure functions from unfuzzy.py, since that module
# cannot be imported without triggering argparse.parse_args() at module level.
def make_replaces(line, replace_list):
    for r in replace_list:
        line = line.replace(r[0], r[1])
    return line


def msgids_equal(id1, id2, replace_list):
    id1 = make_replaces(id1, replace_list)
    id2 = make_replaces(id2, replace_list)
    return id1 == id2


def load_replacements():
    yml = os.path.join(os.path.dirname(os.path.dirname(__file__)), "msg2po", "unfuzzy.yml")
    with open(yml, encoding="utf-8") as yf:
        yaml = ruamel.yaml.YAML()
        replace_list = yaml.load(yf)
    return replace_list


class TestMakeReplaces:
    def test_single_replacement(self):
        result = make_replaces("Nuka Cola", [["Nuka Cola", "Nuka-Cola"]])
        assert result == "Nuka-Cola"

    def test_multiple_replacements(self):
        replacements = [["OK", "okay"], ["Good bye", "Goodbye"]]
        result = make_replaces("OK and Good bye", replacements)
        assert result == "okay and Goodbye"

    def test_no_match(self):
        result = make_replaces("Hello world", [["foo", "bar"]])
        assert result == "Hello world"


class TestMsgidsEqual:
    def test_equal_after_replacement(self):
        replacements = [["Nuka Cola", "Nuka-Cola"]]
        assert msgids_equal("Nuka Cola", "Nuka-Cola", replacements) is True

    def test_not_equal(self):
        replacements = [["Nuka Cola", "Nuka-Cola"]]
        assert msgids_equal("Something else", "Nuka-Cola", replacements) is False

    def test_case_sensitive(self):
        replacements = [["nuka cola", "Nuka-Cola"]]
        assert msgids_equal("Nuka Cola", "Nuka-Cola", replacements) is False


class TestLoadReplacements:
    def test_loads_default_file(self):
        replacements = load_replacements()
        assert isinstance(replacements, list)
        assert len(replacements) > 0
        assert ["Good bye", "Goodbye"] in replacements


class TestUnfuzzyExactMatches:
    def test_unfuzzies_exact_match(self):
        po = polib.POFile()
        entry = polib.POEntry(
            msgid="Hello world",
            msgstr="Bonjour le monde",
            occurrences=[("file.msg", "100")],
        )
        entry.flags.append("fuzzy")
        entry.previous_msgid = "Hello world"
        po.append(entry)

        result = unfuzzy_exact_matches(po)
        assert "fuzzy" not in result[0].flags
        assert result[0].previous_msgid is None

    def test_keeps_fuzzy_when_different(self):
        po = polib.POFile()
        entry = polib.POEntry(
            msgid="Hello world",
            msgstr="Bonjour le monde",
            occurrences=[("file.msg", "100")],
        )
        entry.flags.append("fuzzy")
        entry.previous_msgid = "Hello everyone"
        po.append(entry)

        result = unfuzzy_exact_matches(po)
        assert "fuzzy" in result[0].flags

    def test_unfuzzies_with_matching_context(self):
        po = polib.POFile()
        entry = polib.POEntry(
            msgid="Hello",
            msgstr="Bonjour",
            msgctxt="greeting",
            occurrences=[("file.msg", "100")],
        )
        entry.flags.append("fuzzy")
        entry.previous_msgid = "Hello"
        entry.previous_msgctxt = "greeting"
        po.append(entry)

        result = unfuzzy_exact_matches(po)
        assert "fuzzy" not in result[0].flags
