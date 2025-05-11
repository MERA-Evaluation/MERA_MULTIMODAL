import logging
from io import BytesIO
from typing import Generator, Any

from botocore.exceptions import ClientError
import pandas as pd

from .base_extractor import BaseExtractor


logger = logging.getLogger(__name__)


class CSVExtractor(BaseExtractor):
    def __init__(self, client, path_csv_key: str, contain_remote_urls: bool = False):
        super().__init__(client)
        self.path_csv_key = path_csv_key
        self.contain_remote_urls = contain_remote_urls

    def get_source_file_dataframe(self) -> pd.DataFrame:
        return pd.read_csv(
            BytesIO(self.client.get_source_file(file_path=self.path_csv_key))
        )

    def _get_source_file_data(self) -> list[dict[str, Any]]:
        """
        Get a list of dictionaries with data describing 1 row in Pandas Dataframe
        created from source CSC file.
        Returns
        """
        try:
            df = self.get_source_file_dataframe()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.info("No csv file %s", self.path_csv_key)
            raise Exception(f"No csv file {self.path_csv_key}")
        except FileNotFoundError as err:
            logger.error("File %s doesn't exist", self.path_csv_key)
            raise err
        return df.to_dict("records")

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
        for row in self._get_source_file_data():
            yield row
