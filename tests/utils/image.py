import logging

import cv2
import numpy as np
from PIL import Image


try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
    IMPORT_ERROR = False
except ModuleNotFoundError:
    IMPORT_ERROR = True

logger = logging.getLogger(__name__)


def read_image(src_file: str) -> np.ndarray:
    """
    Read an image from the specified file.

    This function supports HEIC format and other standard image formats
    such as JPEG and PNG. If reading a HEIC file fails, OpenCV will be used
    to read the image.

    Parameters
    ----------
    src_file : str
        Path to the image file.

    Returns
    -------
    np.ndarray
        Image as a NumPy array.

    Notes
    -----
    If the pillow_heif module is not available, the function will fallback
    to using OpenCV for all image formats.

    If the input file is a HEIC file and reading it fails, a warning will be logged,
    and the function will attempt to read the image using OpenCV instead.
    """
    if IMPORT_ERROR:
        logger.warning("Failed to import pillow_heif. Using cv2 to read the image.")
        return cv2.imread(src_file)

    if src_file.lower().endswith(".heic"):
        # logger.info(f"Attempting to read HEIC file: {src_file}")
        try:
            # Use pillow_heif to read the HEIC file
            image = Image.open(src_file)
            image = np.array(image)
            # logger.info("Successfully read HEIC file.")
        except Exception as e:
            logger.error(f"Error reading HEIC file {src_file}: {e}")
            image = cv2.imread(src_file)
    else:
        # logger.info(f"Reading non-HEIC file: {src_file}")
        image = cv2.imread(src_file)

    return image
