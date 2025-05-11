#!/usr/bin/env python3
"""
Script to manage cloud datasets
"""

import logging
import os
from collections import ChainMap
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from typing import List, Optional, Tuple, Union

import boto3
import urllib3
import yaml
from botocore.config import Config
from botocore.exceptions import ClientError
from PIL import ImageFile
from tqdm import tqdm

from rndutils.utils.config import CONFIGS
from rndutils.utils.func import Runnable
from rndutils.utils.os import walk

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

CWD_PATH = os.getcwd()
DATASET_FILE = "dataset.tsv"
HYP_FILE = "dataset.jsonl"
DATASETS_LIST_FILE = "datasets.yaml"


class BotoClient(Runnable):
    """Wrapper for the boto3 client, to simplify handling config and to store default params

    Parameters
    ----------
    destination : str
        Prefix destination for cloud config. For example "public" -> "public_cloud"
    config : dict
        Config dict with credentials.
    config_path : str
        Path to config with credentials
    bucket : str
        Cloud bucket for uploads

    Notes
    -----

    Config example: ~/.config.cfg:
        cloud:
          <destination>:
            bucket: <bucket>
            endpoint: https://...
            key: <access_key>
            secret: <secret_key>
    """

    EXPIRE = 3
    CONTENT_TYPE = "auto"
    CONFIG = {
        "service_name": "s3",
        "region_name": "ru",
        "verify": False,
        "aws_access_key_id": None,
        "aws_secret_access_key": None,
        "endpoint_url": None,
    }

    def __init__(
        self,
        destination: str,
        config: Optional[dict] = None,
        config_path: Optional[str] = None,
        bucket: Optional[str] = None,
        **params,
    ):
        if config is None:
            if config_path is None:
                config_path = CONFIGS

            config_path = os.path.expanduser(config_path)

            if os.path.isfile(config_path):
                conf = yaml.safe_load(open(config_path))
            else:
                raise FileNotFoundError(f"[FAIL]: Cannot read from: {config_path}")
            config = conf["cloud"][destination]

        if params:
            logger.warning(f"Specified unused params {params}")

        self.bucket = bucket if bucket is not None else config.get("bucket")
        self.expire = self.EXPIRE * 24 * 3600
        self.endpoint = config["endpoint"]

        boto_config = dict(self.CONFIG)
        config_with_retries = Config(retries={"max_attempts": 50})
        boto_config.update(
            {
                "aws_access_key_id": config["key"],
                "aws_secret_access_key": config["secret"],
                "endpoint_url": config["endpoint"],
                "config": config_with_retries,
            }
        )
        self.client = boto3.client(**boto_config)

    def _construct_url(self, file_name: str, bucket: Optional[str] = None):
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": file_name},
            ExpiresIn=self.expire,
        )

    def _key_existing_size(self, bucket, key):
        """
        :return: the key's size if it exists, else None
        """
        response = self.client.list_objects_v2(
            Bucket=bucket,
            Prefix=key,
        )
        for obj in response.get("Contents", []):
            if obj["Key"] == key:
                return obj["Size"]
        return None

    def is_dir(self, key, bucket: Optional[str] = None):
        bucket = bucket if bucket is not None else self.bucket

        if not key.endswith("/"):
            key = key + "/"
        response = self.client.list_objects_v2(Bucket=bucket, Prefix=key)
        exists = len(response.get("Contents", [])) > 0
        is_file_ = (
            len(
                [
                    o
                    for o in response.get("Contents", [])
                    if o["Key"] == key and o["Size"] > 0
                ]
            )
            > 0
        )

        return exists and not is_file_

    def is_file(self, key, bucket: Optional[str] = None):
        bucket = bucket if bucket is not None else self.bucket

        response = self.client.list_objects_v2(Bucket=bucket, Prefix=key)
        is_file_ = (
            len(
                [
                    o
                    for o in response.get("Contents", [])
                    if o["Key"] == key and o["Size"] > 0
                ]
            )
            > 0
        )
        return is_file_

    def publish(self, path: str, bucket: Optional[str] = None, unpublish: bool = False):
        """Publish remote cloud s3 data

        Parameters
        ----------
        bucket : str
            Bucket name for remote s3
        path : str
            Remote path to publish
        unpublish : bool
            Make dataset unpublished
        """
        if bucket is None:
            bucket = self.bucket

        res = []
        debug_mode = logging.root.level == logging.DEBUG
        sources = self.walk(bucket, path)

        for _, src_path in tqdm(
            sources,
            total=len(sources),
            disable=debug_mode,
            ncols=100,
            position=0,
            desc="Publishing sources",
        ):
            url = self.endpoint + "/" + bucket + "/" + src_path
            self.client.put_object_acl(
                Bucket=bucket,
                Key=src_path,
                ACL=("private" if unpublish else "public-read"),
            )
            res.append(url)
        return res

    def update_datasets(self, bucket: str, dst):
        # Create empty file for storing datasets list, if it doesn't exist
        if not self.is_file(bucket=bucket, key=DATASETS_LIST_FILE):
            self.client.put_object(Bucket=bucket, Body="", Key=DATASETS_LIST_FILE)

        # Read file with datasets list
        response = self.client.get_object(Bucket=bucket, Key=DATASETS_LIST_FILE)
        datasets = response["Body"].read().decode("utf-8")
        if not datasets:
            datasets = ""

        dst = dst.strip("/")
        if "." in os.path.basename(dst):
            dst = os.path.basename(os.path.dirname(dst))

        # Fill file with datasets list with upload destination folder
        if dst and dst not in datasets.split("\n"):
            if not datasets:
                body = dst
            else:
                body = f"{datasets}\n{dst}"

            self.client.put_object(Body=body, Bucket=bucket, Key=DATASETS_LIST_FILE)

    def check_bucket(self, bucket_name):
        try:
            self.client.head_bucket(Bucket=bucket_name)
            print("Bucket Exists!")
            return True
        except ClientError as e:
            error_code = int(e.response["Error"]["Code"])
            if error_code == 403:
                print("Private Bucket. Access forbidden!")
                return True
            elif error_code == 404:
                print("Bucket does not exist!")
                return False

    def upload(
        self,
        src: Optional[str] = None,
        dst: Optional[str] = None,
        bucket: Optional[str] = None,
        dryrun: bool = False,
        skip_existing: bool = False,
    ):
        """Upload dataset to remote cloud s3

        Parameters
        ----------
        src : str
            Source path to data
        dst : str
            Destination path to remote
        bucket : str
            Bucket name for remote s3
        dryrun : bool
            Do nothing
        skip_existing : bool
            Skip uploading if exists
        """
        if bucket is None:
            bucket = self.bucket

        if not self.check_bucket(bucket):
            self.client.create_bucket(Bucket=bucket)

        src = os.path.expanduser(src)

        dst_is_dir = False
        src_is_dir = os.path.isdir(src)
        result = []
        if self.is_dir(dst, bucket):
            dst_is_dir = True
        elif not self.is_file(key=dst, bucket=bucket):
            dst_is_dir = src_is_dir

        dst_src = os.path.join(dst, os.path.basename(src))

        if src_is_dir and not dst_is_dir:
            raise RuntimeError(f"Couldn' copy: rndutils {src} is dir and {dst} is file")

        if src_is_dir:
            sources = [
                [abs_path, os.path.join(dst_src, rel_path)]
                for rel_path, abs_path in walk(src)
            ]
        elif dst_is_dir:
            sources = [[src, dst_src]]
        else:
            sources = [[src, dst]]

        self.update_datasets(bucket, dst)

        debug_mode = logging.root.level == logging.DEBUG
        for src_path, dst_path in tqdm(
            sources, total=len(sources), disable=debug_mode, ncols=100, position=0
        ):
            if skip_existing:
                if self.is_file(bucket=bucket, key=dst_path):
                    logger.debug(
                        f"Skip existing cp {src_path} s3://{bucket}/{dst_path}"
                    )
                    continue
            logger.debug(f"cp {src_path} s3://{bucket}/{dst_path}")
            if not dryrun:
                self.client.upload_file(src_path, bucket, dst_path)
                result.append([bucket, dst_path])
        return result

    def walk(self, bucket=None, path=None):
        if self.is_file(bucket=bucket, key=path):
            return [["", path]]
        result = []
        if not path.endswith("/"):
            path = path + "/"
        for page in self.client.get_paginator("list_objects").pagination_generator(
            Bucket=bucket, Prefix=path
        ):
            if "Contents" not in page:
                logger.debug(f"There is no such remote path: {path}")
                break
            for item in page["Contents"]:
                rel_path = item["Key"][len(path) :].lstrip("/")  # NOQA
                result.append([rel_path, item["Key"]])
        return result

    def download(
        self,
        src=None,
        dst=None,
        bucket: Optional[str] = None,
        dryrun: bool = False,
        num_samples: int = None,
    ):
        """Download dataset from remote cloud s3

        Parameters
        ----------
        src : str
            Source path to data into cloud
        dst : str
            Destination local path
        bucket : str
            Bucket name for s3
        dryrun : bool
            Do nothing
        num_samples : int
            Download only part of samples
        """
        if bucket is None:
            bucket = self.bucket

        debug_mode = logging.root.level == logging.DEBUG
        sources = self.walk(bucket=bucket, path=src)

        if num_samples is not None:
            sources = sources[:num_samples]

        for rel_path, src_path in tqdm(
            sources, total=len(sources), disable=debug_mode, ncols=100, position=0
        ):
            object_target_path = os.path.join(dst, os.path.basename(src), rel_path)
            os.makedirs(os.path.dirname(object_target_path), exist_ok=True)
            logger.debug(f"cp s3://{bucket}/{src_path} {object_target_path}")
            if not dryrun:
                self.client.download_file(bucket, src_path, object_target_path)

    def delete(self, bucket=None, src=None, force=False):
        """Delete dataset from remote cloud s3

        Deletes file or folder from s3
        If folder is deleted, it is also deleted from DATASETS_LIST_FILE

        Parameters
        ----------
        src : str
            Source path to data into cloud
        bucket : str
            Bucket name for s3
        force : bool
            Force detele

        """
        debug_mode = logging.root.level == logging.DEBUG

        if self.is_dir(src, bucket):
            sources = self.walk(bucket=bucket, path=src)
        elif self.is_file(bucket=bucket, key=src):
            sources = [["", src]]
        else:
            sources = None
            logger.error(f"No such file or directory: s3://{bucket}/{src}")
            exit(1)

        if not force:
            print(f"Are you sure you want to delete s3://{bucket}/{src}?")
            if input("(Y/N) << ").lower() not in ["yes", "y"]:
                exit(1)

        deleted_instances = []
        for _, src_path in tqdm(
            sources, total=len(sources), disable=debug_mode, ncols=100, position=0
        ):
            logger.debug(f"rm s3://{bucket}/{src_path}")
            self.client.delete_object(Bucket=bucket, Key=src_path)
            deleted_instances.append([bucket, src_path])

            # Deleting dataset path from file with datasets list
            response = self.client.get_object(Bucket=bucket, Key=DATASETS_LIST_FILE)
            datasets = response["Body"].read().decode("utf-8").split("\n")

            src = src.strip("/")
            if src in datasets:
                path_to_delete = src
            else:
                path_to_delete = ""

            if path_to_delete:
                datasets.remove(path_to_delete)
                logger.debug(f"{path_to_delete} was removed from datasets list")

            self.client.put_object(
                Body="\n".join(datasets), Bucket=bucket, Key=DATASETS_LIST_FILE
            )

        return deleted_instances

    def get_tree(self, bucket, path):
        src = [path or ""]
        res = []
        while src:
            src_new = []
            for prefix in src:
                list_objects = self.client.list_objects(
                    Bucket=bucket, Prefix=prefix, Delimiter="/"
                )
                for obj in list_objects.get("CommonPrefixes") or []:
                    if obj.get("Prefix") != prefix:
                        res += [obj.get("Prefix")]
                        src_new += [obj.get("Prefix")]
            src = src_new
        return res

    def ls_datasets(self, bucket):
        """
        Prints content of DATASETS_LIST_FILE
        """
        if not self.is_file(bucket=bucket, key=DATASETS_LIST_FILE):
            logger.error("File with datasets list doesn't exist. Please upload some.")
            exit(1)

        response = self.client.get_object(Bucket=bucket, Key=DATASETS_LIST_FILE)
        datasets = response["Body"].read().decode("utf-8")
        datasets = datasets.split("\n")

        return datasets

    def ls_folder_recursively(
        self, key, bucket: Optional[str] = None, with_folders: bool = False
    ):
        """Explore dataset from s3 folder

        Parameters
        ----------
        bucket : str
            Bucket name
        key : str
            Path to folder. Example: "dataset/"
        with_folders : bool
            Return folders list if True
        Returns
        -------
            List of files from folder and sub-folders
        """
        if bucket is None:
            bucket = self.bucket

        if self.is_file(bucket=bucket, key=key):
            return [key]

        if not self.is_dir(key, bucket):
            logger.error("No such file or directory on S3!")
            exit(1)

        if not key.endswith("/"):
            key += "/"

        files, folders = [], []
        for page in self.client.get_paginator("list_objects").pagination_generator(
            Bucket=bucket,
            Prefix=key,
        ):
            if "Contents" not in page:
                break
            for item in page["Contents"]:
                if item["Key"].endswith("/"):
                    folders.append(item["Key"])
                else:
                    files.append(item["Key"])

        if with_folders:
            return files, list(sorted(set(folders)))

        return files

    def get_path_file_set(self, key, bucket: Optional[str] = None):
        if bucket is None:
            bucket = self.bucket

        file_set = set()
        for page in self.client.get_paginator("list_objects").pagination_generator(
            Bucket=bucket,
            Prefix=key,
        ):
            if "Contents" not in page:
                break
            for item in page["Contents"]:
                if not item["Key"].endswith("/"):
                    file_set.add(item["ETag"])
        return file_set

    def ls_folder(self, folder: str, bucket: Optional[str] = None):
        """
        Prints content of folder with depth == 1 (not recursively)
        """
        if bucket is None:
            bucket = self.bucket

        if self.is_file(bucket=bucket, key=folder):
            return [folder]

        if not self.is_dir(folder, bucket):
            raise Exception(f"No such file or directory {folder}!")

        folder = f"{folder.rstrip('/')}/"

        list_objects = self.client.list_objects(
            Bucket=bucket, Prefix=folder, Delimiter="/"
        )

        objects = []

        # Looking for directories inside folder
        dirs = list_objects.get("CommonPrefixes")
        if dirs and len(dirs) > 1:
            for obj in tqdm(dirs, ncols=100, position=0):
                objects.append(obj.get("Prefix"))

        # Looking for files inside folder
        files = list_objects.get("Contents")
        if files:
            for obj in tqdm(files, ncols=100, position=0):
                objects.append(obj.get("Key"))

        return objects


