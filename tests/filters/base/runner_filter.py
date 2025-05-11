import os.path
import sys
import logging
from typing import Any, Optional
import warnings
import argparse

import pandas as pd

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.extend([os.path.join(base_dir, "base"), os.path.join(base_dir, "utils")])

from base_runner import BaseRunner


logger = logging.getLogger(__name__)


class RunnerFilter(BaseRunner):
    @staticmethod
    def _parse_cmd_kwargs() -> dict[str, Any]:
        """
        Parse parameters of filter and s3 client that were
        passed as cmd arguments
        Parameters
        ----------
        Returns
        -------
        Dict of parsed parameters
        """
        parsed_kwargs = BaseRunner._parse_cmd_kwargs()
        parser = argparse.ArgumentParser()
        parser.add_argument("--path_csv_key", required=False, default="", type=str)

        args, _ = parser.parse_known_args()

        args = vars(args)
        parsed_kwargs.update(args)
        return parsed_kwargs

    def format_sample_target_path(self, url: str) -> str:
        return self.file_manager.extractor.client.format_sample_target_path(url)

    def get_filter_name(self):
        return self.map_obj.filter_name

    def __create_predict_dataframe(
        self, batch_context_data: list[dict[str:Any]], **kwargs
    ) -> pd.DataFrame:
        """
        Get dataframe with calculated dataset metrics and
        reformat local file paths to S3 remote.
        Returns
        -------
        Pandas DataFrame with calculated dataset metrics
        """
        predict = self.run_calculations(batch_context_data=batch_context_data, **kwargs)
        if predict:
            df_result = pd.DataFrame(predict)
            df_result["path"] = df_result["path"].apply(
                lambda url: self.format_sample_target_path(url)
            )
            filter_name = self.get_filter_name()
            df_result = df_result.add_prefix(f"{filter_name}_")
            df_result.rename(columns={f"{filter_name}_path": "path"}, inplace=True)
            return df_result

    def __concat_dataframes(
        self, df_1: pd.DataFrame, df_2: pd.DataFrame
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
            df_result = pd.concat([df_1, df_2], ignore_index=True)
            df_result.drop_duplicates(subset=[self.CSV_PATH_FIELD_NAME], keep="first")
        return df_result

    def get_skip_data_keys(
        self, file_name: str
    ) -> tuple[pd.DataFrame, Optional[set[str]]]:
        return self.file_manager.extractor.client.get_skip_data_keys(
            file_name=file_name
        )

    @property
    def target_folder(self) -> str:
        return self.file_manager.extractor.client.target_folder

    @property
    def class_file(self) -> str:
        return self.map_obj.class_file

    def paginate(self, format_name: str, skip_data_keys: Optional[set[str]]):
        return self.file_manager.paginate(format_name, skip_data_keys)

    def upload_file_to_storage(self, byte_result_data: bytes, class_file: str) -> str:
        return self.file_manager.extractor.client.upload_file_to_storage(
            byte_result_data, class_file
        )

    def run(self) -> str:
        """
        Run applying filter to downloaded dataset files
        Returns
        -------
        """

        df_result, skip_data_key = self.get_skip_data_keys(
            os.path.join(self.map_args.get("prefix"), self.class_file)
        )

        filter_extra_params = {"target_folder": self.target_folder}

        for number_batch, batch_context_data in enumerate(
            self.paginate(self.map_args.get("format"), skip_data_key)
        ):
            df_result_step = self.__create_predict_dataframe(
                batch_context_data, **filter_extra_params
            )
            if not isinstance(df_result_step, pd.DataFrame):
                continue
            if not isinstance(df_result, pd.DataFrame):
                df_result = pd.DataFrame(columns=df_result_step.columns)
            logger.info(
                "Predict batch %s file through the %s", number_batch, self.class_file
            )
            df_result = self.__concat_dataframes(df_result, df_result_step)
            byte_result_data = df_result.to_csv(index=False).encode("utf-8")
            uploaded_csv_file = self.file_manager.extractor.client.upload_result(
                byte_result_data, self.class_file
            )
            logger.info(
                f'Upload batch %s file into s3 {self.map_args.get("prefix")} prefix',
                number_batch,
            )
