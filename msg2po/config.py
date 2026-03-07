import os
import sys
from typing import Any

import ruamel.yaml

VERSION = "1.4.3"


class Config:
    encoding: str
    tra_dir: str
    src_lang: str
    simple_languages: bool
    skip_files: list[str]
    extract_format: str
    no_female: bool
    extract_fuzzy: bool
    all_utf8: bool
    ansi_console: bool
    po_dirname: str
    female_dir_suffix: str
    po_dir: str
    poify_dir: str
    version: str
    newline_tra: str
    newline_po: str
    _config: dict[str, Any]

    def __init__(self):
        yml = ".bgforge.yml"
        translation_defaults: dict[str, Any] = {
            "encoding": "cp1252",
            "tra_dir": ".",
            "src_lang": "english",
            "simple_languages": True,  # extract into language name, not language code. pt_BR.po -> portuguese/1.msg
            "skip_files": [],
            "extract_format": "",  # could be 'sfall'
            "no_female": False,  # explicitly disable female extraction (TODO: reason unclear)
            "extract_fuzzy": False,
            # work with all files in utf-8
            "all_utf8": False,
            # if all_utf8 it True, still keep console files in ansi (CONSOLE_FILENAMES)
            "ansi_console": False,
        }

        config: dict[str, Any] = dict(translation_defaults)
        try:
            with open(yml, encoding="utf-8") as yf:
                yaml = ruamel.yaml.YAML()
                config = yaml.load(yf)
            translation_config: dict[str, Any] = {**translation_defaults, **config["translation"]}
        except:
            print(yml + " not found, assuming defaults", file=sys.stderr)
            translation_config = translation_defaults
        config["translation"] = translation_config
        self._config = config  # so that shell wrapper can get values from other stanzas too

        self.encoding = translation_config["encoding"]
        self.tra_dir = translation_config["tra_dir"]
        self.src_lang = translation_config["src_lang"]
        self.simple_languages = translation_config["simple_languages"]
        self.skip_files = translation_config["skip_files"]
        self.extract_format = translation_config["extract_format"]
        self.no_female = translation_config["no_female"]
        self.extract_fuzzy = translation_config["extract_fuzzy"]
        self.all_utf8 = translation_config["all_utf8"]
        self.ansi_console = translation_config["ansi_console"]

        self.po_dirname = "po"
        self.female_dir_suffix = "_female"
        self.po_dir = os.path.join(self.tra_dir, self.po_dirname)
        self.poify_dir = os.path.join(self.tra_dir, self.src_lang)
        self.version = VERSION
        self.newline_tra = "\r\n"
        self.newline_po = "\n"


CONFIG = Config()
