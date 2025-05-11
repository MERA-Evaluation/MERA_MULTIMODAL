import argparse
import os
import sys
from typing import Optional
from io import BytesIO

parent_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.extend([os.path.join(parent_dir, "utils"), os.path.join(parent_dir, "base")])
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd

from di import get_client, checkout_factory
from base_checkout import BaseCheckout
from core_utils import call_with_params_inspection
from projects_configs import PROJECTS_CONFIGS


# def checkout_factory(checkout_name: str, client, project_name: Optional[str] = "common", **kwargs) -> BaseCheckout:
#     if not project_name:
#         project_name = "common"
#     checkouts = PROJECTS_CONFIGS.get(project_name)
#     checkouts_names = [checkout.CHECKOUT_NAME for checkout in checkouts]
#     search_index = dict(zip(checkouts_names, checkouts))
#     checkout_class = search_index.get(checkout_name)
#     if not checkout_class:
#         raise KeyError()
#     checkout_object = checkout_class(client, **kwargs)
#     return checkout_object


def parse_cmd_kwargs() -> dict[str, str | int]:
    """
    Parse command line params.
    Returns
    Parsed command line params as a dictionary
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("project", required=False, type=str)
    parser.add_argument("checkouts", required=False, type=str)

    args, _ = parser.parse_known_args()

    args = vars(args)

    return args


class CheckoutRunner:
    PROJECT_NAME_TEMPLATE = "{}_checkout_result.csv"
    CHECKOUT_FIELDS = ("criterion_name", "criterion_success", "missed_samples")
    CHECKOUTS_FOLDER = "checkout_data"

    def __init__(
        self,
        run_type: str,
        project: Optional[str] = None,
        checkouts: Optional[list] = None,
        result_file_name: str = "",
        all_checkouts_result_file: Optional[str] = None,
        **kwargs,
    ):
        self.project = project.lower() if project else None
        create_client_func = get_client(run_type)
        self.client = call_with_params_inspection(create_client_func, kwargs)
        self.checkouts: list[BaseCheckout] = self.__get_checkouts_objects_list(
            checkouts, self.client
        )
        self.all_checkouts_result_file = all_checkouts_result_file
        self.result_file_name = result_file_name

    def __get_checkouts_objects_list(
        self, checkouts_names: Optional[list[str]], client
    ) -> list[BaseCheckout]:
        if not checkouts_names:
            checkouts_objects_list = [
                checkout_factory(checkout.CHECKOUT_NAME, client, self.project)
                for checkout in PROJECTS_CONFIGS.get(self.project)
            ]
        else:
            checkouts_objects_list = [
                checkout_factory(checkout_name, client, self.project)
                for checkout_name in checkouts_names
            ]
        return checkouts_objects_list

    def __get_all_checkouts_result_file(self) -> str:
        if not self.all_checkouts_result_file:
            return self.PROJECT_NAME_TEMPLATE.format(
                self.project if self.project else "custom"
            )
        return self.all_checkouts_result_file

    @staticmethod
    def __add_checkout_result_to_dataframe(
        df_result: pd.DataFrame, checkout_result: pd.DataFrame
    ) -> pd.DataFrame:
        df_result = pd.concat([df_result, checkout_result])
        return df_result

    def get_source_file(self, path_to_file: str) -> bytes:
        return self.client.get_source_file(path_to_file)

    def load_to_storage(self, df: pd.DataFrame) -> None:
        byte_format_df = df.to_csv(index=False).encode("utf-8")
        file_name = self.__get_all_checkouts_result_file()
        self.client.upload_file_to_storage(byte_format_df, file_name)

    def run(self) -> None:
        df_source_data = pd.read_csv(
            BytesIO(self.get_source_file(self.result_file_name))
        )
        df_result = pd.DataFrame(columns=self.CHECKOUT_FIELDS)
        for checkout in self.checkouts:
            checkout_result = checkout.run_checkout(
                self.CHECKOUTS_FOLDER, df_source_data
            )
            df_result = self.__add_checkout_result_to_dataframe(
                df_result, checkout_result
            )
            print()

        self.load_to_storage(df_result)
