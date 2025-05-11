import logging
from typing import Generator, Any
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    def __init__(self, client):
        self.client = client

    @property
    def target_folder(self) -> str:
        """
        Wrap getter for target_folder filed of a Client() object.
        Returns
        -------
        Client().target_folder
        """
        return self.client.target_folder

    @staticmethod
    def format_depp_map_output(**kwargs) -> dict[str, Any]:
        """
        Convert DEPP map output value to format
        {
          "path": <path_value>,
          <metric_field_1>: <metric_field_1_value>,
          <metric_field_2>: <metric_field_2_value>,
          ...
        }
        Parameters
        ----------
        kwargs
        Returns
        -------
        """
        return kwargs

    @abstractmethod
    def extract(self) -> Generator[dict[str, Any], None, None]:
        """
        Create a generator object extracting
        {
          "path": <path_value>,
          <metric_field_1>: <metric_field_1_value>,
          <metric_field_2>: <metric_field_2_value>,
          ...
        }
        dictionaries from source storage.
        Returns
        --------
        Generator object
        """
        raise NotImplementedError

    def run_worker(self, files: list[str]) -> None:
        """
        Wrap client's method run_worker.
        Parameters
        ----------
        files: files to download from source to target storage.
        Returns
        -------
        """
        self.client.run_worker(files)

    def format_sample_local_path(self, path_in_prefix: str) -> str:
        """
        Wrap client's method format_sample_local_path.
        Parameters
        ----------
        path_in_prefix: path to file in the source
        Returns
        -------
        Path to file in the local file system.
        """
        return self.client.format_sample_local_path(path_in_prefix)
