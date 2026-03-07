# Tests for msg2po.common utility functions.

import os

from msg2po.common import find_files, get_ext


class TestGetExt:
    def test_simple_extension(self):
        assert get_ext("file.msg") == "msg"

    def test_uppercase_lowered(self):
        assert get_ext("file.MSG") == "msg"

    def test_multiple_dots(self):
        assert get_ext("path.to.file.tra") == "tra"

    def test_no_extension(self):
        assert get_ext("noext") is None

    def test_empty_string(self):
        assert get_ext("") is None


class TestFindFiles:
    def test_finds_msg_files(self, fixtures_dir):
        files = find_files(fixtures_dir, "msg")
        basenames = [os.path.basename(f) for f in files]
        assert "sample.msg" in basenames
        assert "sample_translated.msg" in basenames

    def test_finds_tra_files(self, fixtures_dir):
        files = find_files(fixtures_dir, "tra")
        basenames = [os.path.basename(f) for f in files]
        assert "sample.tra" in basenames

    def test_no_match(self, fixtures_dir):
        files = find_files(fixtures_dir, "xyz")
        assert files == []

    def test_nonexistent_dir(self, tmp_path):
        files = find_files(str(tmp_path / "nonexistent"), "msg")
        assert files == []
