from typing import Any, Dict, List
import numpy as np

from collections import Counter
from typing import List, Tuple, Dict, Any

import re
import json
import ast
from typing import Tuple, Any

from lm_eval.api.filter import Filter
from lm_eval.api.registry import register_filter

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


def clean_json_text(s: str) -> str:
    """
    Removes surrounding wrappers:
      - triple backticks (```...```) or 'json\n...\n'
      - single backticks (`...`)
      - the "json" prefix (case-insensitive) followed by ':' or a newline
      - outer single/double quotes (and unpacking escaped \n via ast.literal_eval)
    Returns the cleaned string (JSON text).
    """
    if s is None:
        return ""
    s = s.strip()

    # 1) remove triple backticks ```...``` \\
    m = re.match(r"^```(?:\w+)?\s*(.*)\s*```$", s, flags=re.DOTALL)
    if m:
        s = m.group(1).strip()

    # 2) remove single backticks `...`
    if s.startswith("`") and s.endswith("`"):
        s = s[1:-1].strip()

    # 3) remove prefix "json" или "JSON" перед телом (включая "json:" или "json\n")
    s = re.sub(r"(?i)^\s*json\s*[:\n\r]\s*", "", s, count=1)

    # 4) if the string is wrapped in single or double quotes and contains escaped sequences like \n, etc. —
    # try to safely unpack the literal (ast.literal_eval) to obtain actual newlines
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        try:
            s = ast.literal_eval(s)
            # literal_eval returns str, maybe with real \n
            if not isinstance(s, str):
                s = str(s)
        except Exception:
            # if ast.literal_eval fails — simply strip the outer quotes
            s = s[1:-1]

    return s.strip()


def doc_to_audio(doc: Dict[str, Any]):
    """
    Process audios.
    :param doc: Dict[str, Any]
        one dataset sample as dictionary
    :return
        list of audios
    """

    audios = [doc["inputs"]["audio"]]
    return [get_audio(audio) for audio in audios if audio is not None]


@register_filter("ruslunscoring")
class ruSLUnScoring(Filter):
    def __init__(self) -> None:
        """
        Считывание необходимых для фильтра параметров
        """

    def apply(self, resps, docs):
        """
        Метод, который отвечает за применение фильтра
        """
        # resps: List[List[str]] - список списков генераций
        json_results = []
        for idx, sample in enumerate(resps):
            json_result = []
            for completion in sample:
                processed_completion = clean_json_text(completion)
                json_result.append(processed_completion)
            json_results.append([processed_completion])
        return json_results


def try_parse_json(s: str):
    try:
        return True, json.loads(s)
    except json.JSONDecodeError:
        return False, None


def process_results(doc: Dict, results: List[str]) -> Dict[str, float]:

    is_valid_json, pred_json = try_parse_json(results[0][0])

    if is_valid_json and pred_json is not None:
        ref_json = json.loads(doc["outputs"].replace("\'", "\""))

        # Intent
        intent_correct = int(pred_json.get('intent') == ref_json.get('intent'))

        # Собираем list[(key, value)] из slots (предполагается, что каждый слот — dict с одним ключом)
        def slot_kv_list(json_obj: Dict[str, Any]) -> List[Tuple[str, str]]:
            slots = json_obj.get('slots', []) or []
            kvs: List[Tuple[str, str]] = []
            for slot in slots:
                # Если в словаре несколько пар — добавим все, обычно там одна пара
                for k, v in slot.items():
                    kvs.append((str(k), str(v)))
            return kvs

        pred_kv = slot_kv_list(pred_json)
        ref_kv = slot_kv_list(ref_json)

        pred_counter = Counter(pred_kv)
        ref_counter = Counter(ref_kv)

        # Количество корректных совпадений по ключ+значение (с учётом повторов)
        correct_slot_matches = sum((pred_counter & ref_counter).values())

        # Precision/recall/F1 для слотов (key+value)
        n_pred = len(pred_kv)
        n_ref = len(ref_kv)

        if n_pred == 0 and n_ref == 0:
            slot_precision = slot_recall = slot_f1 = 1.0
        else:
            slot_precision = correct_slot_matches / n_pred if n_pred > 0 else 0.0
            slot_recall = correct_slot_matches / n_ref if n_ref > 0 else 0.0
            if slot_precision + slot_recall > 0:
                slot_f1 = 2 * slot_precision * slot_recall / (slot_precision + slot_recall)
            else:
                slot_f1 = 0.0
    else:
        intent_correct = 0
        slot_f1 = 0

    return {
        'intent_EM': intent_correct,
        'slot_f1': slot_f1,
    }
