## Action

Using this action requires proper directory structure and configured `.bgforge.yml`. Reference for [Fallout](https://forums.bgforge.net/viewtopic.php?f=9&t=331), [Infinity Engine](https://forums.bgforge.net/viewtopic.php?f=9&t=26).

- [Options](#options)
  - [Main](#main)
  - [Additional](#additional)
- [Simple](#simple)
- [Standard](#standard)
- [Advanced](#advanced)
  - [Poify](#poify)
  - [Unpoify](#unpoify)
  - [Dir2msgstr](#dir2msgstr)
- [Handle charsets](#handle-charsets)

### Options

#### Main

Commonly used options.

| name            | default | description                                                                                                                        |
| --------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `poify`         | `false` | Run `poify.py`.                                                                                                                    |
| `unpoify`       | `false` | Run `unpoify.py`.                                                                                                                  |
| `single_commit` | `false` | All changes made by the action in a single run will be put together into a single commit. Supercedes all other `*_commit` options. |

#### Additional

Usually you don't need to change these options, but in some workflows that may be desirable.

| name                | default | description                                                                                                        |
| ------------------- | ------- | ------------------------------------------------------------------------------------------------------------------ |
| `poify_commit`      | `true`  | Commit `poify.py` result.                                                                                          |
| `unpoify_commit`    | `true`  | Commit `unpoify.py` result.                                                                                        |
| `dir2msgstr`        | `false` | For [power users](#dir2msgstr). Enable this only if you're sure that you understand what it does and how it works. |
| `dir2msgstr_commit` | `true`  | Commit `dir2msgstr.py` result.                                                                                     |
| `push`              | `true`  | Push the changes.                                                                                                  |

### Simple

This is a simple configuration that should work for most use cases.

```yaml
name: Poify/Unpoify
on:
  push:
    paths:
      - "data/text/**" # tra_dir

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Poify/Unpoify
        uses: BGforgeNet/msg2po@master
        with:
          poify: true
          unpoify: true
          single_commit: true
```

### Standard

In this configuration, there are 2 workflows:

Actual run with commit and push, launched only commits to `master` branch:

```yaml
# poify.yml

name: Poify/Unpoify
on:
  push:
    branches:
      - master
    paths:
      - "data/text/**"

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Poify/Unpoify
        uses: BGforgeNet/msg2po@master
        with:
          poify: true
          unpoify: true
          single_commit: true
```

And test run, launched on non-master branches and pull requests. It just checks changes to translation files for well-formedness.

```yaml
# poify-test.yml

name: Poify/Unpoify test
on:
  push:
    branches-ignore:
      - master
    paths:
      - "data/text/**"
  pull_request:
    paths:
      - "data/text/**"

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Poify/Unpoify
        uses: BGforgeNet/msg2po@master
        with:
          poify: true
          unpoify: true
          dir2msgstr: true
          push: false
```

This combination allows to reduce commit noise in repositories with a lot of activity.

### Advanced

If for some reason standard configurations don't fit your workflow, check the following examples to see how else the action can be used.

#### Poify

**Poify** scans source language strings and regenerates POT file. Then it merges POs with updated POT, which allows translators to see new and changed strings.

```yaml
name: poify
on:
  push:
    paths:
      - "data/text/english/*/*.msg"
      - "data/text/english/*/*.sve"
      - "data/text/english/*/*.txt"

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: BGforgeNet/msg2po@master
        with:
          poify: true
          poify_commit: true
```

#### Unpoify

**Unpoify** extracts translations from PO files into `msg`/`tra`, etc.

```yaml
name: unpoify
on:
  push:
    paths:
      - "data/text/po/*.po"
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: BGforgeNet/msg2po@master
        with:
          unpoify: true
          unpoify_commit: true
```

#### Dir2msgstr

**Dir2msgstr** scans translation files for strings changed outside of translation system and attempts to load them into PO files.

This is an experimental step. For local translation, consider [working with PO files directly](https://forums.bgforge.net/viewtopic.php?f=9&t=404) instead.

If you choose to use `dir2msgstr`, you might run into merge conflicts or other irregularities - as in any case when there are multiple sources of truth. You might have to resolve them manually.
To reduce the chance of that happening, do not push changes to multiple sources of truth (e.g both source and translation files) at the same time.

```yaml
name: dir2msgstr
on:
  push:
    paths:
      - "data/text/*/*/*.msg"
      - "data/text/*/*/*.sve"
      - "data/text/*/*/*.txt"
      - "!data/text/english/*/*.msg" # exclude source language, since we don't need to update POs in that case
      - "!data/text/english/*/*.sve"
      - "!data/text/english/*/*.txt"
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: BGforgeNet/msg2po@master
        with:
          dir2msgstr: true
          dir2msgstr_commit: true
```

Also, if your translation files are not in utf-8 (classic Fallouts, IE games), it's recommended to keep source strings in ASCII, or close to it, to avoid issues with characters missing in some charsets when extracting incomplete translations.

#### Handle charsets

You can also run [handle-charsets](https://github.com/BGforgeNet/handle-charsets) in the same job, set `handle_charsets: true` for that. Same parameters, same defaults. Prepend prefix `handle_charsets_` to parameter names:

- `handle_charsets_tra_path`
- `handle_charsets_out_path`
- `handle_charsets_from_utf8`
- `handle_charsets_split_console`
- `handle_charsets_commit`

If `single_commit` is enabled, it'll also include handle-charsets changes.
