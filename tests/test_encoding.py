# Tests for encoding detection and handling.

import pytest
from msg2po.core import get_enc


class TestGetEnc:
    def test_default_encoding(self):
        result = get_enc(lang_path="english.po", file_path="dialog.msg")
        assert result == "cp1252"

    def test_russian_encoding(self):
        result = get_enc(lang_path="russian.po", file_path="dialog.msg")
        assert result == "cp1251"

    def test_polish_encoding(self):
        result = get_enc(lang_path="polish.po", file_path="dialog.msg")
        assert result == "cp1250"

    def test_chinese_simplified(self):
        result = get_enc(lang_path="schinese.po", file_path="dialog.msg")
        assert result == "cp936"

    def test_japanese_encoding(self):
        result = get_enc(lang_path="japanese.po", file_path="dialog.msg")
        assert result == "cp932"

    def test_korean_encoding(self):
        result = get_enc(lang_path="korean.po", file_path="dialog.msg")
        assert result == "cp949"

    def test_vietnamese_encoding(self):
        result = get_enc(lang_path="vietnamese.po", file_path="dialog.msg")
        assert result == "cp1258"

    def test_setup_tra_is_utf8(self):
        """Console files default to utf-8 unless ansi_console is set."""
        result = get_enc(lang_path="russian.po", file_path="setup.tra")
        assert result == "utf-8"

    def test_ee_tra_is_utf8(self):
        result = get_enc(lang_path="russian.po", file_path="ee.tra")
        assert result == "utf-8"

    def test_ee_suffix_is_utf8(self):
        result = get_enc(lang_path="russian.po", file_path="mymod_ee.tra")
        assert result == "utf-8"

    def test_unknown_language_uses_default(self):
        result = get_enc(lang_path="klingon.po", file_path="dialog.msg")
        assert result == "cp1252"
