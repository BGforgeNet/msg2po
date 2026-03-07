# functions that are needed in config and core, to avoid circular import
import os


def find_files(dir: str, ext: str):
    """
    Find files with extension ext in directory dir
    """
    files = []
    for root, _subdir_list, file_list in os.walk(dir):
        for f in file_list:
            if get_ext(f) == ext:
                files.append(os.path.join(root, f))
    return files


def get_ext(path):
    parts = path.rsplit(".", 1)
    if len(parts) < 2:
        return None
    return parts[1].lower()
