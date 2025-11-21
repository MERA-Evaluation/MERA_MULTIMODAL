import io
from typing import Any, Dict

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from load_media import get_image


def _doc_to_text(doc: Dict[str, Any]) -> str:
    """
    Helper function that processes the entire doc to form the input prompt only.

    :param doc: Dict[str, Any]
        one dataset sample as dictionary

    :return
        one string - the prompt to be passed into LM
    """

    prompt = doc["instruction"].format(**doc["inputs"])
    return prompt


def doc_to_text(doc: Dict[str, Any]) -> str:
    """
    Get the prompt for a given document.
    This function is used by code to form prompt for each sample.

    Note! Some models may require you have only <image> tags inside the prompt.
    So, this function also changes "{question} <image_1>\nOptions:\n1. <image_2>..."
    into "{question} <image>\nOptions:\n1. <image>...".
    The order of images to be passed into the model will be decided in doc_to_image,
    so you would not lose the information where should go any image.

    :param doc: Dict[str, Any]
        one dataset sample as dictionary

    :return
        one string - the prompt to be passed into LM
    """

    prompt = _doc_to_text(doc)
    return prompt


def doc_to_image(doc: Dict[str, Any]):
    """
    Process images. The result is a sorted in ascending order list of PIL.Image.Image files.
    Sorting here means that if you have more than one image, here you are to decide on the order.
    Like first take image to fill <image_1> tag, then <image_2> and so on in a list.

    :param doc: Dict[str, Any]
        one dataset sample as dictionary

    :return
        list of images in format PIL.Image.Image
    """

    images = [doc["inputs"]["image"]]
    return [get_image(image) for image in images if image is not None]
