r"""Extend base os commands"""

import json
import logging
import os
import random
import shutil
import subprocess as sp
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def write_json(content: dict, output_file: str, **kwargs):
    """Dump json to file with default parameters"""
    default_arguments = {"indent": 2, "separators": (",", ": "), "sort_keys": True}
    for k, v in default_arguments.items():
        if k not in kwargs:
            kwargs[k] = v

    with open(output_file, "w", encoding="utf-8") as output:
        json.dump(content, output, ensure_ascii=False, **kwargs)


def read_json(input_path: str) -> dict:
    """Reads json from utf-8 file"""
    with open(input_path, "r", encoding="utf-8") as fin:
        return json.load(fin)


def walk(path: str, recursive: bool = True, filter_ext=None):
    """Walk over path with recursive support"""
    if recursive:
        for subdir, _, files in os.walk(path, followlinks=True):
            subdir_suffix = subdir[len(path) :].lstrip("/")
            for file in files:
                if filter_ext and not any(
                    file.lower().endswith(ext) for ext in filter_ext
                ):
                    continue
                rel_path = os.path.join(subdir_suffix, file)
                full_path = os.path.join(subdir, file)
                if os.path.isfile(full_path):
                    yield rel_path, full_path
    else:
        for file in os.listdir(path):
            if filter_ext and not any(file.lower().endswith(ext) for ext in filter_ext):
                continue
            full_path = os.path.join(path, file)
            if os.path.isfile(full_path):
                yield file, full_path


def bash(cmd):
    if logging.root.level == logging.DEBUG:
        sp.check_output(cmd.split(" "))
    else:
        sp.run(cmd.split(" "), stderr=sp.DEVNULL, stdout=sp.DEVNULL, check=True)


class TmpFile:
    """Temp file object class"""

    def __init__(self, path: str):
        self.path_ = path

    def __enter__(self):
        return self.path_

    def __exit__(self, type_, value, traceback):
        if os.path.isfile(self.path_):
            bash(f"rm {self.path_}")


class RandomFile:
    """Random file object class"""

    def __init__(self, ext: str = ".txt", subdir=None):
        self.path_ = self.generate(ext=ext, subdir=subdir)
        while os.path.exists(self.path_):
            self.path_ = self.generate(ext)
        os.makedirs(os.path.dirname(self.path_), exist_ok=True)

    def __str__(self):
        return self.path_

    def __repr__(self):
        return self.path_

    def __enter__(self):
        return self.path_

    def __exit__(self, type_, value, traceback):
        if os.path.isfile(self.path_):
            bash(f"rm {self.path_}")

    @staticmethod
    def generate(ext: str = ".txt", subdir=None):
        if subdir:
            return (
                os.path.join(
                    tempfile.gettempdir(),
                    subdir,
                    "lora_" + str(random.randint(1, 10000)),
                )
                + ext
            )
        else:
            return (
                os.path.join(
                    tempfile.gettempdir(), "lora_" + str(random.randint(1, 10000))
                )
                + ext
            )


def create_path(dataset_path, file, file_type):
    """
    Creates full path to file if it exists, throws error otherwise

    Input:
     dataset_path: Path to dataset folder in which dataset files will be looked for
     file: filename (of reference or report)
     file_type: indicates if its reference/hypotheses/report for error message
    """
    path = os.path.join(dataset_path, file)
    if not os.path.exists(path):
        raise RuntimeError(f"There is no {file_type}: {path}")

    return path


def delete_dir_handler(listdir_fn, dirname, exception):
    try:
        for fileobj in listdir_fn(dirname):
            os.remove(fileobj)
        os.removedirs(dirname)
    except FileNotFoundError:
        pass
    except (AttributeError, OSError, TypeError):
        logger.warning(exception[1])
        logger.warning("Sorry. Couldn't delete directory {}.".format(dirname))
        raise


class TempDir:
    """Сontainer for temporary directory. Deletes directory when garbage
    collected/zero references"""

    def __init__(self):
        self.path = tempfile.mkdtemp()

    def __enter__(self):
        if not self.path:
            self.path = tempfile.mkdtemp()
        return self.path

    def __str__(self):
        return self.path

    def __repr__(self):
        return self.path

    def __del__(self):
        if os.path.exists(self.path):
            shutil.rmtree(self.path, onerror=delete_dir_handler)

    def __exit__(self, *args, **kwargs):
        self.__del__()

    def force_cleanup(self):
        if os.path.exists(self.path):
            shutil.rmtree(self.path, onerror=delete_dir_handler)


class SafeTempDir(TempDir):
    """Сontainer for temporary directory with saving parameter"""

    def __init__(self, save_path: Optional[str] = None, save_mode: bool = False):
        self.__save = save_mode

        if save_mode and save_path is not None:
            Path(save_path).mkdir(parents=True, exist_ok=True)
            self.path = save_path
        else:
            super().__init__()

    def __enter__(self):
        if self.__save:
            Path(self.path).mkdir(parents=True, exist_ok=True)
            return self.path
        else:
            return super().__enter__()

    def __del__(self):
        if not self.__save:
            super().__del__()
