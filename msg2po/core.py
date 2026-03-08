# Path helper utilities used across the codebase.

import shutil
from pathlib import Path

from loguru import logger


def basename(path):
    return Path(path).resolve().name


def strip_ext(filename):
    return Path(filename).stem


def get_dir(path: str):
    return str(Path(path).parent)


def create_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def ensure_dir_exists(d):
    if Path(d).is_dir():
        logger.debug(f"Found directory {d}")
    else:
        raise FileNotFoundError(f"Directory '{d}' does not exist. Check the path and try again.")


def copycreate(src_file, dst_file):
    Path(dst_file).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src_file, dst_file)
