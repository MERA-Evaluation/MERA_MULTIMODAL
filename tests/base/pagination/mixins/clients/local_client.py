import os
import logging
from typing import Optional
from io import BytesIO
import shutil

import pandas as pd

from .base_client import BaseClient


logger = logging.getLogger(__name__)


class LocalClient(BaseClient):
    def __init__(self, prefix: Optional[str] = None, meta_folder: Optional[str] = None):
        # root_folder - folder with source data that will be paginated
        # target_folder - folder where batches for processing will be located
        self.root_folder = prefix
        self.target_folder = prefix if prefix else "default"
        self.meta_folder = meta_folder

    def get_source_file(self, file_path: str) -> bytes:
        with open(file_path, "rb") as file:
            return file.read()

    def get_source_file_by_abs_path(self, file_abs_path: str) -> bytes:
        return self.get_source_file(file_abs_path)

    def run_worker(self, files: list[str]) -> None:
        if self.target_folder != self.root_folder:
            for file in files:
                file_name = os.path.basename(file)
                file_subfolder = os.path.dirname(file).strip("/")
                os.makedirs(
                    os.path.join(self.target_folder, file_subfolder), exist_ok=True
                )
                target_file = os.path.join(
                    self.target_folder, file_subfolder, file_name
                )
                shutil.copy2(file, target_file)

    def get_all_files(self):
        filepaths = []
        for dirpath, dirnames, filenames in os.walk(self.root_folder):
            for filename in filenames:
                relative_path = os.path.relpath(
                    os.path.join(dirpath, filename), self.root_folder
                )
                filepaths.append(relative_path)
        yield filepaths

    def process_client_data(self, client_data):
        for files in client_data:
            for path in files:
                yield os.path.join(self.root_folder, path)

    def format_sample_target_path(self, source_sample_path: str) -> str:
        return os.path.join("/", *source_sample_path.split("/")[1:])

    @staticmethod
    def format_sample_local_path(storage_sample_path: str) -> str:
        return storage_sample_path

    def upload_file_to_storage(self, bytes_content: bytes, file_name: str) -> str:
        if not file_name.startswith(self.target_folder):
            file_name = os.path.join(self.target_folder, file_name)
            folder = os.path.dirname(file_name)
            os.makedirs(folder, exist_ok=True)
        with open(file_name, "wb") as file:
            file.write(bytes_content)
        return file_name

    def upload_result(self, bytes_content: bytes, file_name: str) -> str:
        with open(os.path.join(self.meta_folder, file_name), "wb") as file:
            file.write(bytes_content)
        return file_name

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
        target_folder = os.path.dirname(target_files[0])
        source_folder = os.path.dirname(source_files[0])
        os.makedirs(target_folder, exist_ok=True)
        for source_file, target_file in zip(source_files, target_files):
            shutil.copy2(source_file, target_file)
        shutil.rmtree(source_folder)

    def get_skip_data_keys(
        self, file_name: str
    ) -> tuple[Optional[pd.DataFrame], set[str]]:
        try:
            df_result = pd.read_csv(BytesIO(self.get_source_file(file_name)))
            skip_data_key = {value for value in df_result["path"].to_dict().values()}
            logger.info(
                "Get csv file %s with intermediate results from local file system",
                file_name,
            )
            return df_result, skip_data_key
        except Exception:
            logger.info("Create new result filter file %s", file_name)
            return None, set()

    def remove_file(self, path_to_file: str) -> None:
        os.remove(path_to_file)