class CloudS3(BotoClient):
    """Cloud Database S3"""

    def __init__(
        self,
        destination: str = "external",
        config: Optional[dict] = None,
        config_path: Optional[str] = None,
        bucket: Optional[str] = None,
    ):
        """Extended cloud s3 class

        Parameters
        ----------
        destination : str
            Prefix destination for cloud config. For example "public" -> "public_cloud"
        config : dict
            Config dict with credentials.
        config_path : str
            Path to config with credentials
        bucket : str
            Cloud bucket for uploads

        Notes
        -----

        Config example: ~/.config.cfg:
            <destination>_cloud:
            bucket: <bucket>
            endpoint: https://...
            key: <access_key>
            secret: <secret_key>

        """
        super().__init__(destination, config, config_path, bucket)
        if self.bucket is None:
            raise AttributeError(
                f"Specify bucket into config {config} or as input argument. Got {self.bucket}"
            )

    def upload_file(self, cloud_path: str, local_path: str):
        """Upload file to s3 cloud

        Parameters
        ----------
        cloud_path : str
            Target path in s3 cloud
        local_path : str
            Source local path

        """

        self.client.upload_file(local_path, self.bucket, cloud_path)

    def upload_fileobj(self, cloud_path: str, content: BytesIO):
        """Upload file to s3 cloud

        Parameters
        ----------
        cloud_path : str
            Target path in s3 cloud
        content : str
            In-memory content of the file to be uploaded

        """

        self.client.upload_fileobj(content, self.bucket, cloud_path)

    def upload_files(self, src_path: str, dst_path: str):
        """Upload files to s3 remote

        Parameters
        ----------
        src_path : str
            Source path into s3 cloud
        dst_path : str
            Target local path

        """
        self.upload(src=src_path, dst=dst_path, bucket=self.bucket)

    def copy_file(self, src_path: str, dst_path: str):
        """Copy file from one s3 bucket location to another

        Parameters
        ----------
        src_path : str
            Source path into s3 cloud
        dst_path : str
            Target local path

        """
        self.client.copy(
            CopySource={"Bucket": self.bucket, "Key": src_path},
            Bucket=self.bucket,
            Key=dst_path,
        )

    def download_file(self, cloud_path: str, local_path: str):
        """Download file from s3 cloud

        Parameters
        ----------
        cloud_path : str
            Source path into s3 cloud
        local_path : str
            Target local path

        """
        try:
            self.client.download_file(self.bucket, cloud_path, local_path)
        except ClientError:
            logger.info(f"{cloud_path} not found at S3...")
            return cloud_path

    def download_dataset(
        self,
        sources: list,
        local_path: str,
        num_samples: int = None,
        num_jobs: int = 1,
        with_path: bool = False,
        rm_path: str = None,
    ):
        """Download dataset from cloud to local path

        Parameters
        ----------
        sources : str
            List of items to download
        local_path : str
            Target local path
        num_samples : int
            Samples to download
        num_jobs : int
            Number of workers. Default: 1
        with_path : bool
            Save with full path. Default: False
        rm_path : str
            Do left strip for path if with_path.
        """
        if isinstance(num_samples, int) and num_samples > 0:
            sources = sources[:num_samples]

        def _single_download(src_path: str):
            if with_path:
                local_file = os.path.join(local_path, src_path.lstrip(rm_path))
            else:
                local_file = os.path.join(local_path, os.path.basename(src_path))
            os.makedirs(os.path.dirname(local_file), exist_ok=True)

            cloud_path = os.path.join(self.endpoint, self.bucket) + "/"
            if cloud_path in src_path:
                src_path = src_path.split(cloud_path)[-1]

            if self.is_file(key=src_path) and not os.path.exists(local_file):
                self.download_file(src_path, local_file)
                return local_file

        with ThreadPoolExecutor(max_workers=num_jobs) as executor:
            passed = list(
                tqdm(
                    executor.map(_single_download, sources),
                    desc="Download dataset",
                    ncols=100,
                    position=0,
                    total=len(sources),
                )
            )

        return [item for item in passed if item is not None]

    def upload_dataset(self, sources: list, cloud_path: str):
        """Upload dataset to cloud from local path

        Parameters
        ----------
        sources : str
            List of items to upload
        cloud_path : str
            Cloud remote path
        """
        result = []
        for local_file in tqdm(
            sources, total=len(sources), disable=False, ncols=100, position=0
        ):
            cloud_file = os.path.join(cloud_path, os.path.basename(local_file))
            self.upload_file(cloud_file, local_file)
            result.append(cloud_file)
        return result

    def find_dataset(
        self,
        datapath: str,
        extensions: Optional[Union[str, Tuple]] = None,
        only_filenames: bool = False,
    ):
        """Explore dataset from s3 folder

        Parameters
        ----------
        datapath : str
            Path to dataset. Example: "dataset/"
        extensions : str
            Template for file extentions ("*.mp4, *.mov etc.). Can be string or tuple of strings.
        only_filenames : bool
            Return only filenames without

        Returns
        -------
            List of files from datapath folder

        """

        dataset = self.ls_folder_recursively(key=datapath)
        if extensions:
            dataset = [item for item in dataset if item.lower().endswith(extensions)]
        if only_filenames:
            return [os.path.basename(os.path.splitext(item)[0]) for item in dataset]
        return dataset

    def publish_dataset(self, sources: list, unpublish: bool = False):
        self.publish_sources(sources, unpublish)

    def publish_sources(self, sources: list, unpublish: bool = False):
        """Change the public data type

        Parameters
        ----------
        sources: list
            Path to data. Example: "project/data/..."
                                or "endpoint_url/bucket/project/data/...."
        unpublish: bool
            The public data type: False - public, True - private. Default: False
        """

        sources = list(
            map(
                lambda x: x.replace(
                    os.path.join(self.endpoint, self.bucket), ""
                ).lstrip("/"),
                sources,
            )
        )

        count_files = 0
        for src_path in tqdm(
            sources, desc="Publish sources", total=len(sources), ncols=100, position=0
        ):
            if self.is_file(key=src_path):
                count_files += 1

                self.client.put_object_acl(
                    Bucket=self.bucket,
                    Key=src_path,
                    ACL=("private" if unpublish else "public-read"),
                )

        logging.info(f"Input {len(sources)} files, find {count_files} files")

    def delete_sources(self, sources: list):
        for src_path in tqdm(
            sources, desc="Delete sources", total=len(sources), ncols=100, position=0
        ):
            if self.is_file(key=src_path):
                self.client.delete_object(Bucket=self.bucket, Key=src_path)

    def delete_empty_folders(self, source: str):
        files, folders = self.ls_folder_recursively(key=source, with_folders=True)
        if len(files) > 0:
            logger.info(
                f"Cannot delete some folders because of non-empty folders: {files}"
            )

        if len(folders) > 0:
            logger.info(f"Delete {len(folders)} folders.")
            deleted = dict(Objects=[{"Key": item} for item in folders])
            self.client.delete_objects(Bucket=self.bucket, Delete=deleted)

    # def is_file(self, key: str, bucket: Optional[str] = None):
    #     bucket = bucket if bucket is not None else self.bucket
    #     return super().is_file(bucket=bucket, key=key)

    @property
    def remote(self):
        return os.path.join(self.endpoint, self.bucket)

    def _get_image_shape(self, source: str, chunk_size: int = 1024) -> dict:
        image = self.client.get_object(Bucket=self.bucket, Key=source)["Body"]

        shapes = None
        parser = ImageFile.Parser()
        while True:
            chunk = image.read(chunk_size)
            if not chunk:
                break

            parser.feed(chunk)
            if parser.image:
                shapes = parser.image.size
                break
        return {source: shapes}

    def get_shapes_for_images(
        self, sources: Union[List, str], num_jobs: int = 1
    ) -> dict:
        if isinstance(sources, str):
            sources = self.find_dataset(sources)

        with ThreadPoolExecutor(num_jobs) as executor:
            shapes = list(
                tqdm(
                    executor.map(self._get_image_shape, sources),
                    desc="Getting image shapes",
                    ncols=100,
                    position=0,
                    total=len(sources),
                )
            )

        return dict(ChainMap(*shapes))

    # def get_config(self, config_path: str) -> dict:
    #     """Get configs for pipelines from s3 database"""
    #     with TempDir() as temp_dir:
    #         local_path = os.path.join(temp_dir, config_path)
    #         if not self.is_file(self.bucket, config_path):
    #             config = {}
    #         else:
    #             self.download_file(config_path, local_path)
    #             config = yaml.load(open(local_path), Loader=yaml.Loader)
    #
    #     return Dict(config)
    #
    # def put_config(self, config: dict, config_path: str):
    #     """Update configs for pipelines into s3 database
    #     """
    #     with TempDir() as temp_dir:
    #         local_path = os.path.join(temp_dir, config_path)
    #         with open(local_path, "w") as cfg:
    #             yaml.dump(config, cfg)
    #
    #         suffix = str(datetime.now())[:-7].replace(" ", "_")
    #
    #         cfg_name, cfg_fmt = os.path.splitext(os.path.basename(config_path))
    #         backup_path = os.path.join(self.BACKUP_CONF, f"{cfg_name}_{suffix}{cfg_fmt}")
    #         if self.is_file(self.bucket, config_path):
    #             self.client.copy(
    #                 CopySource={"Bucket": self.bucket, "Key": config_path}, Bucket=self.bucket, Key=backup_path
    #             )
    #
    #         self.upload_file(local_path, config_path)
