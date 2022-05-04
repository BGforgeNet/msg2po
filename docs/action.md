## Action

Using this action requires proper directory structure and configured `.bgforge.yml`. Reference for [Fallout](https://forums.bgforge.net/viewtopic.php?f=9&t=331), [Infinity Engine](https://forums.bgforge.net/viewtopic.php?f=9&t=26).

- [Standard](#standard)
- [Advanced](#advanced)
  - [Poify](#poify)
  - [Unpoify](#unpoify)
  - [Dir2msgstr](#dir2msgstr)

### Standard

This is the recommended configuration and should work for pretty much everyone.

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
      - name: Checkout
        uses: actions/checkout@v2
      - name: Poify/Unpoify
        uses: BGforgeNet/msg2po@v1.1.0  # version subject to change
        with:
          poify: "true"
          unpoify: "true"
          # dir2msgstr: "false"
```

`dir2msgstr` settings are for [power users](#dir2msgstr). Enable them only if you're sure that you understand what they do and how they work.

### Advanced
If for some reason standard configuration doesn't fit your workflow, check the following examples to see how else the action can be used.

### Poify
**Poify** scans source language strings and regenerates POT file. Then it merges POs with updated POT, which allows translators to see new and changed strings.

```yaml
name: poify
on:
  push:
    paths:
      - 'data/text/english/*/*.msg'
      - 'data/text/english/*/*.sve'
      - 'data/text/english/*/*.txt'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: BGforgeNet/msg2po@v1.1.0
        with:
          poify: "true"
          poify_commit: "true"
```

### Unpoify
**Unpoify** extracts translations from PO files into `msg`/`tra`, etc.

```yaml
name: unpoify
on:
  push:
    paths:
      - 'data/text/po/*.po'
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: BGforgeNet/msg2po@v1.1.0
        with:
          unpoify: "true"
          unpoify_commit: "true"
```

### Dir2msgstr

**Dir2msgstr** scans translation files for strings changed outside of translation system and attempts to load them into PO files.

This is an experimental step. It is recommended to submit translations only through the system.

If you choose to use it, you might run into merge conflicts or other irregularities - as in any case when there are multiple sources of truth. You might have to resolve them manually.

```yaml
name: dir2msgstr
on:
  push:
    paths:
      - 'data/text/*/*/*.msg'
      - 'data/text/*/*/*.sve'
      - 'data/text/*/*/*.txt'
      - '!data/text/english/*/*.msg' # exclude source language, since we don't need to update POs in that case
      - '!data/text/english/*/*.sve'
      - '!data/text/english/*/*.txt'
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: BGforgeNet/msg2po@v1.1.0
        with:
          dir2msgstr: "true"
          dir2msgstr_commit: "true"
```
