#!/usr/bin/env python3

"""Fail if any file with a `working-tree-encoding` gitattribute is not stored as UTF-8 in Git.

Git keeps working-tree-encoding content as UTF-8 in the blob and converts to the declared
encoding only on checkout. Files uploaded via the GitHub web UI / contents API bypass Git's
clean filter, so their raw legacy bytes get committed as the blob. On later checkout Git can no
longer convert UTF-8 -> the declared encoding, logs "error: failed to encode ..." and yet exits
0 - so the corruption is silent and the build stays green.

This validates the attributed blobs without a checkout: it streams them out of Git and runs the
same UTF-8 -> declared-encoding conversion through `iconv`, which is the converter Git itself
uses (a plain table codec would, for instance, wrongly reject valid cp1258 Vietnamese text that
Git accepts via combining-diacritic decomposition). Files are grouped by encoding so a whole
group converts in a single iconv pass; only a group that fails is then probed file by file.
"""

from __future__ import annotations

import subprocess
import sys
from collections import defaultdict
from collections.abc import Iterator

# working-tree-encoding values that need no UTF-8 -> legacy conversion, so they cannot fail.
SKIP = {"", "unspecified", "unset", "set", "utf-8", "utf8"}


def git(*args: str, stdin: bytes | None = None) -> bytes:
    return subprocess.run(["git", *args], input=stdin, capture_output=True, check=True).stdout


def cat_file_batch(oids: list[str]) -> bytes:
    """Raw `git cat-file --batch` output (per blob: a header line, the bytes, a newline)."""
    return git("cat-file", "--batch", stdin="".join(oid + "\n" for oid in oids).encode("ascii"))


def split_blobs(batch: bytes) -> Iterator[bytes]:
    """Yield each blob's bytes from cat-file --batch output, in request order."""
    pos = 0
    while pos < len(batch):
        newline = batch.index(b"\n", pos)
        size = int(batch[pos:newline].split()[2])  # header: "<oid> blob <size>"
        start = newline + 1
        yield batch[start : start + size]
        pos = start + size + 1  # skip the blob and its trailing newline


def iconv_ok(data: bytes, encoding: str) -> bool:
    """True if `data` converts cleanly from UTF-8 to `encoding` - Git's own conversion path."""
    result = subprocess.run(
        ["iconv", "-f", "UTF-8", "-t", encoding],
        input=data,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def main() -> int:
    # path -> blob oid for every tracked file ("<mode> <oid> <stage>\t<path>", NUL-separated).
    oids: dict[str, str] = {}
    for entry in git("ls-files", "-s", "-z").split(b"\0"):
        if not entry:
            continue
        meta, _, path = entry.partition(b"\t")
        oids[path.decode("utf-8", "surrogateescape")] = meta.split(b" ")[1].decode("ascii")

    # Group the attributed files by their declared encoding.
    paths_z = "\0".join(oids).encode("utf-8", "surrogateescape") + b"\0"
    fields = git("check-attr", "--stdin", "-z", "working-tree-encoding", stdin=paths_z).split(b"\0")
    groups: dict[str, list[tuple[str, str]]] = defaultdict(list)  # encoding -> [(path, oid)]
    for i in range(0, len(fields) - 2, 3):
        path_b, value_b = fields[i], fields[i + 2]
        if not path_b:
            continue
        encoding = value_b.decode("ascii", "replace")
        if encoding.lower() in SKIP:
            continue
        path = path_b.decode("utf-8", "surrogateescape")
        groups[encoding].append((path, oids[path]))

    if not groups:
        print("Encoding check: no legacy working-tree-encoding files.")
        return 0

    bad: list[str] = []
    for encoding, items in groups.items():
        batch = cat_file_batch([oid for _, oid in items])
        if iconv_ok(batch, encoding):
            continue
        # The group failed somewhere; find the offending files.
        bad.extend(path for (path, _), blob in zip(items, split_blobs(batch)) if not iconv_ok(blob, encoding))

    if bad:
        print("::error::Files with a working-tree-encoding attribute are not stored as UTF-8 in Git.")
        print("They were most likely uploaded via the GitHub web UI/API, which bypasses Git's encoding filter.")
        print("Fix: re-commit them from a local clone (git add --renormalize <files>), or upload UTF-8 bytes.")
        print("Affected files:")
        for path in sorted(bad):
            print(f"  {path}")
        return 1

    print("Encoding check passed: all working-tree-encoding files are stored as UTF-8 in Git.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
