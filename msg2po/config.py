import ruamel.yaml
import sys
import os

VERSION = "1.1.15"


class Config:
    def __init__(self):
        yml = ".bgforge.yml"
        translation_defaults = {
            "encoding": "cp1252",
            "tra_dir": ".",
            "src_lang": "english",
            "simple_languages": True,  # extract into language name, not language code. pt_BR.po -> portuguese/1.msg
            "skip_files": [],
            "extract_format": "",  # could be 'sfall'
            "no_female": False,  # explicitly disable female extraction (TODO: reason unclear)
            "extract_fuzzy": False,
            "lowercase": True,
        }

        config = translation_defaults
        try:
            with open(yml, encoding="utf-8") as yf:
                yaml = ruamel.yaml.YAML()
                config = yaml.load(yf)
            translation_config = {**translation_defaults, **config["translation"]}
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
        self.lowercase = translation_config["lowercase"]

        self.po_dirname = "po"
        self.female_dir_suffix = "_female"
        self.po_dir = os.path.join(self.tra_dir, self.po_dirname)
        self.poify_dir = os.path.join(self.tra_dir, self.src_lang)
        self.version = VERSION
        self.newline_tra = "\r\n"
        self.newline_po = "\n"


CONFIG = Config()
