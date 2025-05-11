from abc import ABC, abstractmethod
import zipfile
import tarfile
import shutil
import os
import sys
import logging
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from formats import FORMATS


logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


class Archive(ABC):
    FORMAT = None
    RESULT_FOLDER = "./archive_content"
    BATCH_SIZE = 10
    BATCH_MEMORY_ACCEPTABLE_OFFSET = 400
    CHUNK_SIZE = 1024 * 1024

    def __init__(self, batch_archives_amount: int = 10):
        self.batch_archives_amount = batch_archives_amount

    @staticmethod
    def _check_sample_format(sample_path: str, content_format: str) -> bool:
        return Path(sample_path).suffix in FORMATS.get(content_format)

    def _get_archive_name(self, sample_path):
        basename = os.path.basename(sample_path)
        basename = basename.replace(self.FORMAT, "")
        return basename

    @abstractmethod
    def open_archive(self, archive_path: str, content_format: str) -> str:
        raise NotImplementedError

    def open_archives(
        self, archives_paths: list[str], content_format: str
    ) -> list[str]:
        """
        Open archives.
        Parameters
        ----------
        content_format
        archives_paths

        Returns
        -------
        """

        archives_files = []
        for sample_path in archives_paths:
            result = self.open_archive(sample_path, content_format)
            archives_files.extend(result)

        logger.info("All archives were unpacked")
        return archives_files


class DummyArchive(Archive):
    """Implement archive methods for flat files."""

    def open_archive(self, archive_path: str, content_format: str) -> list[str]:
        return [
            archive_path,
        ]


class ZipArchive(Archive):
    FORMAT = ".zip"

    def open_archive(
        self,
        archive_path: str,
        content_format: str,
    ) -> list[str]:
        # folder_name = archive_path.replace(".zip", "")
        archive_file = archive_path.replace(self.FORMAT, "")
        shutil.move(archive_path, archive_file)
        os.makedirs(archive_path, exist_ok=True)
        files = []
        with zipfile.ZipFile(archive_file, "r") as zip_file:
            for member in zip_file.infolist():
                file_path = os.path.join(archive_path, member.filename)
                if not self._check_sample_format(file_path, content_format):
                    continue
                file_folder = os.path.dirname(
                    os.path.join(archive_path, member.filename)
                )
                os.makedirs(file_folder, exist_ok=True)
                files.append(file_path)
                if member.is_dir():
                    os.makedirs(file_path, exist_ok=True)
                else:
                    with zip_file.open(member) as fileobj:
                        with open(file_path, "wb") as outfile:
                            while True:
                                chunk = fileobj.read(self.CHUNK_SIZE)
                                if not chunk:
                                    break
                                outfile.write(chunk)
        return files


class TarArchive(Archive):
    FORMAT = ".tar"

    def open_archive(
        self,
        archive_path: str,
        content_format: str,
    ) -> list[str]:
        folder_name = os.path.basename(archive_path).replace(self.FORMAT, "")
        extract_path = os.path.join(self.RESULT_FOLDER, folder_name)
        os.makedirs(extract_path, exist_ok=True)
        files = []
        with tarfile.open(archive_path, "r") as tar:
            for member in tar.getmembers():
                if os.path.dirname(member.name):
                    os.makedirs(
                        os.path.join(extract_path, os.path.dirname(member.name)),
                        exist_ok=True,
                    )
                files.append(os.path.join(extract_path, member.name))
                with tar.extractfile(member) as fileobj:
                    file_path = os.path.join(extract_path, member.name)
                    if not self._check_sample_format(file_path, content_format):
                        continue
                    with open(file_path, "wb") as outfile:
                        while True:
                            chunk = fileobj.read(self.CHUNK_SIZE)
                            if not chunk:
                                break
                            outfile.write(chunk)
        return files
