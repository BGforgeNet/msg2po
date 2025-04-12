## Changelog

### 1.4.1

Added simplified language aliases for cs/hu/pt/tchinese to use during extraction.

### 1.4.0

Disallow to use curly brackets in msg files, to avoid
[breaking translations](https://github.com/BGforgeNet/Fallout2_Restoration_Project/issues/336) in game.

### 1.3.2

- Removed unused `lowercase` setting.
- Replaced `all_utf8_yes_really_all` with `ansi_console`.
- Console files are in utf-8 by default now.

### 1.3.1

Fixed initial poify not working.

### 1.3.0

Added support for Python 3.12. Action now uses a virtual environment.

### 1.2.3

Added [special handling](https://github.com/BGforgeNet/Fallout2_Restoration_Project/issues/301) for cp1258 Vietnamese
encoding.

### 1.2.2

Set charset to cp1258 for Vietnamese.

### 1.2.1

Added `vi`/`vietnamese` language slug.

### 1.2.0

Added support for `all_utf8`, `all_utf8_yes_really_all` parameters to `.bgforge.yml`. Use the first one to consider all
files except DOS_FILENAMES in UTF-8, add the second one to consider even DOS_FILENAMES UTF-8.

### 1.1.16

Fixed file2msgstr invocation.

### 1.1.15

Fixed unfuzzy not working on Windows due to different default encoding.

### 1.1.14

Action: upgraded [paths-filter](https://github.com/AurorNZ/paths-filter) to 3.0.1.

### 1.1.13

- Added missing console entry point for `poify.py`, it can now be called as `poify`.
- Fixed spurious [change messages](https://github.com/BGforgeNet/msg2po/issues/5) for lines that are the same.
- Fixed `dir2msgstr` [missing](https://github.com/BGforgeNet/msg2po/issues/7) new female entries.
- Fixed `poify` to always use [Linux style paths](https://github.com/BGforgeNet/msg2po/issues/4) in occurrences, even on
  Windows.
- POlib updated to 1.2.0.

### 1.1.12

Action: added [handle-charsets](https://github.com/BGforgeNet/handle-charsets) capability.

### 1.1.11

Action: force unpoify if dir2msgstr found changes.

### 1.1.10

Allow to load manual translation change to the same value that existing `msgstr` is set to in PO, when `extract_fuzzy`
is not set, clearing `fuzzy` flag.

### 1.1.9

- Renamed some files to get rid of dash to fix pip install.

### 1.1.8

- Renamed some files to get rid of dash to fix pip install.

### 1.1.7

- Bumped version.

### 1.1.6

- Added `sv` slug for Swedish language.

### 1.1.5

- Fixed `poify` processing utf-8 characters in EE source tra's.

### 1.1.4

- Fixed `msgmerge` sometimes obsoleting female entries that have a fuzzy male match.
- `msgmerge` now deletes obsolete female entries.

### 1.1.3

- `dir2msgstr` works faster on translations with many female entries.
- Fixed spurious "different female lines" message in`*msgstr`.
- `*msgstr` loads changed female values too.
- `unfuzzy` can use local config.
- Action filters are shown in output for easier debug.
- Action `tra` paths are fixed.

### 1.1.2

- Fixed version in po generator.
- Moved lowercasing into a separate script.

### 1.1.1

- Action:
  - Works
  - Works faster
  - Commit and push enabled by default.
- `POT-Creation-Date` only updated on actual update.
- F2: For female lines in game dir, print a warning instead of dying.
- Enforce line endings: `\n` for PO and `\r\n` for translation files.
- Proper encoding for Hungarian.
- Fixed `dir2msgstr` encoding detection.
- `dir2msgstr` now supports known locale codes.
- Unfuzzying by `*2msgstr` properly removes `previous_msgid`.

### 1.1.0

- Massive rewrite under the hood.
- Published to PyPi.
- Added github action.
- Added repeated runs capability for `dir2msgstr`.
