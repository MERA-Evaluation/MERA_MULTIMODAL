import os.path
import urllib.parse
from functools import reduce
from typing import List, Union

import pandas as pd

from rndutils.remote.cloud import CloudS3
from rndutils.utils.logger import get_logger

logger = get_logger(__name__)


class CSVPublisher:
    def __init__(
        self,
        s3_config_key: str,
        folders_to_publish: Union[str, List[str]],
        publishing_content_type: str = None,
        fix_acl_before_publish: bool = False,
        content_url_column_name: str = "url",
        content_type_column_name: str = "type",
    ):
        """
        Publish files on S3 and dump links on it to CSV file

        Parameters
        ----------
        s3_config_key : key for S3 connection in config
        folders_to_publish : concrete folder or list of folders to publish
        publishing_content_type : type of publishing contents (image or video or else)
        fix_acl_before_publish : flag of fix ACL on file before publish (apply public-read ACL on file before publish)
        content_url_column_name : name of column with URL in result CSV file
        content_type_column_name : name of column with content type in result CSV file
        """
        self._s3_client = CloudS3(destination=s3_config_key)
        self._folders_to_publish = folders_to_publish
        self._fix_acl_before_publish = fix_acl_before_publish
        self._s3_bucket = self._s3_client.bucket
        self.publishing_content_type = publishing_content_type
        self._s3_endpoint = (
            self._s3_client.endpoint.replace("http://", "")
            .replace("https://", "")
            .strip("/")
        )
        self._content_url_column_name = content_url_column_name
        self._content_type_column_name = content_type_column_name

    def __get_files_to_publish(self) -> List[str]:
        """
        Get all files to publish

        Returns
        -------
        List of paths to files on S3
        """
        logger.info("ls files to publish")
        if isinstance(self._folders_to_publish, list):
            files_to_publish = []
            for folder in self._folders_to_publish:
                files_to_publish.append(
                    self._s3_client.ls_folder_recursively(key=folder)
                )
            return reduce(
                lambda list_first, list_next: list_first + list_next, files_to_publish
            )
        elif isinstance(self._folders_to_publish, str):
            return self._s3_client.ls_folder_recursively(key=self._folders_to_publish)

    def publish(self, csv_filename: str):
        """
        Prepare CSV file with links to file on S3
        Parameters
        ----------
        csv_filename : name of result CSV file
        """
        publish_links = []
        logger.info("Prepare public links")

        for file_to_publish in self.__get_files_to_publish():
            file_to_publish = urllib.parse.quote(file_to_publish)
            if self._s3_endpoint == "obs.ru-moscow-1.hc.sbercloud.ru":
                publish_link = (
                    f"https://{self._s3_bucket}.{self._s3_endpoint}/{file_to_publish}"
                )
            else:
                publish_link = (
                    f"https://{self._s3_endpoint}/{self._s3_bucket}/{file_to_publish}"
                )

            if self._fix_acl_before_publish:
                self._s3_client.publish(path=file_to_publish)

            if self.publishing_content_type:
                publish_links.append([publish_link, self.publishing_content_type])
            else:
                publish_links.append(publish_link)

        if self.publishing_content_type:
            columns = [self._content_url_column_name, self._content_type_column_name]
        else:
            columns = [self._content_url_column_name]
        links_to_public_df = pd.DataFrame(data=publish_links, columns=columns)
        csv_dir = os.path.dirname(csv_filename)
        if csv_dir and not os.path.exists(csv_dir):
            os.makedirs(csv_dir)
        logger.info("Write publish result to CSV")
        links_to_public_df.to_csv(csv_filename, sep=",", encoding="utf-8", index=False)
