import logging
from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd


logger = logging.getLogger(__name__)


class BaseClient(ABC):
    @abstractmethod
    def get_source_file(self, file_path: str) -> bytes:
        """
        Get byte stream of the source CSV file with data.
        Parameters
        ----------
        file_path: path (remote, local, etc ...) to file

        Returns
        -------

        """
        raise NotImplementedError

    @abstractmethod
    def run_worker(self, files: list[str]) -> None:
        """
        Run files downloading from the storage process.
        Parameters
        ----------
        files: list of the files' paths to download.
        Returns
        -------

        """
        raise NotImplementedError

    @abstractmethod
    def get_all_files(self) -> list[str]:
        """Get a list of files to paginate from the storage"""
        raise NotImplementedError

    def _format_wrapper(self, value) -> dict[str, str]:
        """
        Convert path value to output format
        {
          "path": <path_value>
        }
        Parameters
        ----------
        value

        Returns
        -------
        Formatted dict with path's value
        """
        return {"path": value}

    @abstractmethod
    def format_sample_target_path(self, source_sample_path: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def upload_file_to_storage(self, bytes_content: bytes, file_name: str) -> None:
        """
        Upload file's byte's stream to storage
        Parameters
        ----------
        bytes_content: file's byte's stream
        file_name: name of the file in the storage
        Returns
        -------

        """
        raise NotImplementedError

    @abstractmethod
    def upload_all_data_to_storage(
        self, source_files: list[str], target_files: list[str]
    ) -> None:
        """
        Upload all files from the list to storage
        Parameters
        ----------
        source_files: path to files in local file system
        target_files: paths to files in target storage
        Returns
        -------
        """
        raise NotImplementedError

    @abstractmethod
    def get_skip_data_keys(
        self, file_name: str
    ) -> tuple[Optional[pd.DataFrame], set[str]]:
        """
        Get Pandas and set of
        Parameters
        ----------
        file_name: CSV file in storage
        Returns
        -------
        Tuple[pd.Dataframe with already processed samples]
        """
        raise NotImplementedError

    @abstractmethod
    def remove_file(self, path_to_file: str) -> None:
        raise NotImplementedError
