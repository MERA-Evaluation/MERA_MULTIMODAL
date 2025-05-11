from typing import Optional, Any
from abc import ABC, abstractmethod
import os

import pandas as pd


class BaseCheckout(ABC):
    CHECKOUT_NAME: Optional[str] = None
    CHECKOUT_CRITERION_NAME: Optional[str] = None
    CHECKOUT_FIELDS = ("criterion_name", "criterion_success", "missed_samples")

    def __init__(self, client):
        self.client = client

    @abstractmethod
    def get_failed_samples_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get Pandas Dataframe with data that doesn't pass checkout.
        Parameters
        ----------
        df: Pandas DataFrame with all checkouts data.
        Returns
        -------
        Pandas DataFrame with failed samples.
        """
        raise NotImplementedError

    def transform_checkout_result_to_output_format(
        self, *args, **kwargs
    ) -> dict[str, Any]:
        """

        Parameters
        ----------
        args
        kwargs

        Returns
        -------

        """
        formatted_result = {}
        for arg_name, arg_value in zip(self.CHECKOUT_METRICS, args):
            formatted_result[arg_name] = arg_value
        formatted_result = {**formatted_result, **kwargs}
        return formatted_result

    def save_failed_samples(self, folder: str, df: pd.DataFrame) -> None:
        file_path = os.path.join(folder, self.CHECKOUT_NAME + ".csv")
        checkout_df = self.get_failed_samples_dataframe(df)
        df_bytes = checkout_df.to_csv(index=False).encode("utf-8")
        self.client.upload_file_to_storage(df_bytes, file_path)

    def get_failed_samples_data(
        self, failed_samples_folder: str, df: pd.DataFrame
    ) -> pd.DataFrame:
        failed_samples_df = self.get_failed_samples_dataframe(df)
        len_df_checkout = failed_samples_df.shape[0]
        criterion_success = len_df_checkout == 0
        values = (self.CHECKOUT_CRITERION_NAME, criterion_success, len_df_checkout)
        df = pd.DataFrame(
            {
                self.CHECKOUT_FIELDS[i]: [values[i]]
                for i in range(len(self.CHECKOUT_FIELDS))
            }
        )
        if failed_samples_df.shape[0] != 0:
            self.save_failed_samples(failed_samples_folder, failed_samples_df)
        return df

    def run_checkout(self, failed_samples_folder, df):
        df = self.get_failed_samples_data(failed_samples_folder, df)
        return df
