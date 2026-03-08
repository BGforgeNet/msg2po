# Tests for pure utility functions in msg2po.core.

import pytest

from msg2po.core import (
    TRANSLITERATION_RULES_VIETNAMESE,
    basename,
    copycreate,
    create_dir,
    encode_custom,
    ensure_dir_exists,
    get_dir,
    get_line_format,
    language_slug,
    metadata,
    parent_dir,
    strip_ext,
    transliterate,
)


class TestBasename:
    def test_simple_path(self):
        assert basename("/foo/bar/baz") == "baz"

    def test_trailing_separator(self):
        assert basename("/foo/bar/baz/") == "baz"

    def test_single_component(self):
        result = basename("baz")
        assert result == "baz"


class TestParentDir:
    def test_simple_path(self):
        result = parent_dir("/foo/bar/baz")
        assert result == "/foo/bar"

    def test_trailing_separator(self):
        result = parent_dir("/foo/bar/baz/")
        assert result == "/foo/bar"


class TestStripExt:
    def test_simple(self):
        assert strip_ext("file.msg") == "file"

    def test_dotted_path(self):
        assert strip_ext("path.to.file.tra") == "path.to.file"

    def test_no_extension(self):
        # rsplit with no dot will return the whole string
        assert strip_ext("noext") == "noext"


class TestGetDir:
    def test_with_directory(self, tmp_path):
        import os

        path = os.path.join(str(tmp_path), "file.msg")
        assert get_dir(path) == str(tmp_path)

    def test_filename_only(self):
        assert get_dir("file.msg") == "."


class TestCreateDir:
    def test_creates_nested_dirs(self, tmp_path):
        target = tmp_path / "a" / "b" / "c"
        create_dir(str(target))
        assert target.is_dir()

    def test_existing_dir_is_noop(self, tmp_path):
        create_dir(str(tmp_path))
        assert tmp_path.is_dir()


class TestEnsureDirExists:
    def test_existing_dir_succeeds(self, tmp_path):
        # Should not raise
        ensure_dir_exists(str(tmp_path))

    def test_missing_dir_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            ensure_dir_exists(str(tmp_path / "nonexistent"))


class TestCopycreate:
    def test_copies_file_creating_dirs(self, tmp_path):
        src = tmp_path / "src.txt"
        src.write_text("hello")
        dst = tmp_path / "sub" / "dir" / "dst.txt"
        copycreate(str(src), str(dst))
        assert dst.read_text() == "hello"


class TestGetLineFormat:
    def test_msg_no_context(self):
        entry = {"index": 100, "value": "Hello", "female": None, "context": None}
        result = get_line_format(entry, "msg")
        assert result == "{{{index}}}{{}}{{{value}}}\n"

    def test_msg_with_context(self):
        entry = {"index": 100, "value": "Hello", "female": None, "context": "ctx"}
        result = get_line_format(entry, "msg")
        assert result == "{{{index}}}{{{context}}}{{{value}}}\n"

    def test_tra_with_female(self):
        entry = {"index": 100, "value": "Hello", "female": "Hello F", "context": None}
        result = get_line_format(entry, "tra")
        assert result == "@{index} = ~{value}~ ~{female}~\n"

    def test_tra_no_context_no_female(self):
        entry = {"index": 100, "value": "Hello", "female": None, "context": None}
        result = get_line_format(entry, "tra")
        assert result == "@{index} = ~{value}~\n"

    def test_sve_default(self):
        entry = {"index": 100, "value": "Hello", "female": None, "context": None}
        result = get_line_format(entry, "sve")
        assert result == "{index}:{value}\n"

    def test_msg_forbidden_character_raises(self):
        entry = {"index": 100, "value": "Hello {world}", "female": None, "context": None}
        with pytest.raises(ValueError, match="Invalid translation character"):
            get_line_format(entry, "msg")


class TestLanguageSlug:
    def test_simple_language(self):
        assert language_slug("french.po") == "french"

    def test_language_code_mapping(self):
        # simple_languages is True by default
        assert language_slug("pt_br.po") == "portuguese"
        assert language_slug("ru.po") == "russian"
        assert language_slug("cs.po") == "czech"

    def test_unknown_language_passes_through(self):
        assert language_slug("klingon.po") == "klingon"

    def test_path_with_directory(self):
        result = language_slug("/some/path/french.po")
        assert result == "french"


class TestTransliterate:
    def test_vietnamese_a_breve(self):
        # a + combining breve -> ă
        result = transliterate("a\u0306", TRANSLITERATION_RULES_VIETNAMESE)
        assert result == "\u0103"

    def test_no_change(self):
        result = transliterate("hello", TRANSLITERATION_RULES_VIETNAMESE)
        assert result == "hello"


class TestEncodeCustom:
    def test_utf8_passthrough(self):
        result = encode_custom("Hello world", "utf-8")
        assert result == "Hello world"

    def test_cp1252(self):
        result = encode_custom("Hello", "cp1252")
        assert result == "Hello"

    def test_cp1258_calls_vietnamese(self):
        result = encode_custom("hello", "cp1258")
        assert result == "hello"


class TestMetadata:
    def test_default_metadata(self):
        meta = metadata()
        assert "Content-Type" in meta
        assert meta["Content-Type"] == "text/plain; charset=UTF-8"
        assert "X-Generator" in meta

    def test_pot_metadata_has_creation_date(self):
        meta = metadata(pot=True)
        assert "POT-Creation-Date" in meta

    def test_po_metadata_has_revision_date(self):
        meta = metadata(po=True)
        assert "PO-Revision-Date" in meta

    def test_existing_metadata_returned_as_is(self):
        existing = {"foo": "bar"}
        result = metadata(old_metadata=existing)
        assert result == {"foo": "bar"}
