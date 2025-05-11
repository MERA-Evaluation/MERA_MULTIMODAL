import abc
from concurrent.futures import ProcessPoolExecutor
from typing import Any
import os
import sys
import logging

import requests

sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "utils")
)

from rndutils.remote.cloud import CloudS3
from archivers import DummyArchive
from di import get_archiver


logger = logging.getLogger(__name__)


class BaseMap(abc.ABC):
    """
    Base abstract class for DEPP map.
    """

    S3_REMOTE_MODELS_BUCKET = "rndml-stage"
    OBS_MODEl_PATH = ""
    LOCAL_PATH = "./"
    RESULT_FORMAT = ".csv"
    ML_MODELS_CONFIG: dict[str, dict[str, str]] = {}

    MAP_FIELDS = ("num_jobs",)

    def __init__(self, **kwargs) -> None:
        self.current_path = self.LOCAL_PATH
        self.map_kwargs = kwargs
        for key, value in kwargs.items():
            if key in self.MAP_FIELDS:
                setattr(self, key, value)

        config = {
            "endpoint": "https://obs.ru-moscow-1.hc.sbercloud.ru",
            "key": "MR1XDQUZGPKTVRQPSJIB",
            "secret": "X8vQ6xrDZ8MQnSHTG71wmW0SxcKLAWnDKehq6fli",
            "bucket": "rndml-stage",
        }

        cloud: CloudS3 = CloudS3(config=config)

        self.archive = get_archiver(self.map_kwargs.get("format"))

        if self.ML_MODELS_CONFIG:
            non_existent_files = self.__get_local_non_existent_files()
            if non_existent_files:
                if non_existent_files := self.check_s3_files_exists(
                    cloud, non_existent_files
                ):
                    self.download_model_data_from_s3(cloud, non_existent_files)
                else:
                    raise Exception("Models from config weren't found in OBS")
            else:
                logger.info("All ML models exist locally")

    @property
    def filter_name(self) -> str:
        return self.__class__.__name__

    def __check_local_file_exists(self, model_name: str, model_config) -> bool:
        dirname = model_config.get("dirname")
        filenames = model_config.get("filenames")
        if not dirname:
            logger.info(
                f"Local folder {dirname} for '{model_name}' doesn't configurate in class"
            )
        if not filenames:
            logger.info(
                f"Local files {filenames} of '{model_name}' doesn't configurate in class"
            )
        file_existence_flag = False
        for file in filenames:
            local_file = os.path.join(self.LOCAL_PATH, dirname, file)
            file_existence_flag = os.path.exists(local_file)
            if not file_existence_flag:
                logger.info(
                    f"File {local_file} of the model {model_name} wasn't found. Try to download file from OBS."
                )
                break
            else:
                logger.info(
                    f"File {local_file} of the model {model_name} exists locally."
                )
        return file_existence_flag

    def __get_local_non_existent_files(self):
        return {
            model: model_config
            for model, model_config in self.ML_MODELS_CONFIG.items()
            if not self.__check_local_file_exists(model, model_config)
        }

    @staticmethod
    def check_s3_path_exists(cloud, model_name: str, s3_dirname: str) -> bool:
        s3_file_existence_flag = cloud.is_dir(key=s3_dirname)
        if not s3_file_existence_flag:
            logger.info(
                f"Folder {s3_dirname} for model {model_name} doesn't exist in OBS"
            )
        return s3_file_existence_flag

    def check_s3_files_exists(
        self, cloud, non_existent_models: dict[str, dict[str, str]]
    ) -> dict[str, dict[str, str]]:
        """"""
        return {
            model: model_config
            for model, model_config in non_existent_models.items()
            if self.check_s3_path_exists(cloud, model, model_config.get("dirname"))
        }

    def download_model_data_from_s3(
        self, cloud, non_existent_models: dict[str, dict[str, str]]
    ) -> None:
        for model, model_config in non_existent_models.items():
            cloud_dir_path = model_config.get("dirname")
            os.makedirs(cloud_dir_path, exist_ok=True)
            logger.info(f"Downloading model from {cloud_dir_path}")
            for file, url in zip(
                model_config.get("filenames"), model_config.get("urls")
            ):
                cloud_file_path = os.path.join(cloud_dir_path, file)
                if cloud.is_file(cloud_file_path):
                    local_path = os.path.join(cloud_dir_path, file)
                    self.download_s3_public_object(url, local_file_path=cloud_file_path)
                    logger.info(
                        f"File {cloud_file_path} was downloaded from OBS to {local_path}"
                    )
                else:
                    logger.error(f"File {cloud_file_path} wasn't found in OBS")
                    raise ValueError(f"File {cloud_file_path} wasn't found in OBS")

    @staticmethod
    def download_s3_public_object(url: str, local_file_path: str) -> None:
        """
        Download file from s3 with ACL public-read.
        Parameters
        ----------
        url: url to file
        local_file_path: path to file on the local file system
        Returns
        -------
        """
        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open(local_file_path, "wb") as f:
                    f.write(response.content)
            else:
                logger.error(
                    f"Failed to download file from {url}. Status code: {response.status_code}"
                )
        except Exception as e:
            logger.error(f"Something went wrong during downloading file {url}: {e}")

    @abc.abstractmethod
    def apply_for_file(self, context_data: dict[str:Any], **kwargs) -> dict[str, Any]:
        """
        Apply DEPP map to a file on the local file system.
        Parameters
        ----------
        sample_path
        Path to file on the local file system.
        context_data
        Context file example: label, target ...
        Returns
        -------
        Tuple of (
        [[box for word_1], [box for word_2], ...],
        imagetext,
        [word_1_language, word_2_language]
        )
        """
        raise NotImplementedError

    def open_archives(self, batch_context_data: list[dict[str:Any]]) -> list[str]:
        return self.archive.open_archives(
            batch_context_data, self.map_kwargs.get("archive_content_format")
        )

    def apply_for_files(
        self, batch_context_data: list[dict[str:Any]], **kwargs
    ) -> list[dict[str, Any]]:
        """
        Apply DEPP map for images from specified list param
        Parameters
        ----------
        List of samples paths to process
        batch_context_data

        Returns
        -------
        List of calculated metrics for images
        """
        num_jobs = getattr(self, "num_jobs", 4)

        if num_jobs == 1:
            metrics = list(map(self.apply_for_file, batch_context_data))
            metrics = list(filter(None, metrics))
            return metrics

        with ProcessPoolExecutor(max_workers=num_jobs) as executor:
            metrics = list(
                executor.map(self.apply_for_file, batch_context_data),
            )
            metrics = list(filter(None, metrics))
            return metrics

    def process_content(
        self, batch_context_data: list[dict[str:Any]]
    ) -> list[dict[str, Any]]:
        self.open_archives(batch_context_data)
        result = self.apply_for_files(batch_context_data)
        return result

    def extend_context_via_archive_data(
        self, batch_context_data: list[dict[str:Any]], files: list[dict[str:Any]]
    ) -> list[dict[str, Any]]:
        """
        Map data from context to each extracted file from archive.
        Parameters
        ----------
        batch_context_data:
        files: extracted list of files' paths from archive

        Returns
        -------

        """
        if len(batch_context_data[0]) > 1:
            archives_file_distribution = {}
            for file in files:
                arch_name = os.path.dirname(file) + self.archive.FORMAT
                archives_file_distribution.setdefault(arch_name, [])
                archives_file_distribution[arch_name].append(file)
            result = []
            for sample in batch_context_data:
                arch_name = sample.pop("path")
                for archive in archives_file_distribution.get(arch_name):
                    new_dict = {**{"path": archive}, **sample}
                    result.append(new_dict)
            return result
        else:
            return files

    def run(
        self, batch_context_data: list[dict[str:Any]], **kwargs
    ) -> list[dict[str, Any]]:
        """
        Run applying filter business logic to all files.
        Parameters
        ----------
        batch_context_data
        Context for batch data
        Returns
        -------
        Result of function apply_for_files call
        """

        if not isinstance(self.archive, DummyArchive):
            sample_paths = list(
                map(lambda sample_data: sample_data.get("path"), batch_context_data)
            )
            files = self.open_archives(sample_paths)
            files = list(map(lambda file: {"path": file}, files))
            batch_context_data = self.extend_context_via_archive_data(
                batch_context_data, files
            )
        result = self.apply_for_files(batch_context_data, **kwargs)
        return result
