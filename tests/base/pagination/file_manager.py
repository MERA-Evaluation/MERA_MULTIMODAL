import os
import sys
import logging
from typing import Optional, Generator, TypeVar
from pathlib import Path

import pandas as pd

sys.path.extend(
    [
        os.path.dirname(os.path.abspath(__file__)),
        os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "utils",
        ),
    ]
)

from mixins.extractors.base_extractor import BaseExtractor
from formats import FORMATS


T = TypeVar("T")
logger = logging.getLogger(__name__)


class FileManager:
    EXCLUDE_PROCESSOR_FOLDER_PATTERN: str = "processor_result"

    def __init__(self, extractor: BaseExtractor, count_download_file: int):
        self.extractor: BaseExtractor = extractor
        self.count_download_file: int = count_download_file

    @staticmethod
    def __get_file_extension(file: str) -> str:
        """
        Get file extension
        Parameters
        ----------
        file: path to file
        Returns
        -------
        FIle extension
        """
        return Path(file).suffix

    @property
    def target_folder(self) -> str:
        return self.extractor.target_folder

    def is_download_file(
        self, key: str, format_key: str, skip_data_key: set[str]
    ) -> bool:
        """
        Check that the file can be downloaded.
        Parameters
        ----------
        key: path to file
        format_key: file format value
        skip_data_key: set of the files' paths that must be skipped to download
        Returns
        -------
        Bool flag
        """
        return self.__get_file_extension(key) in self.__get_formats_values(
            format_key
        ) and (len(skip_data_key) == 0 or (key not in skip_data_key))

    @staticmethod
    def __get_formats_values(format_key: str) -> tuple[...]:
        """
        Get a tuple of files extensions for specified modality.
        Parameters
        ----------
        format_key: modality name
        Returns
        -------
        A tuple of files resolutions for specified modality
        """
        return FORMATS.get(format_key)

    def get_target_folder(self) -> str:
        """
        Wrap getter method for extraction target_folder value from Client(...) object.
        Returns
        -------
        Target folder name.
        """
        return self.extractor.client.target_folder

    def format_sample_target_path(self, local_path: str) -> str:
        """
        Wrap format_sample_target_path method of the Client(...) object.
        Parameters
        ----------
        local_path: Local path value.
        Returns
        -------
        Storage path value.
        """
        return self.extractor.client.format_sample_target_path(local_path)

    def get_skip_data_keys(
        self, result_file_name: str
    ) -> tuple[pd.DataFrame, set[str]]:
        """
        Wrap get_skip_data_keys method of the Client(...) object.
        Parameters
        ----------
        result_file_name: name of the file with result data.
        Returns
        -------
        Tuple of Pandas DataFrame with already processed data and set of paths.
        """
        return self.extractor.client.get_skip_data_keys(file_name=result_file_name)

    def upload_file_to_storage(
        self, byte_result_data: bytes, result_file_name: str
    ) -> None:
        """
        Wrap upload_file_to_storage method of the Client(...) object.
        Parameters
        ----------
        byte_result_data:
        result_file_name:
        Returns
        -------
        """
        self.extractor.client.upload_file_to_storage(byte_result_data, result_file_name)

    def extract(self):
        return self.extractor.extract()

    def format_sample_local_path(self, path_in_prefix: str) -> str:
        return self.extractor.format_sample_local_path(path_in_prefix)

    def run_worker(self, files: list[str]):
        self.extractor.run_worker(files)

    def paginate(
        self, format_key: str, skip_data_key: Optional[set] = None
    ) -> Generator[list[dict[str:T]], None, None]:
        """
        Paginate though the storage files forming a batch of n files
        on each iteration.
        Parameters
        ----------
        format_key: files format value
        skip_data_key: set of the files' paths that must be skipped to download

        Returns
        -------

        """
        batch_context_data: list[dict[str:T]] = []
        count_file: int = 0
        path_s3_key: list[str] = []
        cancelled_samples: int = 0

        for row in self.extract():
            if self.target_folder and not os.path.exists(self.target_folder):
                os.makedirs(self.target_folder, exist_ok=True)

            if self.is_download_file(
                key=row["path"], format_key=format_key, skip_data_key=skip_data_key
            ):
                path_in_prefix: str = row["path"]
                if self.EXCLUDE_PROCESSOR_FOLDER_PATTERN in path_in_prefix:
                    continue
                local_path = self.format_sample_local_path(path_in_prefix)
                if self.target_folder:
                    local_path: str = os.path.join(self.target_folder, local_path)
                row["path"] = local_path
                if path_in_prefix:
                    path_s3_key.append(self.format_sample_local_path(path_in_prefix))
                batch_context_data.append(row)
                count_file += 1

                if count_file >= self.count_download_file:
                    self.run_worker(path_s3_key)
                    yield batch_context_data
                    batch_context_data = []
                    count_file = 0
                    path_s3_key = []
            else:
                cancelled_samples += 1

        if count_file > 0:
            self.run_worker(path_s3_key)
            yield batch_context_data

        logger.info(f"Cancelled samples: {cancelled_samples}")
