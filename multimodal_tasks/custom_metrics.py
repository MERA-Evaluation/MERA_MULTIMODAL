from transformers.data.metrics.squad_metrics import compute_exact
from transformers import AutoTokenizer
import requests
import numpy as np
import os


MAX_LENGTH = 8000
OFFSET = 5


def load_tokenizer():
    # check model name or get default from MERA repo
    vllm_model = os.environ.get("MERA_JUDGE_MODEL", "MERA-evaluation/MERA_Answer_judge")
    tokenizer = AutoTokenizer.from_pretrained(vllm_model)
    return tokenizer


tokenizer = load_tokenizer()


def truncate_prompt(tokens, tokenizer, _max_length=8000, _offset=5, side="left"):
        if side == "right":
            prompt_truncated = tokenizer.decode(tokens[:(_max_length - _offset)])
        elif side == "left":
            prompt_truncated = tokenizer.decode(tokens[-(_max_length - _offset):])
        else:
            err = f"Unknown side: {side}"
            print(f"Truncation error {err}")
            prompt_truncated = tokenizer.decode(tokens[:(_max_length - _offset)])
        return prompt_truncated


def preprocess_request(question, true, prediction, tokenizer) -> list[str]:
    result = []
    prompt_full = question + tokenizer.sep_token + str(true) + tokenizer.sep_token + str(prediction)
    tokens_full = tokenizer.encode(prompt_full)
    if len(tokens_full) > MAX_LENGTH - OFFSET:
        left_prompt = truncate_prompt(tokens_full, tokenizer, _max_length=MAX_LENGTH, _offset=OFFSET, side="right")
        right_prompt = truncate_prompt(tokens_full, tokenizer, _max_length=MAX_LENGTH, _offset=OFFSET, side="left")
        result.extend([left_prompt, right_prompt])
    else:
        result.extend([prompt_full])
    sep_answer = str(prediction).split("ОТВЕТ")[-1].strip()
    if sep_answer:
        prompt_split = question + tokenizer.sep_token + str(true) + tokenizer.sep_token + sep_answer
        tokens_split = tokenizer.encode(prompt_split)
        if len(tokens_split) > MAX_LENGTH - OFFSET:
            left_prompt_split = truncate_prompt(tokens_split, tokenizer, _max_length=MAX_LENGTH, _offset=OFFSET, side="right")
            right_prompt_split = truncate_prompt(tokens_split, tokenizer, _max_length=MAX_LENGTH, _offset=OFFSET, side="left")
            result.extend([left_prompt_split, right_prompt_split])
        else:
            result.extend([prompt_split])
    return result


def judge_score(question, truth, prediction, tokenizer):
    # first check if vllm serve is launched by environ vars
    vllm_url = os.environ.get("MERA_JUDGE_URL", None)
    if not vllm_url:
        return 0
    # check model name or get default from MERA repo
    vllm_model = os.environ.get("MERA_JUDGE_MODEL", "MERA-evaluation/MERA_Answer_judge")
    # prepare requests
    reqs = preprocess_request(question, truth, prediction, tokenizer)
    # make post requests
    reqs_labels = [0]
    for req in reqs:
        try:
            answer = requests.post(vllm_url, {
                "model": vllm_model,
                "input": req,
                "truncate_prompt_tokens": 8192  # hardcoded for MERA_Answer_judge
            })
            answer = np.argmax(answer.json()['data'][0]['probs'])
        except:
            answer = 0
        reqs_labels.extend([answer])
    return max(reqs_labels)


def process_results_template(doc: dict, results: list[str], func) -> dict:
    model_answer = results[0]
    if len(doc["outputs"]) > 0:
        return {
            "exact_match": compute_exact(doc["outputs"], model_answer),
            "judge_score": judge_score(func(doc), doc["outputs"], model_answer)
        }
    return {
        "exact_match": 0,
        "judge_score": 0
    }


def process_results_group(doc: dict, results: list[str], func) -> dict:
    model_answer = results[0]
    if len(doc["outputs"]) > 0:
        return {
            "exact_match": compute_exact(doc["outputs"], model_answer),
            "judge_score": judge_score(func(doc), doc["outputs"], model_answer),
            "group_exact_match": [compute_exact(doc["outputs"], model_answer), doc["meta"]["group_id"]],
            "group_judge_score": [judge_score(func(doc), doc["outputs"], model_answer), doc["meta"]["group_id"]]
        }
    return {
        "exact_match": 0,
        "judge_score": 0,
        "group_exact_match": [0, 0],
        "group_judge_score": [0, 0]
    }


def aggregate_group_score(items):
    unzipped = list(zip(*items))
    scores = unzipped[0]
    groups = unzipped[1]
    dct_agg = {}
    for i in range(len(groups)):
        dct_agg.setdefault(groups[i], []).extend([scores[i]])
    metric_list = []
    for group_id in dct_agg:
        if sum(dct_agg[group_id]) == len(dct_agg[group_id]):
            metric_list.extend([1])
        else:
            metric_list.extend([0])
    return sum(metric_list) / len(metric_list)
