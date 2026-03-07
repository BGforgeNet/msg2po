# Tests for file2po, po2file, and roundtrip conversions.

import polib
import pytest

from msg2po.core import (
    CONTEXT_FEMALE,
    EMPTY_COMMENT,
    female_entries,
    file2msgstr,
    file2po,
    po2file,
    po_make_unique,
    sort_po,
    translation_entries,
    update_female_entries,
)


class TestFile2Po:
    def test_msg_to_po(self, msg_file):
        po = file2po(msg_file, encoding="utf-8")
        assert len(po) == 4

    def test_msg_entry_values(self, msg_file):
        po = file2po(msg_file, encoding="utf-8")
        assert po[0].msgid == "Hello world"
        assert po[1].msgid == "How are you?"

    def test_msg_occurrences(self, msg_file):
        po = file2po(msg_file, encoding="utf-8")
        assert po[0].occurrences == [(msg_file, "100")]

    def test_msg_context_preserved(self, msg_file):
        po = file2po(msg_file, encoding="utf-8")
        assert po[2].msgctxt == "Some context"

    def test_msg_empty_entry_gets_comment(self, msg_file):
        po = file2po(msg_file, encoding="utf-8")
        assert po[3].msgid == " "
        assert po[3].comment == EMPTY_COMMENT

    def test_tra_to_po(self, tra_file):
        po = file2po(tra_file, encoding="utf-8")
        assert len(po) == 4

    def test_tra_context(self, tra_file):
        po = file2po(tra_file, encoding="utf-8")
        assert po[2].msgctxt == "SOME_CONTEXT"

    def test_sve_to_po(self, sve_file):
        po = file2po(sve_file, encoding="utf-8")
        assert len(po) == 3
        assert po[0].msgid == "Hello world"

    def test_txt_to_po(self, txt_indexed_file):
        po = file2po(txt_indexed_file, encoding="utf-8")
        assert len(po) == 3

    def test_duplicate_msgids_merge_occurrences(self, tmp_path):
        """Two entries with same value should be merged into one PO entry with two occurrences."""
        msg = tmp_path / "dup_val.msg"
        msg.write_text("{100}{}{Same text}\n{200}{}{Same text}", encoding="utf-8")
        po = file2po(str(msg), encoding="utf-8")
        assert len(po) == 1
        assert len(po[0].occurrences) == 2


class TestCheckPathInPo:
    def test_missing_path_raises(self, msg_file):
        po = file2po(msg_file, encoding="utf-8")
        with pytest.raises(FileNotFoundError, match="not present in selected PO file"):
            po2file(po, "nonexistent.msg", "utf-8", "nonexistent.msg")


class TestTRAFemaleContextConflict:
    def test_female_with_context_raises(self, tmp_path):
        """TRA entries with both female text and context are invalid."""
        # No space between context and female -- this is how the regex captures both
        tra = tmp_path / "bad.tra"
        tra.write_text("@100 = ~Hello~ [CTX]~Female~\n", encoding="utf-8")
        with pytest.raises(ValueError, match="female variants may not have context"):
            file2po(str(tra), encoding="utf-8")


