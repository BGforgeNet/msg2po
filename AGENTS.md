# Agents Documentation

## Project Overview

**msg2po** converts Fallout 1/2 MSG and WeiDU TRA files into GNU gettext PO format and back. It is used by [BGforge Hive](https://hive.bgforge.net/) for game translation workflows. Published on PyPI as `msg2po`.

**Workflow:**
```
poify    →  Weblate  →  unpoify  →  dir2msgstr (optional)
(game → PO)       (PO → game)    (reload edits)
```

## Dependencies

- **polib** - PO file parsing
- **loguru** - Logging
- **ruamel.yaml** - YAML config parsing

## Key Commands

```bash
uv run ruff check              # Lint (rules: E, F, W, I, UP, B, SIM)
uv run ruff check --fix        # Lint with auto-fix
uv run ruff format             # Format
uv run ruff format --check     # Format check
uv run ty check                # Type check
```

Ruff config: line-length 120, SIM108 ignored (ternary often less readable here).

**Pre-commit:**
```bash
uv run pre-commit install      # Set up hooks
uv run pre-commit run --all-files  # Run manually
```

## Core Modules

- **formats.py** - FILE_FORMAT dict (MSG, SVE, TXT, TRA specs)
- **config.py** - Config class, loads .bgforge.yml
- **transfile.py** - TRANSFile parser, TRANSEntry dataclass
- **conversion.py** - file2po, po2file, file2msgstr
- **indexed_po.py** - IndexedPO (POFile + precomputed indexes)
- **po_utils.py** - PO manipulation utilities

## File Formats

| Format | Description | Female Handling |
|--------|-------------|-----------------|
| MSG | Fallout 1/2 dialog | Separate `_female` dirs |
| SVE | Fallout 2 subtitles | Separate `_female` dirs |
| TXT | Indexed text | Separate `_female` dirs |
| TRA | WeiDU/Infinity Engine | Inline `~female~` |

## Config (.bgforge.yml)

```yaml
translation:
  encoding: cp1251    # cp1252 default, cp1251/ru, cp1250/pl, cp1258/vi
  tra_dir: "."
  src_lang: "english"
  extract_format: ""  # or "sfall"
  no_female: false
  extract_fuzzy: false
```

## CI

- **Lint:** ShellCheck, ruff, ty
- **Test:** pytest (runs in parallel with lint)
- **Release:** `uv build` + `uv publish` on tag
- **GitHub Action:** Composite action (`action.yml`) automates poify/unpoify/dir2msgstr in CI
