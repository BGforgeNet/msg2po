# Tests for TRANSFile parsing across all supported formats.

import pytest
from msg2po.core import TRANSFile, is_indexed


class TestTRANSFileMSG:
    def test_parse_entries(self, msg_file):
        trans = TRANSFile(filepath=msg_file, is_source=True, encoding="utf-8")
        assert len(trans.entries) == 4

    def test_entry_indexes(self, msg_file):
        trans = TRANSFile(filepath=msg_file, is_source=True, encoding="utf-8")
        indexes = [e.index for e in trans.entries]
        assert indexes == ["100", "101", "102", "103"]

    def test_entry_values(self, msg_file):
        trans = TRANSFile(filepath=msg_file, is_source=True, encoding="utf-8")
        assert trans.entries[0].value == "Hello world"
        assert trans.entries[1].value == "How are you?"

    def test_entry_context(self, msg_file):
        trans = TRANSFile(filepath=msg_file, is_source=True, encoding="utf-8")
        # Entry without context
        assert trans.entries[0].context is None
        # Entry with context
        assert trans.entries[2].context == "Some context"
        assert trans.entries[2].value == "This has context"

    def test_empty_entry_becomes_space(self, msg_file):
        """Empty MSG values get replaced with space and EMPTY_COMMENT when is_source=True."""
        trans = TRANSFile(filepath=msg_file, is_source=True, encoding="utf-8")
        assert trans.entries[3].value == " "
        assert trans.entries[3].comment == "LEAVE empty space in translation"

    def test_forbidden_character_raises(self, tmp_path):
        bad_file = tmp_path / "bad.msg"
        bad_file.write_text("{100}{}{Hello {nested} braces}", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid translation character"):
            TRANSFile(filepath=str(bad_file), is_source=True, encoding="utf-8")

    def test_duplicate_index_raises(self, tmp_path):
        bad_file = tmp_path / "dup.msg"
        bad_file.write_text("{100}{}{First}\n{100}{}{Second}", encoding="utf-8")
        with pytest.raises(ValueError, match="Duplicate entry indices"):
            TRANSFile(filepath=str(bad_file), is_source=True, encoding="utf-8")

    def test_invalid_index_000_raises(self, tmp_path):
        bad_file = tmp_path / "zero.msg"
        bad_file.write_text("{000}{}{Bad index}", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid entry index"):
            TRANSFile(filepath=str(bad_file), is_source=True, encoding="utf-8")


class TestTRANSFileSVE:
    def test_parse_entries(self, sve_file):
        trans = TRANSFile(filepath=sve_file, is_source=True, encoding="utf-8")
        assert len(trans.entries) == 3

    def test_entry_values(self, sve_file):
        trans = TRANSFile(filepath=sve_file, is_source=True, encoding="utf-8")
        assert trans.entries[0].value == "Hello world"
        assert trans.entries[0].index == "100"

    def test_no_context(self, sve_file):
        trans = TRANSFile(filepath=sve_file, is_source=True, encoding="utf-8")
        for entry in trans.entries:
            assert entry.context is None


class TestTRANSFileTRA:
    def test_parse_entries(self, tra_file):
        trans = TRANSFile(filepath=tra_file, is_source=True, encoding="utf-8")
        assert len(trans.entries) == 4

    def test_entry_values(self, tra_file):
        trans = TRANSFile(filepath=tra_file, is_source=True, encoding="utf-8")
        assert trans.entries[0].value == "Hello world"
        assert trans.entries[0].index == "100"

    def test_context(self, tra_file):
        trans = TRANSFile(filepath=tra_file, is_source=True, encoding="utf-8")
        assert trans.entries[2].context == "SOME_CONTEXT"
        assert trans.entries[2].value == "This has context"

    def test_female(self, tra_file):
        trans = TRANSFile(filepath=tra_file, is_source=True, encoding="utf-8")
        assert trans.entries[3].value == "Male greeting"
        assert trans.entries[3].female == "Female greeting"

    def test_no_female_when_absent(self, tra_file):
        trans = TRANSFile(filepath=tra_file, is_source=True, encoding="utf-8")
        assert trans.entries[0].female is None


class TestTRANSFileTXT:
    def test_parse_indexed(self, txt_indexed_file):
        trans = TRANSFile(filepath=txt_indexed_file, is_source=True, encoding="utf-8")
        assert len(trans.entries) == 3
        assert trans.entries[0].value == "Hello world"

    def test_has_indexed_txt_comment(self, txt_indexed_file):
        trans = TRANSFile(filepath=txt_indexed_file, is_source=True, encoding="utf-8")
        assert trans.entries[0].comment == "indexed_txt"


class TestIsIndexed:
    def test_indexed_file(self, txt_indexed_file):
        assert is_indexed(txt_indexed_file, encoding="utf-8") is True

    def test_nonindexed_file(self, txt_nonindexed_file):
        assert is_indexed(txt_nonindexed_file, encoding="utf-8") is False