class TestPo2File:
    def test_msg_roundtrip(self, msg_file, tmp_path):
        """MSG -> PO -> MSG roundtrip preserves content."""
        po = file2po(msg_file, encoding="utf-8")
        output = str(tmp_path / "output.msg")
        po2file(po, output, "utf-8", msg_file)

        with open(msg_file, encoding="utf-8") as f:
            original_lines = f.read().strip().splitlines()
        with open(output, encoding="utf-8") as f:
            output_lines = f.read().strip().splitlines()

        assert len(output_lines) == len(original_lines)

    def test_sve_roundtrip(self, sve_file, tmp_path):
        """SVE -> PO -> SVE roundtrip preserves content."""
        po = file2po(sve_file, encoding="utf-8")
        output = str(tmp_path / "output.sve")
        po2file(po, output, "utf-8", sve_file)

        with open(sve_file, encoding="utf-8") as f:
            original = f.read().strip()
        with open(output, encoding="utf-8") as f:
            result = f.read().strip()

        assert result == original

    def test_tra_roundtrip(self, tra_file, tmp_path):
        """TRA -> PO -> TRA roundtrip preserves entries."""
        po = file2po(tra_file, encoding="utf-8")
        output = str(tmp_path / "output.tra")
        po2file(po, output, "utf-8", tra_file)

        with open(output, encoding="utf-8") as f:
            result = f.read()

        # Verify key entries are present
        assert "@100 = ~Hello world~" in result
        assert "@101 = ~How are you?~" in result
        assert "[SOME_CONTEXT]" in result

    def test_untranslated_uses_msgid(self, msg_file, tmp_path):
        """When msgstr is empty, po2file should use the msgid."""
        po = file2po(msg_file, encoding="utf-8")
        # msgstr is "" by default from file2po
        output = str(tmp_path / "output.msg")
        po2file(po, output, "utf-8", msg_file)

        with open(output, encoding="utf-8") as f:
            content = f.read()

        assert "Hello world" in content

    def test_translated_uses_msgstr(self, msg_file, tmp_path):
        """When msgstr is set, po2file should use it."""
        po = file2po(msg_file, encoding="utf-8")
        po[0].msgstr = "Bonjour le monde"
        output = str(tmp_path / "output.msg")
        po2file(po, output, "utf-8", msg_file)

        with open(output, encoding="utf-8") as f:
            content = f.read()

        assert "Bonjour le monde" in content
        assert "{100}{}{Bonjour le monde}" in content


class TestFile2Msgstr:
    def test_loads_translations(self, msg_file, msg_translated_file):
        """file2msgstr loads translated values into PO msgstr."""
        po = file2po(msg_file, encoding="utf-8")
        po = file2msgstr(
            input_file=msg_translated_file,
            po=po,
            occurrence_path=msg_file,
            encoding="utf-8",
        )
        assert po[0].msgstr == "Bonjour le monde"
        assert po[1].msgstr == "Comment allez-vous?"

    def test_skips_same_as_source(self, msg_file):
        """file2msgstr skips translations identical to source by default."""
        po = file2po(msg_file, encoding="utf-8")
        po = file2msgstr(
            input_file=msg_file,
            po=po,
            occurrence_path=msg_file,
            encoding="utf-8",
        )
        # Should remain empty since translation == source
        assert po[0].msgstr == ""

    def test_loads_same_when_flag_set(self, msg_file):
        """file2msgstr loads same-as-source translations when same=True."""
        po = file2po(msg_file, encoding="utf-8")
        po = file2msgstr(
            input_file=msg_file,
            po=po,
            occurrence_path=msg_file,
            encoding="utf-8",
            same=True,
        )
        assert po[0].msgstr == "Hello world"

    def test_tra_female_entries(self, tra_file, tra_translated_file):
        """file2msgstr picks up female translations from TRA files."""
        po = file2po(tra_file, encoding="utf-8")
        po = file2msgstr(
            input_file=tra_translated_file,
            po=po,
            occurrence_path=tra_file,
            encoding="utf-8",
        )
        fe_map = female_entries(po)
        assert "Male greeting" in fe_map
        assert fe_map["Male greeting"].msgstr == "Salutation feminine"


class TestSortPo:
    def test_sorts_by_occurrence(self):
        po = polib.POFile()
        e1 = polib.POEntry(msgid="B", occurrences=[("z_file.msg", "200")])
        e2 = polib.POEntry(msgid="A", occurrences=[("a_file.msg", "100")])
        po.append(e1)
        po.append(e2)
        sorted_po = sort_po(po)
        assert sorted_po[0].msgid == "A"
        assert sorted_po[1].msgid == "B"


