# MSG2PO

[![Build status](https://github.com/BGforgeNet/msg2po/workflows/release/badge.svg)](https://github.com/BGforgeNet/msg2po/actions?query=workflow%3Arelease)
[![Patreon](https://img.shields.io/badge/Patreon-donate-FF424D?logo=Patreon&labelColor=141518)](https://www.patreon.com/BGforge)
[![Telegram](https://img.shields.io/badge/telegram-join%20%20%20%20%E2%9D%B1%E2%9D%B1%E2%9D%B1-darkorange?logo=telegram)](https://t.me/bgforge)
[![Discord](https://img.shields.io/discord/420268540700917760?logo=discord&label=discord&color=blue&logoColor=FEE75C)](https://discord.gg/4Yqfggm)
[![IRC](https://img.shields.io/badge/%23IRC-join%20%20%20%20%E2%9D%B1%E2%9D%B1%E2%9D%B1-darkorange)](https://bgforge.net/irc)

This is a set of tools to convert Fallout 1/2 MSG and WeiDU TRA into GNU gettext PO and back, used in [BGforge Hive](https://hive.bgforge.net/). Ask questions [here](https://forums.bgforge.net/viewforum.php?f=9).

## Installation
```bash
pip install msg2po
```

Also install [Gettext tools](https://www.gnu.org/software/gettext/), and make sure they are in PATH.

## Usage
```bash
$ poify.py -h
.bgforge.yml not found, assuming defaults
usage: poify.py [-h] [-e ENC] [DIR]

Poify files in selected directory

positional arguments:
  DIR         source language directory (default: ./english)

options:
  -h, --help  show this help message and exit
  -e ENC      source encoding (default: cp1252)
```

## Action
Github [action](docs/action.md) is available for automatic processing.

---
[Changelog](docs/changelog.md)
