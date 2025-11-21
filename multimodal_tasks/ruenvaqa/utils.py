from typing import Any, Dict, List
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from load_media import get_audio


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
    :param doc: Dict[str, Any]
        one dataset sample as dictionary
    :return
        one string - the prompt to be passed into LM
    """

    prompt = _doc_to_text(doc)
    return prompt


def doc_to_audio(doc: Dict[str, Any]) -> List[str]:
    """
    Process audios.
    :param doc: Dict[str, Any]
        one dataset sample as dictionary
    :return
        list of audios
    """

    audios = [doc["inputs"]["audio"]]
    return [get_audio(audio) for audio in audios if audio is not None]