class TestPoMakeUnique:
    def test_merges_duplicate_entries(self):
        po = polib.POFile()
        e1 = polib.POEntry(msgid="Hello", occurrences=[("file1.msg", "100")])
        e2 = polib.POEntry(msgid="Hello", occurrences=[("file2.msg", "200")])
        po.append(e1)
        po.append(e2)
        result = po_make_unique(po)
        assert len(result) == 1
        assert len(result[0].occurrences) == 2

    def test_preserves_different_entries(self):
        po = polib.POFile()
        e1 = polib.POEntry(msgid="Hello", occurrences=[("file1.msg", "100")])
        e2 = polib.POEntry(msgid="World", occurrences=[("file1.msg", "200")])
        po.append(e1)
        po.append(e2)
        result = po_make_unique(po)
        assert len(result) == 2

    def test_different_context_kept_separate(self):
        po = polib.POFile()
        e1 = polib.POEntry(msgid="Hello", msgctxt=None, occurrences=[("f.msg", "1")])
        e2 = polib.POEntry(msgid="Hello", msgctxt="ctx", occurrences=[("f.msg", "2")])
        po.append(e1)
        po.append(e2)
        result = po_make_unique(po)
        assert len(result) == 2


class TestTranslationEntries:
    def test_returns_file_index_mapping(self, msg_file):
        po = file2po(msg_file, encoding="utf-8")
        entries = translation_entries(po)
        assert msg_file in entries
        assert len(entries[msg_file]) == 4
        assert entries[msg_file][0]["file_index"] == 100
        assert entries[msg_file][0]["po_index"] == 0


class TestFemaleEntries:
    def test_finds_female_entries(self):
        po = polib.POFile()
        male = polib.POEntry(msgid="Hello", msgstr="Bonjour", occurrences=[("f.tra", "1")])
        female = polib.POEntry(msgid="Hello", msgstr="Bonjour F", msgctxt=CONTEXT_FEMALE)
        po.append(male)
        po.append(female)
        fe_map = female_entries(po)
        assert "Hello" in fe_map
        assert fe_map["Hello"].msgstr == "Bonjour F"

    def test_empty_when_no_female(self, msg_file):
        po = file2po(msg_file, encoding="utf-8")
        fe_map = female_entries(po)
        assert len(fe_map) == 0


class TestUpdateFemaleEntries:
    def test_unobsoletes_female_with_male_match(self):
        """Obsolete female entries are restored when a matching male entry exists."""
        po = polib.POFile()
        male = polib.POEntry(msgid="Hello", msgstr="Bonjour", occurrences=[("f.tra", "1")])
        female = polib.POEntry(msgid="Hello", msgstr="Bonjour F", msgctxt=CONTEXT_FEMALE)
        female.obsolete = True
        po.append(male)
        po.append(female)

        result = update_female_entries(po)
        female_found = [e for e in result if e.msgctxt == CONTEXT_FEMALE]
        assert len(female_found) == 1
        assert female_found[0].obsolete is False

    def test_deletes_orphaned_obsolete_female(self):
        """Obsolete female entries with no male match are removed."""
        po = polib.POFile()
        female = polib.POEntry(msgid="Orphaned", msgstr="Orpheline", msgctxt=CONTEXT_FEMALE)
        female.obsolete = True
        po.append(female)

        result = update_female_entries(po)
        assert len(result) == 0

    def test_copies_fuzzy_from_male(self):
        """Female entries inherit fuzzy flag from their male counterpart."""
        po = polib.POFile()
        male = polib.POEntry(msgid="Hello", msgstr="Bonjour", occurrences=[("f.tra", "1")])
        male.flags.append("fuzzy")
        male.previous_msgid = "Hi"
        female = polib.POEntry(msgid="Hello", msgstr="Bonjour F", msgctxt=CONTEXT_FEMALE)
        female.obsolete = True
        po.append(male)
        po.append(female)

        result = update_female_entries(po)
        female_found = [e for e in result if e.msgctxt == CONTEXT_FEMALE]
        assert "fuzzy" in female_found[0].flags
        assert female_found[0].previous_msgid == "Hi"
