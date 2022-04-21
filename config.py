import ruamel.yaml
import sys
import os

VERSION = "1.1.0"


class Config:
    def __init__(self):
        yml = ".bgforge.yml"
        defaults = {
            "encoding": "cp1252",
            "tra_dir": ".",
            "src_lang": "english",
            "simple_languages": True,  # extract into language name, not language code. pt_BR.po -> portuguese/1.msg
            "skip_files": [],
            "extract_format": "",  # could be 'sfall'
            "no_female": False,  # expllicitly disable female extraction?
            "extract_fuzzy": False,
        }

        config = defaults
        try:
            with open(yml) as yf:
                yaml = ruamel.yaml.YAML()
                config = yaml.load(yf)
                config = {**defaults, **config["translation"]}
        except:
            print(yml + " not found, assuming defaults", file=sys.stderr)
        self._config = config  # for shell wrapper

        self.encoding = config["encoding"]
        self.tra_dir = config["tra_dir"]
        self.src_lang = config["src_lang"]
        self.simple_languages = config["simple_languages"]
        self.skip_files = config["skip_files"]
        self.extract_format = config["extract_format"]
        self.no_female = config["no_female"]
        self.extract_fuzzy = config["extract_fuzzy"]

        self.po_dirname = "po"
        self.female_dir_suffix = "_female"
        self.po_dir = os.path.join(self.tra_dir, self.po_dirname)
        self.poify_dir = os.path.join(self.tra_dir, self.src_lang)
        self.version = VERSION


CONFIG = Config()