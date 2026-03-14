# MSG2PO

[![Build status](https://github.com/BGforgeNet/msg2po/workflows/release/badge.svg)](https://github.com/BGforgeNet/msg2po/actions?query=workflow%3Arelease)
[![Patreon](https://img.shields.io/badge/Patreon-donate-FF424D?logo=Patreon&labelColor=141518)](https://www.patreon.com/BGforge)
[![Telegram](https://img.shields.io/badge/telegram-join%20%20%20%20%E2%9D%B1%E2%9D%B1%E2%9D%B1-darkorange?logo=telegram)](https://t.me/bgforge)
[![Discord](https://img.shields.io/discord/420268540700917760?logo=discord&label=discord&color=blue&logoColor=FEE75C)](https://discord.gg/4Yqfggm)
[![IRC](https://img.shields.io/badge/%23IRC-join%20%20%20%20%E2%9D%B1%E2%9D%B1%E2%9D%B1-darkorange)](https://bgforge.net/irc)

A set of tools to convert Fallout 1/2 MSG and WeiDU TRA into GNU gettext PO and back, used in [BGforge Hive](https://hive.bgforge.net/). Ask questions [here](https://forums.bgforge.net/viewforum.php?f=9).

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Commands](#commands)
  - [poify](#poify)
  - [unpoify](#unpoify)
  - [file2po](#file2po)
  - [po2file](#po2file)
  - [file2msgstr](#file2msgstr)
  - [dir2msgstr](#dir2msgstr)
  - [msgmerge-female](#msgmerge-female)
  - [resave-po](#resave-po)
  - [lowercase](#lowercase)
  - [unfuzzy](#unfuzzy)
  - [bgforge-config](#bgforge-config)
- [GitHub Action](#github-action)
- [Changelog](docs/changelog.md)

## Installation

```bash
pipx install msg2po
```

Also install [Gettext tools](https://www.gnu.org/software/gettext/), and make sure they are in PATH.

## Configuration

Create a `.bgforge.yml` file in your project root to configure the tool:

```yaml
translation:
  encoding: cp1252      # source encoding (cp1252 default, cp1251/ru, cp1250/pl, cp1258/vi)
  tra_dir: "."          # translation root directory
  src_lang: "english"   # source language (used for poify)
  extract_format: ""    # "" (default), "sfall" for Fallout
  no_female: false      # skip female translations
  extract_fuzzy: false  # include fuzzy entries
```

## Commands

### poify

Converts game translation files (MSG, SVE, TXT, TRA) from a source language directory into a single `.pot` (PO Template) file.

```bash
poify [DIR] [-e ENC] [-v] [-q] [-t]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `DIR` | Source language directory | `./english` |
| `-e ENC` | Source encoding | `cp1252` |
| `-v, --verbose` | Enable verbose output | - |
| `-q, --quiet` | Suppress info messages | - |
| `-t, --timestamps` | Show timestamps in log output | - |

**Example:**

```bash
poify ./english -e cp1252
```

This scans the `./english` directory for all translation files and creates `./po/english.pot`.

---

### unpoify

Extracts translated files from PO files back into the game's directory structure. Used after translation is done in Weblate/PO editor.

```bash
unpoify [DIR] [-v] [-q] [-t]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `DIR` | Directory with PO files | `./po` |
| `-v, --verbose` | Enable verbose output | - |
| `-q, --quiet` | Suppress info messages | - |
| `-t, --timestamps` | Show timestamps in log output | - |

**Example:**

```bash
unpoify ./po
```

This reads PO files from `./po` and extracts translations back into language-specific directories (e.g., `./french/`).

---

### file2po

Converts a single game translation file (MSG, SVE, TXT, TRA) into a PO file. Useful for extracting from individual files.

```bash
file2po INPUT_SOURCE OUTPUT_PO [-e ENC] [-v] [-q] [-t]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `INPUT_SOURCE` | Input translation file | - |
| `OUTPUT_PO` | Output PO file | - |
| `-e ENC` | Source encoding | `cp1252` |
| `-v, --verbose` | Enable verbose output | - |
| `-q, --quiet` | Suppress info messages | - |
| `-t, --timestamps` | Show timestamps in log output | - |

**Example:**

```bash
file2po ./english/dialog.msg ./output.pot -e cp1252
```

---

### po2file

Converts PO entries back into a single game translation file. The reverse of `file2po`.

```bash
po2file INPUT_FILE OUTPUT_FILE [-e ENC] [--path PATH] [-v] [-q] [-t]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `INPUT_FILE` | Input PO file | - |
| `OUTPUT_FILE` | Output translation file | - |
| `-e ENC` | Output encoding | `cp1252` |
| `--path PATH` | File occurrence in PO (relative path) | Output filename |
| `-v, --verbose` | Enable verbose output | - |
| `-q, --quiet` | Suppress info messages | - |
| `-t, --timestamps` | Show timestamps in log output | - |

**Example:**

```bash
po2file ./french.po ./french/dialog.msg -e cp1252
```

---

### file2msgstr

Loads translations from a game translation file into the `msgstr` fields of an existing PO file. Useful for reloading edited translations.

```bash
file2msgstr INPUT_FILE OUTPUT_FILE [-e ENC] [--path PATH] [--overwrite] [--same] [-v] [-q] [-t]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `INPUT_FILE` | Input translation file | - |
| `OUTPUT_FILE` | Output PO file (must exist) | - |
| `-e ENC` | Source encoding | `cp1252` |
| `--path PATH` | PO occurrence path | Input filename |
| `--overwrite` | Overwrite existing translations | - |
| `--same` | Load translations identical to original strings | - |
| `-v, --verbose` | Enable verbose output | - |
| `-q, --quiet` | Suppress info messages | - |
| `-t, --timestamps` | Show timestamps in log output | - |

**Example:**

```bash
file2msgstr ./french/dialog.msg ./french.po --overwrite
```

---

### dir2msgstr

Batch loads translations from all files in a directory into corresponding PO files. Reverse of `unpoify` - used when translators edit files directly instead of PO.

```bash
dir2msgstr [--auto] [-s SRC_DIR] [-o OUTPUT_FILE] [--ext EXT] [--same] [--overwrite] [-v] [-q] [-t]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `--auto` | Auto-find POs and language dirs, process all valid extensions | - |
| `-s SRC_DIR` | Directory to load from | `.` |
| `-o OUTPUT_FILE` | Existing PO file | - |
| `--ext EXT` | Load files with this extension | - |
| `--same` | Load translations identical to original strings | - |
| `--overwrite` | Overwrite existing translations | - |
| `-v, --verbose` | Enable verbose output | - |
| `-q, --quiet` | Suppress info messages | - |
| `-t, --timestamps` | Show timestamps in log output | - |

**Example:**

```bash
dir2msgstr --auto
```

Or manually:

```bash
dir2msgstr -s ./french -o ./french.po --ext msg --overwrite
```

---

### msgmerge-female

Updates PO files from a POT template using GNU gettext's `msgmerge`, with special handling to keep female translations. Requires Gettext tools in PATH.

```bash
msgmerge-female [PO POT] [-v] [-q] [-t]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `PO` | PO file to update | - |
| `POT` | POT template file | - |
| `-v, --verbose` | Enable verbose output | - |
| `-q, --quiet` | Suppress info messages | - |
| `-t, --timestamps` | Show timestamps in log output | - |

**Single file:**

```bash
msgmerge-female french.po english.pot
```

**Batch (uses .bgforge.yml config):**

```bash
msgmerge-female
```

---

### resave-po

Resaves a PO file using the polib API to correct formatting. Useful for normalizing PO file structure.

```bash
resave-po INPUT_FILE [-v] [-q] [-t]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `INPUT_FILE` | PO file to resave | - |
| `-v, --verbose` | Enable verbose output | - |
| `-q, --quiet` | Suppress info messages | - |
| `-t, --timestamps` | Show timestamps in log output | - |

**Example:**

```bash
resave-po ./french.po
```

---

### lowercase

Recursively renames files and directories to lowercase. Useful for preparing case-insensitive file systems.

```bash
lowercase DIR [-v] [-q] [-t]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `DIR` | Directory to process | - |
| `-v, --verbose` | Enable verbose output | - |
| `-q, --quiet` | Suppress info messages | - |
| `-t, --timestamps` | Show timestamps in log output | - |

**Example:**

```bash
lowercase ./french
```

Note: Excludes `.git`, `.svn`, `.hg`, `.github` directories, `.po` files, and `README.md`.

---

### unfuzzy

Removes fuzzy flags from PO entries where the previous msgid matches the current msgid after applying string replacements. Used to reduce diff noise after source language spelling changes.

Create `unfuzzy.yml` with replacements:

```yaml
- ["Nuka Cola", "Nuka-Cola"]
- ["nuka cola", "Nuka-Cola"]
```

```bash
unfuzzy INPUT_FILE [-w] [-v] [-q] [-t]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `INPUT_FILE` | PO file to process | - |
| `-w` | Write changes to file (without this, previews only) | - |
| `-v, --verbose` | Enable verbose output | - |
| `-q, --quiet` | Suppress info messages | - |
| `-t, --timestamps` | Show timestamps in log output | - |

**Example:**

```bash
unfuzzy ./french.po -w
```

---

### bgforge-config

Reads values from `.bgforge.yml` configuration. Primarily used by GitHub Actions.

```bash
bgforge-config STANZA KEY
```

| Argument | Description |
|----------|-------------|
| `STANZA` | Config section (e.g., `translation`) |
| `KEY` | Config key (e.g., `encoding`) |

**Example:**

```bash
bgforge-config translation encoding
```

---

## GitHub Action

A GitHub Action is available for automatic processing. See [docs/action.md](docs/action.md) for details.
