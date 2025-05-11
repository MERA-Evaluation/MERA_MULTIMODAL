import os
import sys
from typing import Any, Optional
import logging
from pathlib import Path

import cv2
from PIL import UnidentifiedImageError, Image
import imagehash as imhash

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.extend(
    [
        os.path.join(base_dir, "utils"),
        os.path.join(base_dir, "base"),
        os.path.join(os.path.dirname(base_dir), "logging_configuration"),
    ]
)

from runner_filter import RunnerFilter
from base_filter import Filter
from image import read_image
from configure_logging import configure_logger


configure_logger()
logger = logging.getLogger(__name__)


class MetaExtractorFilter(Filter):
    @staticmethod
    def __get_image_dimension(
        filename: str,
    ) -> tuple[str, int, int, Optional[float], int, Optional[str], Optional[str]]:
        """
        Calculate the width, height, and aspect ratio of a single image.

        Parameters
        ----------
        filename : str
            The name of the image file.

        Returns
        -------
        tuple
            A tuple containing:
            - filename (str): The name of the image file.
            - image width (int): The width of the image in pixels.
            - image height (int): The height of the image in pixels.
            - aspect ratio of the image (float or None if height is 0).
            - file_size (int): size of the file in bytes
            - file_extension (str): name of the file format starting with '.' symbol.
            - hash (int): hash of the image file.
        """
        try:
            cv2_image = read_image(filename)
            cv2_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
            im_pil = Image.fromarray(cv2_image)
            hash = str(imhash.phash(im_pil))

            height, width = cv2_image.shape[:2]

            if height == 0 or width == 0:
                aspect_ratio = None
            else:
                aspect_ratio = round(max(width, height) / min(width, height), 3)
            file_size = os.path.getsize(filename)
            file_extension = Path(filename).suffix

            return (
                filename,
                width,
                height,
                aspect_ratio,
                file_size,
                file_extension,
                hash,
            )

        except UnidentifiedImageError:
            logger.error(
                f"Cannot identify image file: {filename}. It may be corrupted or not an image."
            )
            return filename, 0, 0, None, 0, None, None
        except OSError as e:
            logger.error(f"OS error while processing {filename}: {e}")
            return filename, 0, 0, None, 0, None, None
        except Exception as e:
            logger.error(f"Unexpected error while processing {filename}: {e}")
            return filename, 0, 0, None, 0, None, None

    def apply_for_file(self, context_data: dict[str:Any]) -> dict[str, Any]:
        """
        Apply Meta Exctractor filter to one file
        Parameters
        ----------
        sample_path
        Path to file on the local file system.
        context_data
        Context file example: label, target ...
        Returns
        -------
        """
        sample_path = context_data["path"]

        predict = self.__get_image_dimension(sample_path)
        return {
            "path": sample_path,
            "width": predict[1],
            "height": predict[2],
            "aspect_ratio": predict[3],
            "file_size": predict[4],
            "file_extension": predict[5],
            "hash": predict[6],
        }


if __name__ == "__main__":
    runner = RunnerFilter(MetaExtractorFilter)
    runner.run()
