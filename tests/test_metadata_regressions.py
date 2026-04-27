import sys
from pathlib import Path

import polib

from msg2po.dir2msgstr import main as dir2msgstr_main
from msg2po.msgmerge import merge
from msg2po.poify import poify


def _write_duplicate_po(path: Path) -> None:
    po = polib.POFile()
    po.metadata = {"Content-Type": "text/plain; charset=UTF-8"}
    po.append(polib.POEntry(msgid="Hello", msgstr="", occurrences=[("game/one.msg", "100")]))
    po.append(polib.POEntry(msgid="Hello", msgstr="", occurrences=[("game/two.msg", "200")]))
    po.save(path)


class TestPoifyOccurrenceChanges:
    def test_rewrites_pot_when_only_occurrences_change(self, tmp_path):
        english_dir = tmp_path / "english"
        game_dir = english_dir / "game"
        game_dir.mkdir(parents=True)

        first_file = game_dir / "one.msg"
        first_file.write_text("{100}{}{Hello}\n", encoding="utf-8")

        poify(str(english_dir), encoding="utf-8")

        pot_path = tmp_path / "po" / "english.pot"
        pot = polib.pofile(pot_path)
        assert pot[0].occurrences == [("game/one.msg", "100")]

        first_file.unlink()
        second_file = game_dir / "two.msg"
        second_file.write_text("{200}{}{Hello}\n", encoding="utf-8")

        poify(str(english_dir), encoding="utf-8")

        pot = polib.pofile(pot_path)
        assert pot[0].occurrences == [("game/two.msg", "200")]


class TestMsgmergeOccurrenceOnlyNormalization:
    def test_merge_saves_dedup_when_only_occurrences_change(self, tmp_path, monkeypatch):
        po_path = tmp_path / "it.po"
        pot_path = tmp_path / "en.pot"
        _write_duplicate_po(po_path)

        pot = polib.POFile()
        pot.metadata = {"Content-Type": "text/plain; charset=UTF-8"}
        pot.append(polib.POEntry(msgid="Hello", msgstr="", occurrences=[("game/one.msg", "100")]))
        pot.save(pot_path)

        def fake_run(*_args, **_kwargs):
            return type("Result", (), {"stdout": "", "stderr": "", "returncode": 0})()

        monkeypatch.setattr("msg2po.msgmerge.subprocess.run", fake_run)

        merge(str(po_path), str(pot_path))

        po = polib.pofile(po_path)
        assert len(po) == 1
        assert po[0].occurrences == [("game/one.msg", "100"), ("game/two.msg", "200")]


class TestDir2MsgstrOccurrenceOnlyNormalization:
    def test_dir2msgstr_saves_dedup_when_only_occurrences_change(self, tmp_path, monkeypatch):
        po_path = tmp_path / "it.po"
        src_dir = tmp_path / "translations"
        src_dir.mkdir()
        _write_duplicate_po(po_path)

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "dir2msgstr.py",
                "-s",
                str(src_dir),
                "-o",
                str(po_path),
                "--ext",
                "msg",
            ],
        )

        dir2msgstr_main()

        po = polib.pofile(po_path)
        assert len(po) == 1
        assert po[0].occurrences == [("game/one.msg", "100"), ("game/two.msg", "200")]
