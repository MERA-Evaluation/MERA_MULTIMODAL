import os
import sys
from typing import Any, Optional
import logging

import cv2
from PIL import UnidentifiedImageError

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.extend(
    [
        os.path.join(base_dir, "base"),
        os.path.join(os.path.dirname(base_dir), "logging_configuration"),
    ]
)

from runner_filter import RunnerFilter
from base_filter import Filter
from configure_logging import configure_logger


configure_logger()
logger = logging.getLogger(__name__)


class BlurFilter(Filter):
    """Blur filter implementation."""

    @staticmethod
    def __variance_of_laplacian(image):
        """Apply Laplacian operator to image."""
        return cv2.Laplacian(image, cv2.CV_64F).var()

    def __check_blur_effect(self, sample_path: str) -> Optional[float]:
        """
        Check blur effect on image file.
        Parameters
        ----------
        filename - path to file on the local file system.

        Returns
        -------
        Bool (True or False) value of blur effect existence on the image.
        """
        try:
            image = cv2.imread(sample_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            fm = self.__variance_of_laplacian(gray)
            return fm
        except UnidentifiedImageError:
            logger.error(
                f"Cannot identify image file: {sample_path}. It may be corrupted or not an image."
            )
        except OSError:
            logger.error(f"OS error while processing {sample_path}")
        except Exception:
            logger.error(f"Unexpected error while processing {sample_path}")

    def apply_for_file(self, context_data: dict[str:Any]) -> dict[str, Any]:
        """
        Apply Blur filter to one file.
        Parameters
        ----------
        context_data: dict {
                            'path': 'path to file on the local file system.'
                            'text': 'text describing the sample' (Optional field using only with csv_pagination and s3_csv_with_redis
                             pagination types)
                           } with samples metadata
        Returns
        -------
        Dict {
                'path': (required field)
                'any_filter_out_1': 'any_filter_output_value_1',
                'any_filter_out_2': 'any_filter_output_value_2'
             } with prediction results
        """
        sample_path = context_data["path"]
        predict = self.__check_blur_effect(sample_path)
        return {"path": sample_path, "blur_score": predict}


if __name__ == "__main__":
    runner = RunnerFilter(BlurFilter)
    runner.run()
