## Changelog

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
