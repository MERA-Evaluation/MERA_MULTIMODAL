import os
import sys
from typing import TypeVar, Callable, Optional

import boto3
from botocore.client import Config

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "filters")
)

from checkouts.base.base_checkout import BaseCheckout
from pagination.mixins.clients.local_client import LocalClient
from pagination.mixins.clients.s3_client import S3Client
from pagination.mixins.extractors.prefix_extractor import PrefixExtractor
from pagination.mixins.extractors.csv_extractor import CSVExtractor
from pagination.file_manager import FileManager
from collectors.collector import RunnerCollector
from archivers import ZipArchive, TarArchive, Archive, DummyArchive
from pagination.mixins.clients.base_client import BaseClient
from core_utils import call_with_params_inspection
from checkouts.projects_configs import PROJECTS_CONFIGS


T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., FileManager])


def checkout_factory(
    checkout_name: str, client, project_name: Optional[str] = "common", **kwargs
) -> BaseCheckout:
    if not project_name:
        project_name = "common"
    checkouts = PROJECTS_CONFIGS.get(project_name)
    checkouts_names = [checkout.CHECKOUT_NAME for checkout in checkouts]
    search_index = dict(zip(checkouts_names, checkouts))
    checkout_class = search_index.get(checkout_name)
    if not checkout_class:
        raise KeyError(f"{checkout_name} not in {list(search_index.keys())}")
    checkout_object = checkout_class(client, **kwargs)
    return checkout_object


def get_boto3_client(
    endpoint_url: str, access_key: str, secret_key: str
) -> boto3.client:
    """
    Create boto3 object to interact with s3  as a dependency injection pattern.
    Parameters
    ----------
    endpoint_url: S3 endpoint
    access_key: user's S3 access key
    secret_key: user's S3 secret key
    Returns
    -------
    Boto3 client
    """
    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(s3={"addressing_style": "virtual", "max_pool_connections": 100}),
    )


def get_prefix_local_pagination(prefix: str, count_download_file: int) -> FileManager:
    """
    Create a paginator object as a dependency injection pattern for pagination through the local file system
    using prefix to get all files.
    Parameters
    ----------
    prefix: path to folder with files
    count_download_file: files amount in 1 batch
    Returns
    -------
    File manager object to paginate
    """
    client = LocalClient(prefix=prefix, meta_folder=prefix)
    extractor = PrefixExtractor(client, prefix)
    paginator = FileManager(extractor, count_download_file=count_download_file)
    return paginator


def get_csv_local_pagination(
    path_csv_key: str, prefix: str, count_download_file: int, contain_remote_urls=False
) -> FileManager:
    """
    Create a paginator object as a dependency injection pattern for pagination through the local file system using CSV
    file to get all files.
    Parameters
    ----------
    prefix: path to folder with result_meta data
    path_csv_key: path to csv file with data
    count_download_file: files amount in 1 batch
    contain_remote_urls: flag, True if paths in CSV file in remote style format, False - local style format.
    Returns
    -------
    File manager object to paginate
    """
    client = LocalClient(meta_folder=prefix)
    extractor = CSVExtractor(
        client, path_csv_key, contain_remote_urls=contain_remote_urls
    )
    paginator = FileManager(extractor, count_download_file=count_download_file)
    return paginator


def get_prefix_s3_pagination(
    endpoint_url: str,
    access_key: str,
    secret_key: str,
    bucket: str,
    prefix: str,
    count_download_file: int,
    target_folder: str = "default",
) -> FileManager:
    """
    Create a paginator object as a dependency injection pattern for pagination through the s3 using prefix to
    get all files.
    Parameters
    ----------
    endpoint_url: S3 endpoint
    access_key: user's S3 access key
    secret_key: user's S3 secret key
    bucket: bucket with source files
    prefix: path to folder with source files inside in bucket
    count_download_file: files amount in 1 batch
    target_folder: folder to download files
    Returns
    -------
    File manager object to paginate
    """
    client = S3Client(
        get_boto3_client(endpoint_url, access_key, secret_key),
        endpoint_url,
        bucket,
        prefix,
        target_folder,
    )
    extractor = PrefixExtractor(client, prefix)
    paginator = FileManager(extractor, count_download_file=count_download_file)
    return paginator


