import logging
import os
import sys
import warnings
from io import BytesIO
from typing import Literal

import pandas as pd

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend(
    [
        os.path.join(os.path.dirname(base_dir), "utils"),
        os.path.join(os.path.dirname(base_dir), "logging_configuration"),
        os.path.join(os.path.dirname(base_dir), "base"),
    ]
)

from pagination.mixins.clients.base_client import BaseClient


MergeType = Literal["left", "right", "inner", "outer", "cross"]
logger = logging.getLogger(__name__)


class RunnerCollector:
    def __init__(
        self,
        client: BaseClient,
        input_folder: str,
        filters: list[str],
        files_folder: str,
        result_file_name: str,
    ):
        self.client = client
        self.input_folder = input_folder
        self.filters = filters
        self.files_folder = files_folder
        self.result_file_name = result_file_name

    @staticmethod
    def bytes_to_dataframe(data: bytes) -> pd.DataFrame:
        """
        Convert input bytes from CSV file to Pandas Dataframe.
        """
        df = pd.read_csv(BytesIO(data))
        return df

    @staticmethod
    def __dataframe_to_bytes(df: pd.DataFrame) -> bytes:
        """
        Convert Pandas Dataframe to bytes.
        Parameters
        ----------
        df

        Returns
        -------
        Bytes stream
        """
        return df.to_csv(index=False).encode("utf-8")

    def _merge_results(self) -> pd.DataFrame:
        """
        Merge each CSV file with filter result into a common CSV file.
        Returns
        -------
        Pandas DataFrame with merged data.
        """
        df_result = None
        for filter_name in self.filters:
            filter_path = os.path.join(self.input_folder, f"{filter_name}.csv")

            try:
                df_step = self.bytes_to_dataframe(
                    self.client.get_source_file_by_abs_path(filter_path)
                )
                if df_result is None:
                    df_result = df_step
                else:
                    df_result = self.__concat_dataframes(df_result, df_step)
            except Exception as err:
                logger.error("File %s doesn't exists", filter_path)
                raise err
        return df_result

    def _upload_result_to_storage(self, df: pd.DataFrame) -> None:
        """
        Upload result CSV file to target storage
        Parameters
        ----------
        df: pd.DataFrame with results
        Returns
        -------
        """
        bytes_content = self.__dataframe_to_bytes(df)
        self.client.upload_file_to_storage(bytes_content, self.result_file_name)

    @staticmethod
    def __concat_dataframes(
        df_1: pd.DataFrame,
        df_2: pd.DataFrame,
        merge_key: str = "path",
        merge_type: MergeType = "outer",
    ) -> pd.DataFrame:
        """
        Concat 2 pandas dataframes.
        Parameters
        ----------
        df_1 - dataset that accumulates the result
        df_2 - dataset that was formed on current iteration for 1 batch
        Returns
        -------
        Result of concatination of 2 datasets
        """
        with warnings.catch_warnings():
            warnings.simplefilter(action="ignore", category=FutureWarning)
            df_result = df_1.merge(df_2, on=merge_key, how=merge_type)

        return df_result

    def rm_intermediate_result(self):
        for filter_name in self.filters:
            self.client.remove_file(
                os.path.join(self.input_folder, f"{filter_name}.csv")
            )

    def run(self):
        df_result = self._merge_results()
        self._upload_result_to_storage(df_result)
        self.rm_intermediate_result()
