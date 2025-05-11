import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from base.base_checkout import BaseCheckout


class BaseMeraCheckout(BaseCheckout): ...


class ACLSecurityCheckout(BaseMeraCheckout):
    CHECKOUT_NAME = "acl_security"
    CHECKOUT_CRITERION_NAME = "Доступ к материалам закрыт"

    def get_failed_samples_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df["ACLSecurityFilter_acl_security"] == False][
            ["path", "ACLSecurityFilter_acl_security"]
        ]


class CorruptedImageCheckout(BaseMeraCheckout):
    CHECKOUT_NAME = "corrupted_image"
    CHECKOUT_CRITERION_NAME = "Отсутствие битых файлов"

    def get_failed_samples_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df_failed = df[
            (df["MetaExtractorFilter_width"] == 0)
            & (df["MetaExtractorFilter_height"] == 0)
            & (df["MetaExtractorFilter_aspect_ratio"] is None)
            & (df["MetaExtractorFilter_file_size"] == 0)
            & (df["MetaExtractorFilter_file_extension"] is None)
            & (df["MetaExtractorFilter_hash"] is None)
        ]
        return df_failed[
            [
                "path",
                "MetaExtractorFilter_width",
                "MetaExtractorFilter_height",
                "MetaExtractorFilter_aspect_ratio",
                "MetaExtractorFilter_file_size",
                "MetaExtractorFilter_file_extension",
                "MetaExtractorFilter_hash",
            ]
        ]


class ImageResolutionCheckout(BaseMeraCheckout):
    CHECKOUT_NAME = "image_resolution"
    CHECKOUT_CRITERION_NAME = "Корректное разрешение файлов"
    MIN_SIDE_VALUE = 224
    MAX_SIDE_VALUE = 3840

    def get_failed_samples_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[
            (
                df["MetaExtractorFilter_width"].apply(
                    lambda row: not (self.MIN_SIDE_VALUE <= row <= self.MAX_SIDE_VALUE)
                )
            )
            & (
                df["MetaExtractorFilter_height"].apply(
                    lambda row: not (self.MIN_SIDE_VALUE <= row <= self.MAX_SIDE_VALUE)
                )
            )
        ][["path", "MetaExtractorFilter_width", "MetaExtractorFilter_height"]]


class ImageFormatCheckout(BaseMeraCheckout):
    CHECKOUT_NAME = "image_format"
    CHECKOUT_CRITERION_NAME = "Отсутствие битых файлов"
    FORMATS = (".png", ".jpeg", ".jpg")

    def get_failed_samples_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[
            df["MetaExtractorFilter_file_extension"].apply(
                lambda row: row not in self.FORMATS
            )
        ][["path", "MetaExtractorFilter_file_extension"]]


class PHashCheckout(BaseMeraCheckout):
    CHECKOUT_NAME = "phash"
    CHECKOUT_CRITERION_NAME = "Уникальность phash"

    def get_failed_samples_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df["MetaExtractorFilter_hash"].duplicated(keep=False)][
            ["path", "MetaExtractorFilter_hash"]
        ]


class NSFWCheckout(BaseMeraCheckout):
    CHECKOUT_NAME = "nsfw"
    CHECKOUT_CRITERION_NAME = "Проверка NSFW фильтра"
    NSFW_AVAILABLE_FORMATS = ("drawings", "neutral")

    def get_failed_samples_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[
            df["NSFWFilter_nsfw_type"].apply(
                lambda row: row not in self.NSFW_AVAILABLE_FORMATS
            )
        ][["path", "NSFWFilter_nsfw_type"]]


class WatermarkCheckout(BaseMeraCheckout):
    CHECKOUT_NAME = "watermark"
    CHECKOUT_CRITERION_NAME = "Проверка Watermark фильтра"

    def get_failed_samples_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[
            df["WatermarkFilter_watermark_detected"].apply(lambda row: row == "yes")
        ][["path", "WatermarkFilter_watermark_detected"]]


class BlurCheckout(BaseMeraCheckout):
    CHECKOUT_NAME = "blur"

    CHECKOUT_CRITERION_NAME = "Проверка Blur фильтра"

    def get_failed_samples_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[df["BlurFilter_blur_score"] < 100][["path", "BlurFilter_blur_score"]]
