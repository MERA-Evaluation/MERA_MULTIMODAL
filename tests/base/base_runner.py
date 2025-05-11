import abc
import argparse
import os.path
import sys
import logging
from typing import Any, TypeVar, Callable

sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "utils")
)

from di import get_pagination_func
from base_map import BaseMap
from core_utils import call_with_params_inspection


F = TypeVar("F", bound=Callable[..., Any])
logger = logging.getLogger(__name__)


class BaseRunner:
    CSV_PATH_FIELD_NAME = "path"

    S3_ARGS = (
        "endpoint_url",
        "access_key",
        "secret_key",
        "bucket",
        "prefix",
        "count_download_file",
    )

    @staticmethod
    def _parse_cmd_kwargs() -> dict[str, Any]:
        """
        Parse parameters that were
        passed as cmd arguments
        Parameters
        ----------
        Returns
        -------
        Dict of parsed parameters
        """
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--num_jobs",
            type=int,
            required=True,
            default=1,
        )
        parser.add_argument(
            "--endpoint_url",
            required=False,
            type=str,
        )
        parser.add_argument(
            "--access_key",
            required=False,
            type=str,
        )
        parser.add_argument(
            "--secret_key",
            required=False,
            type=str,
        )
        parser.add_argument(
            "--bucket",
            required=False,
            type=str,
        )
        parser.add_argument(
            "--prefix",
            required=True,
            type=str,
        )
        parser.add_argument(
            "--count_download_file",
            required=True,
            type=int,
        )
        parser.add_argument(
            "--result_file_name",
            required=False,
            type=str,
        )
        parser.add_argument("--format", required=True, type=str)

        parser.add_argument("--archive_content_format", required=False, type=str)

        parser.add_argument("--is_use_k8s_mount", required=True, default=0, type=int)

        parser.add_argument(
            "--type_pagination", required=True, default="local_prefix", type=str
        )

        args, _ = parser.parse_known_args()

        args = vars(args)
        return args

    def get_files_type(self) -> str:
        """
        Define type of dataset files: archive (tar, zip, etc)
        or ordinary flat files (jpeg, png, etc).
        """
        return self.map_args.get("format")

    def open_archives(self, batch_context_data: list[dict[str:Any]]) -> list[str]:
        return self.map_obj.open_archives(batch_context_data)

    def unpack_data(
        self, batch_context_data: list[dict[str:Any]]
    ) -> list[dict[str:Any]]:
        """
        Unpack archives.
        Parameters
        ----------
        batch_context_data
        [{'path': archive_1.tar, 'text'}, ...]

        Returns
        -------

        """
        sample_paths = list(
            map(lambda sample_data: sample_data.get("path"), batch_context_data)
        )
        archives_contents = self.open_archives(sample_paths)
        result = []
        for sample_path in archives_contents:
            result.append({"path": sample_path})
        return result

    def run_calculations(self, batch_context_data: list[dict[str:Any]], **kwargs):
        """
        Create instance of Filter class using *args and **kwargs
        and run method 'map' of Map instance for specified files paths
        Parameters
        ----------
        paths - paths to dataset files
        args - positional parameters
        kwargs - key-value parameters

        Returns
        -------

        """
        return self.map_obj.run(batch_context_data, **kwargs)

    @staticmethod
    def create_file_manager(pagination_func: F, func_params: dict[str, Any]):
        return call_with_params_inspection(pagination_func, func_params)

    def __init__(self, map_cls):
        args = self._parse_cmd_kwargs()
        args["prefix"] = args["prefix"].rstrip("/")
        args["is_use_k8s_mount"] = bool(args["is_use_k8s_mount"])
        self.map_args = args
        self.sample_format = self.map_args.get("format")
        get_file_manager = get_pagination_func(self.map_args.get("type_pagination"))
        self.file_manager = self.create_file_manager(get_file_manager, self.map_args)

        self.map_args["client"] = self.file_manager.extractor.client
        self.map_obj: BaseMap = map_cls(**self.map_args)

        for key, map_arg in self.map_args.items():
            setattr(self, key, map_arg)

    @abc.abstractmethod
    def run(self) -> None:
        """
        Run applying map functionality to downloaded dataset files
        Returns
        -------
        """
        raise NotImplementedError
