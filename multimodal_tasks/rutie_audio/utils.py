import datasets
import numpy as np

from lm_eval.filters.extraction import RegexFilter
from lm_eval.models.api_models import JsonChatStr

from typing import Dict, Any

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from load_media import get_audio

FALLBACK = "-1"
RUTIE_END_QUESTION_ID = 499
TEMPLATE = "RUTIE_TARGET_{idx}"
REGEXP = RegexFilter(regex_pattern=r"\b([A-D])\b", group_select=0, fallback=FALLBACK)


_process_docs_cache: Dict[str, datasets.Dataset] = {}


def process_docs(dataset: datasets.Dataset) -> datasets.Dataset:
    fingerprint = dataset._fingerprint
    if fingerprint in _process_docs_cache:
        return _process_docs_cache[fingerprint]

    min_id = min(item["id"] for item in dataset["meta"])

    def transform_sample(sample: dict) -> dict:
        sample["meta"]["question_id"] = (sample["meta"]["id"] - min_id) % (RUTIE_END_QUESTION_ID + 1)
        sample["meta"]["dialog_id"] = (sample["meta"]["id"] - min_id) // (RUTIE_END_QUESTION_ID + 1)
        del sample["meta"]["id"]
        sample["sorting_arg"] = sample["meta"]["question_id"] + sample["meta"]["dialog_id"] * 10 ** 6
        return sample

    ds2 = dataset.map(
        transform_sample,
        batched=False
    )

    ds2 = ds2.sort("sorting_arg").remove_columns(["sorting_arg"])
    _process_docs_cache[fingerprint] = ds2

    return ds2


def replace_targets(string, max_num, storage):
    # for consistency only
    if max_num == 0:
        return string
    # string contains parts like RUTIE_TARGET_0, RUTIE_TARGET_1, so on
    for idx in range(max_num - 1, -1, -1):
        to_fill = TEMPLATE.format(idx=idx)
        # replace each part with corresponding answer from storage
        string = string.replace(to_fill, storage["answers"][to_fill])
    return string


def _update_request(storage, request):
    # sanity check, if req_id > 0 and storage is empty => something went wrong
    if len(storage) == 0 and request.doc["meta"]["question_id"] != 0:
        print("No previous responses logged in storage!")
        return request

    max_num = request.doc["meta"]["question_id"]

    # when string passed (everywhere except for API calls)
    if isinstance(request.arguments[0], str):
        new_req = replace_targets(request.arguments[0], max_num, storage)
        request.arguments = (new_req, *request.arguments[1:])
    elif isinstance(request.arguments[0], list):
        for el in request.arguments[0]:
            for content in el["content"]:
                if content["type"] == "text":
                    content["text"] = replace_targets(content["text"], max_num, storage)
    else:
        new_req = replace_targets(request.arguments[0].prompt, max_num, storage)
        new_req = JsonChatStr(new_req)
        request.arguments = (new_req, *request.arguments[1:])

    return request


def _update_storage(storage, request):
    req_id = request.doc["meta"]["question_id"]

    # check that the set is over to clear storage
    if not isinstance(request.arguments[1], dict):
        dialog_ends = (
            request.doc["meta"]["question_id"] == RUTIE_END_QUESTION_ID
            and len(storage["candidates"]) == 1
        )
    else:
        dialog_ends = request.doc["meta"]["question_id"] == RUTIE_END_QUESTION_ID

    # clear storage after rutie ends
    if dialog_ends:
        return {}

    # loglikelihood setup
    if not isinstance(request.arguments[1], dict):
        # update storage only after running 2 requests for the same sample
        storage.setdefault("candidates", []).extend([request.resps[0][0]])
        # need 2 probas to decide on the answer
        if len(storage["candidates"]) == 2:
            # decide on the answer
            result = ["1", "2"][np.argmax(storage["candidates"])]
            # get string that includes the context
            storage.setdefault("answers", {})[TEMPLATE.format(idx=req_id)] = result
            # discard candidates
            storage["candidates"] = []

    # generative setup
    else:
        # pick LM answer and truncate spaces
        storage["candidates"] = request.resps[0].strip()

        # apply filter to response to get digit out of LM answer
        string_answer = extract_string([storage["candidates"]])
        filtered_answer = REGEXP.apply([[string_answer]], None)

        # might not find pattern - replace with FALLBACK
        result = (
            FALLBACK
            if (not len(filtered_answer) or not filtered_answer[0])
            else filtered_answer[0][0]
        )

        # store LM filtered answer
        storage.setdefault("answers", {})[TEMPLATE.format(idx=req_id)] = result

    return storage


def extract_string(nested_list):
    for item in nested_list:
        if isinstance(item, list):
            # If the item is a list, call the function recursively
            result = extract_string(item)
            if result is not None:
                return result
        elif isinstance(item, str):
            # If the item is a string, return it
            return item
    return None

def _doc_to_text(doc: Dict[str, Any]) -> str:
    """
    Helper function that processes the entire doc to form the input prompt only.

    :param doc: Dict[str, Any]
        one dataset sample as dictionary

    :return
        one string - the prompt to be passed into LM
    """

    # take the instruction and fill it with all doc["inputs"] data
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

def doc_to_audio(doc: Dict[str, Any]):
    audios = [doc["inputs"]["audio"]]
    return [get_audio(audio) for audio in audios if audio is not None]