def get_csv_s3_pagination(
    endpoint_url: str,
    access_key: str,
    secret_key: str,
    bucket: str,
    prefix: str,
    path_csv_key: str,
    count_download_file: int,
    target_folder: str = "default",
    contain_remote_urls=True,
):
    """
    Create a paginator object as a dependency injection pattern for pagination through the s3 using CSV file to
    get all files.
    Parameters
    ----------
    endpoint_url: S3 endpoint
    access_key: user's S3 access key
    secret_key: user's S3 secret key
    bucket: bucket with source files
    prefix: path to folder with source files inside in bucket
    path_csv_key: path to csv file with data
    count_download_file: files amount in 1 batch
    target_folder: folder to download files
    contain_remote_urls: flag, True if paths in CSV file in remote style format, False - local style format
    Returns
    ------
    File manager object to paginate-
    """
    client = S3Client(
        get_boto3_client(endpoint_url, access_key, secret_key),
        endpoint_url,
        bucket,
        prefix,
        target_folder,
    )
    extractor = CSVExtractor(client, path_csv_key, contain_remote_urls)
    paginator = FileManager(extractor, count_download_file=count_download_file)
    return paginator


def get_local_client(prefix: str) -> LocalClient:
    return LocalClient(prefix)


def get_s3_client(
    endpoint_url,
    access_key,
    secret_key,
    bucket,
    prefix,
    target_folder: Optional[str] = None,
) -> S3Client:
    return S3Client(
        get_boto3_client(endpoint_url, access_key, secret_key),
        endpoint_url,
        bucket,
        prefix,
        target_folder,
    )


def get_client(run_type: str) -> BaseClient:
    create_client_funcs = {
        "local": get_local_client,
        "s3": get_s3_client,
    }
    create_client_func = create_client_funcs.get(run_type)
    if not create_client_funcs:
        raise KeyError("run type %s doesn't associated with any client", run_type)
    return create_client_func


def get_runner_collector(
    run_type: str,
    input_folder: str,
    filters: list[str],
    files_local_folder: str,
    result_file: str,
    **kwargs,
) -> RunnerCollector:
    """
    Create a paginator object as a dependency injection pattern for pagination through the s3 using CSV file to
    get all files.
    Parameters
    ----------
    prefix
    run_type:
    filters: list of files with filter results
    files_local_folder: path to folder with files with filters' results
    result_file: result CSV file with aggregated data
    kwargs: client params
    Returns
    -------
    RunnerCollector object
    """
    kwargs["result_file_name"] = result_file
    client_class = get_client(run_type)
    client = call_with_params_inspection(
        client_class,
        kwargs,
    )
    return RunnerCollector(
        client, input_folder, filters, files_local_folder, result_file
    )


def get_pagination_func(pagination_type: str) -> F:
    """
    Get function to create a file manager of a certain type.
    Parameters
    ----------
    pagination_type
    Returns
    -------
    Function to create a file manager
    """
    pagination_types = {
        "local_prefix": get_prefix_local_pagination,
        "local_csv": get_csv_local_pagination,
        "local_docker_prefix": get_prefix_local_pagination,
        "local_docker_csv": get_csv_local_pagination,
        "s3_prefix": get_prefix_s3_pagination,
        "s3_csv": get_csv_s3_pagination,
        "s3_docker_prefix": get_prefix_s3_pagination,
        "s3_docker_csv": get_csv_s3_pagination,
    }
    pagination_func = pagination_types.get(pagination_type)
    if not pagination_func:
        raise KeyError(f"Incorrect pagination type '{pagination_type}' was passed")
    return pagination_func


def get_archiver(file_type: str) -> Archive:
    """
    Create an archiver object as a dependency injection pattern.
    Parameters
    ----------
    file_type:
    Returns
    -------
    Archive object
    """
    archivers = {"tar": TarArchive(), "zip": ZipArchive()}
    if not (archiver := archivers.get(file_type)):
        return DummyArchive()
    return archiver
