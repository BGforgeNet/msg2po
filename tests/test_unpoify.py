from pathlib import Path

from msg2po.unpoify import clean_generated_female_dirs


def test_clean_generated_female_dirs_removes_only_generated_female_dirs(tmp_path):
    lang_dir = tmp_path / "polish"
    dialog_female = lang_dir / "dialog_female"
    cuts_female = lang_dir / "cuts_female"
    dialog = lang_dir / "dialog"

    dialog_female.mkdir(parents=True)
    cuts_female.mkdir(parents=True)
    dialog.mkdir(parents=True)

    (dialog_female / "stale.msg").write_text("{100}{}{STALE}\n", encoding="utf-8")
    (cuts_female / "stale.txt").write_text("STALE\n", encoding="utf-8")
    (dialog / "keep.msg").write_text("{100}{}{KEEP}\n", encoding="utf-8")

    clean_generated_female_dirs(str(lang_dir))

    assert not dialog_female.exists()
    assert not cuts_female.exists()
    assert dialog.exists()
    assert (dialog / "keep.msg").read_text(encoding="utf-8") == "{100}{}{KEEP}\n"


def test_clean_generated_female_dirs_ignores_missing_directory(tmp_path):
    missing = tmp_path / "missing"

    clean_generated_female_dirs(str(missing))

    assert not missing.exists()
