import logging
import os
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, wait
from io import BytesIO

import pandas as pd
from botocore.exceptions import ClientError

from .base_client import BaseClient


logger = logging.getLogger(__name__)


class S3Client(BaseClient):
    def __init__(
        self,
        boto3_client,
        endpoint_url: str,
        bucket: str,
        prefix: str,
        target_folder: str = "default",
    ):
        self.endpoint_url = endpoint_url
        self.bucket = bucket
        self.prefix = prefix
        self.boto3_client = boto3_client
        self.target_folder = target_folder

    def get_source_file_by_name(self, file_name: str) -> bytes:
        prefix_path = self.prefix
        if self.prefix[-1] != "/":
            prefix_path = self.prefix + "/"
        return (
            self.boto3_client.get_object(
                Bucket=self.bucket, Key=f"{prefix_path}{file_name}"
            )
            .get("Body")
            .read()
        )

    def get_source_file_by_abs_path(self, file_abs_path: str) -> bytes:
        return (
            self.boto3_client.get_object(Bucket=self.bucket, Key=f"{file_abs_path}")
            .get("Body")
            .read()
        )

    def get_source_file(self, file_path: str) -> bytes:
        prefix_path = self.prefix
        if self.prefix[-1] != "/":
            prefix_path = self.prefix + "/"
        return (
            self.boto3_client.get_object(
                Bucket=self.bucket, Key=f"{prefix_path}{file_path}"
            )
            .get("Body")
            .read()
        )

    def download_one_file(self, bucket: str, key: str):
        try:
            os.makedirs(
                self.target_folder + "/" + "/".join(key.split("/")[:-1]), exist_ok=True
            )
        except OSError as error:
            logger.error(f"Ошибка при создании директории: {error}")
        self.boto3_client.download_file(
            Bucket=bucket, Key=key, Filename=self.target_folder + "/" + key
        )

    def run_worker(self, files: list[str]) -> None:
        with ThreadPoolExecutor(max_workers=50) as executor:
            future_to_key = {
                executor.submit(self.download_one_file, self.bucket, key): key
                for key in files
            }
            wait(future_to_key)

    def get_all_files(self):
        self.boto3_client.get_paginator("list_objects_v2")
        paginator = self.boto3_client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=self.bucket, Prefix=self.prefix):
            x = page["Contents"]
            yield from x

    def process_client_data(self, client_data):
        for obj in client_data:
            yield obj["Key"]

    def format_sample_target_path(self, source_sample_path: str) -> str:
        """
        Format path to S3 remote file.
        Parameters
        ----------
        file_path - path to local file

        Returns
        -------
        S3 remote path
        """
        protocol, domain = self.endpoint_url.split("://")
        remote_url = protocol + "://" + self.bucket + "." + domain
        if source_sample_path.startswith(self.target_folder):
            source_sample_path = source_sample_path.replace(
                self.target_folder, "", 1
            ).strip("/")
        return f"{remote_url}/{source_sample_path}"

    def upload_file_to_storage(self, bytes_content: bytes, file_name: str) -> str:
        prefix_path = self.prefix
        if self.prefix[-1] != "/":
            prefix_path = self.prefix + "/"
        self.boto3_client.put_object(
            Bucket=self.bucket,
            Key=f"{os.path.join(prefix_path, file_name)}",
            Body=bytes_content,
        )
        return os.path.join(prefix_path, file_name)

    def upload_result(self, bytes_content: bytes, file_name: str) -> str:
        return self.upload_file_to_storage(bytes_content, file_name)

    def upload_sample_to_s3(self, file_path: str, remote_prefix: str) -> None:
        """"""
        with open(file_path, "rb") as sample_file:
            data = sample_file.read()
            self.upload_file_to_storage(file_name=remote_prefix, bytes_content=data)

    def upload_all_data_to_s3(
        self, local_files_list: list[str], prefix_list: list[str], worker: int = 50
    ):
        with ThreadPoolExecutor(max_workers=worker) as executor:
            future_to_key = {
                executor.submit(
                    self.upload_sample_to_s3, local_file_path, prefix
                ): local_file_path
                for local_file_path, prefix in zip(local_files_list, prefix_list)
            }
            wait(future_to_key)

    def get_storage_file(self, file_name: str) -> bytes:
        prefix_path = self.prefix
        if self.prefix[-1] != "/":
            prefix_path = self.prefix + "/"
        return (
            self.boto3_client.get_object(
                Bucket=self.bucket, Key=f"{os.path.join(prefix_path, file_name)}"
            )
            .get("Body")
            .read()
        )

    @staticmethod
    def format_sample_local_path(storage_sample_path: str) -> str:
        return (
            "/".join(storage_sample_path.split("/")[3:])
            if storage_sample_path.startswith("http")
            else storage_sample_path
        )

    def get_skip_data_keys(
        self, file_name: str
    ) -> tuple[Optional[pd.DataFrame], set[str]]:
        try:
            df_result = pd.read_csv(BytesIO(self.get_storage_file(file_name)))
            skip_data_key = {
                self.format_sample_local_path(value)
                for value in df_result["path"].to_dict().values()
            }
            logger.info(
                "Get csv file %s with intermediate results from s3 prefix %s",
                file_name,
                self.prefix,
            )
            return df_result, skip_data_key
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.info(
                    "No csv file %s with intermediate results in s3 prefix %s",
                    file_name,
                    self.prefix,
                )
                logger.info("Create new result filter file %s", file_name)
            return None, set()

    def upload_all_data_to_storage(
        self, source_files: list[str], target_files: list[str]
    ) -> None:
        with ThreadPoolExecutor(max_workers=50) as executor:
            future_to_key = {
                executor.submit(
                    self.upload_sample_to_s3, local_file_path, prefix
                ): local_file_path
                for local_file_path, prefix in zip(source_files, target_files)
            }
            wait(future_to_key)

    def __check_only_full_control_acl(self, grants_list: list):
        for grant in grants_list:
            if (
                grant["Grantee"]["Type"] == "Group"
                and grant["Grantee"]["URI"]
                == "http://acs.amazonaws.com/groups/global/AllUsers"
                and grant["Permission"] == "READ"
            ):
                return False
        return True

    def get_sample_acl(self, key):
        response = self.boto3_client.get_object_acl(Bucket=self.bucket, Key=key)
        return self.__check_only_full_control_acl(response.get("Grants"))

    def check_all_files_acl(self, samples: list[str], workers: int = 50):
        """
        Check that samples S3 ACL parameter equal to 'FULL_CONTROL'.
        """
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(self.get_sample_acl, sample) for sample in samples
            ]
            wait(futures)
            return [future.result() for future in futures]

    def remove_file(self, path_to_file: str) -> None:
        self.boto3_client.delete_object(Bucket=self.bucket, Key=path_to_file)
