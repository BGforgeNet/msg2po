# Project configuration loaded from .bgforge.yml.
# Config is a frozen dataclass; load_config() is the factory.
# Module-level CONFIG is the convenience singleton for CLI use.

import os
from dataclasses import dataclass, field
from typing import Any

import ruamel.yaml
from loguru import logger

VERSION = "1.5.0"

TRANSLATION_DEFAULTS: dict[str, Any] = {
    "encoding": "cp1252",
    "tra_dir": ".",
    "src_lang": "english",
    "simple_languages": True,
    "skip_files": [],
    "extract_format": "",
    "no_female": False,
    "extract_fuzzy": False,
    "all_utf8": False,
    "ansi_console": False,
}


@dataclass(frozen=True)
class Config:
    encoding: str = "cp1252"
    tra_dir: str = "."
    src_lang: str = "english"
    simple_languages: bool = True
    skip_files: tuple[str, ...] = ()
    extract_format: str = ""
    no_female: bool = False
    extract_fuzzy: bool = False
    all_utf8: bool = False
    ansi_console: bool = False
    po_dirname: str = "po"
    female_dir_suffix: str = "_female"
    version: str = VERSION
    newline_tra: str = "\r\n"
    newline_po: str = "\n"
    # Raw config dict for bgforge-config shell wrapper
    _config: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def po_dir(self) -> str:
        return os.path.join(self.tra_dir, self.po_dirname)

    @property
    def poify_dir(self) -> str:
        return os.path.join(self.tra_dir, self.src_lang)


def load_config(yml_path: str = ".bgforge.yml") -> Config:
    """Load Config from a .bgforge.yml file. Returns defaults if file not found."""
    try:
        with open(yml_path, encoding="utf-8") as yf:
            yaml = ruamel.yaml.YAML()
            raw_config = yaml.load(yf)
        translation_config: dict[str, Any] = {**TRANSLATION_DEFAULTS, **raw_config["translation"]}
    except (OSError, KeyError):
        logger.warning(
            f"Config file '{yml_path}' not found or missing 'translation' key. "
            "Using defaults. Create a .bgforge.yml with a 'translation' section to configure."
        )
        translation_config = dict(TRANSLATION_DEFAULTS)
        raw_config = {}

    raw_config["translation"] = translation_config

    return Config(
        encoding=translation_config["encoding"],
        tra_dir=translation_config["tra_dir"],
        src_lang=translation_config["src_lang"],
        simple_languages=translation_config["simple_languages"],
        skip_files=tuple(translation_config["skip_files"]),
        extract_format=translation_config["extract_format"],
        no_female=translation_config["no_female"],
        extract_fuzzy=translation_config["extract_fuzzy"],
        all_utf8=translation_config["all_utf8"],
        ansi_console=translation_config["ansi_console"],
        _config=raw_config,
    )


CONFIG = load_config()
