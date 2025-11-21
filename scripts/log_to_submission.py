import argparse
import glob
import hashlib
import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

import datasets
import numpy as np
from lm_eval.loggers.evaluation_tracker import GeneralConfigTracker
from lm_eval.utils import load_yaml_config, sanitize_model_name
from tqdm.auto import tqdm

BENCHMARK_STORAGE = "MERA-evaluation"
_TASKS = {}
DATASETS_TO_TRUNCATION = []
INPUT_DATE_FORMAT = "%Y-%m-%dT%H-%M-%S.%f"
SAMPLES_SUFFIX = "samples_"
RESULTS_SUFFIX = "results_"
INDEX_TO_GET = 0
DOMAIN_DATASETS = {
    "unisciencevqa": [
        "unisciencevqa_applied_sciences",
        "unisciencevqa_business",
        "unisciencevqa_cultural_studies",
        "unisciencevqa_fundamental_sciences",
        "unisciencevqa_social_sciences",
        "unisciencevqa_health_and_medicine",
    ],
    "schoolsciencevqa": [
        "schoolsciencevqa_biology",
        "schoolsciencevqa_chemistry",
        "schoolsciencevqa_physics",
        "schoolsciencevqa_earth_science",
        "schoolsciencevqa_history_all",
        "schoolsciencevqa_history_ru",
        "schoolsciencevqa_economics",
    ],
    "runaturalsciencevqa": [
        "runaturalsciencevqa_biology",
        "runaturalsciencevqa_chemistry",
        "runaturalsciencevqa_physics",
        "runaturalsciencevqa_earth_science",
    ],
    "ruhhh_image": ["ruhhh_image"],
    "weird": ["weird"],
    "ruclevr": ["ruclevr"],
    "rucommonvqa": ["rucommonvqa"],
    "realvqa": ["realvqa"],
    "rumathvqa": ["rumathvqa"],
    "labtabvqa": ["labtabvqa"],
    "aquaria": ["aquaria"],
    "ruenvaqa": ["ruenvaqa"],
    "realvideoqa": ["realvideoqa"],
    "ruhhh_video": ["ruhhh_video"],
    "commonvideoqa": ["commonvideoqa"],
    "rutie_vision": ["rutie_vision"],
    "rutie_audio": ["rutie_audio"],
    "ruslun": ["ruslun"],
}


def get_files_from_dir(dir_path):
    f = []
    for _, _, filenames in os.walk(dir_path):
        for fn in filenames:
            fn = os.path.join(dir_path, fn)
            f.extend([fn])
    return f


def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(obj, file, ensure_ascii=False, indent=4)


def load_json(path):
    with open(path, encoding="utf-8") as file:
        text = json.loads(file.read().strip())
    return text


def load_jsonl(path):
    with open(path, encoding="utf-8") as file:
        result = [json.loads(line) for line in file.readlines()]
    return result


def save_jsonl(file, path):
    with open(path, "w", encoding="utf-8") as outfile:
        for entry in file:
            json.dump(entry, outfile, ensure_ascii=False)
            outfile.write("\n")


def extract_date(file_name: str) -> datetime:
    extract_str_date = file_name.split(".json")[0].split("_")[-1]
    date = datetime.strptime(extract_str_date, INPUT_DATE_FORMAT)
    return date


def register_task(cls):
    _TASKS[cls.__name__] = cls
    return cls


class BaseTask:
    @property
    def src_name(self):
        return self.__class__.__name__.lower()

    @property
    def dst_name(self):
        return self.__class__.__name__

    @property
    def key(self):
        if self._key is None:
            self._key = "filtered_resps"
        return self._key
    
    def find_samples_files(self, dataset_name):
        return glob.glob(
            os.path.join(self.outputs_dir, f"samples_{dataset_name}_*.json*")
        )
    
    def filter_samples_files(self, files):
        return sorted(files, key=extract_date, reverse=True)


    def outputs_path(self):
        res = []
        errors = []
        for domain in DOMAIN_DATASETS[self.src_name]:
            filelist = self.find_samples_files(domain)
            if not filelist:
                errors.extend([domain])
                continue
            # sorting filelist to get the latest
            filelist = self.filter_samples_files(filelist)
            res.extend([filelist[INDEX_TO_GET]])
        return res, errors

    @property
    def submission_path(self):
        return os.path.join(self.dst_dir, f"{self.dst_name}.json")

    @staticmethod
    def doc_to_meta(doc):
        return doc["meta"]

    def doc_to_id(self, doc):
        return self.doc_to_meta(doc)["id"]

    def load(self):
        path = self.dataset_path or os.path.join(BENCHMARK_STORAGE, self.dst_name)
        dataset = datasets.load_dataset(path=path)["test"]
        examples = {}
        for example in dataset:
            doct_id = self.doc_to_id(example)
            examples[doct_id] = example
        return examples

    def __init__(self, outputs_dir, dst_dir, dataset_path: Optional[str] = None):
        self.outputs_dir = outputs_dir
        self.dst_dir = dst_dir
        self.dataset_path = dataset_path
        self._key = None


class TextTask(BaseTask):
    def convert(self):
        paths, errors = self.outputs_path()
        if len(errors):
            for error in errors:
                print(
                    "No samples to pack found, or there is an error in path processed. Src:",
                    error,
                )
        submission = []
        for path in paths:
            domain_submission = load_jsonl(path)
            submission += domain_submission
        if len(submission):
            submission = self.outputs_to_submission(submission)
            save_json(submission, self.submission_path)
        return submission

    def outputs_to_submission(self, outputs):
        res = []
        for doc in outputs:
            doc_id = int(self.doc_to_id(doc["doc"]))
            resp = doc[self.key]
            res.extend([self.doc_outputs_to_submission(doc_id, resp)])
        return {"data": {"test": res}}

    @staticmethod
    def parse_doc(doc):
        return doc[0]

    def doc_outputs_to_submission(self, doc_id, outputs):
        out = outputs[0]
        if isinstance(out, list):
            out = out[0]
        res = {
            "outputs": out,
            "meta": {"id": doc_id},
        }
        return res


class MultiOutputTask(TextTask):
    def doc_outputs_to_submission(self, doc_id, outputs):
        res = {
            "outputs": outputs,
            "meta": {
                "id": doc_id,
            },
        }
        return res


@register_task
class AQUARIA(TextTask):
    pass


@register_task
class CommonVideoQA(TextTask):
    pass


@register_task
class LabTabVQA(TextTask):
    pass


@register_task
class RealVideoQA(TextTask):
    pass


@register_task
class RealVQA(TextTask):
    pass


@register_task
class ruCLEVR(TextTask):
    pass


@register_task
class ruCommonVQA(TextTask):
    pass


@register_task
class ruEnvAQA(TextTask):
    pass


@register_task
class ruHHH_Image(TextTask):
    pass


@register_task
class ruHHH_Video(TextTask):
    pass


@register_task
class ruMathVQA(TextTask):
    pass


@register_task
class ruNaturalScienceVQA(TextTask):
    pass


@register_task
class ruSLUn(TextTask):
    pass


@register_task
class ruTiE_Audio(TextTask):
    
    def doc_to_id(self, doc):
        if "id" in doc["meta"]:
            return doc["meta"]["id"]
        return doc["meta"]["question_id"] + 500 * doc["meta"]["dialog_id"] + 11


@register_task
class ruTiE_Vision(TextTask):
    
    def doc_to_id(self, doc):
        if "id" in doc["meta"]:
            return doc["meta"]["id"]
        return doc["meta"]["question_id"] + 500 * doc["meta"]["dialog_id"] + 11


@register_task
class SchoolScienceVQA(TextTask):
    pass


@register_task
class UniScienceVQA(TextTask):
    pass


@register_task
class WEIRD(TextTask):
    pass


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs_dir", type=str, help="lm-evaluation-harness outputs")
    parser.add_argument(
        "--dst_dir",
        type=str,
        default="submission/",
        help="dir to save files for submission",
    )
    parser.add_argument(
        "--model_args",
        type=str,
        default="",
        help="Comma separated string arguments for model, e.g. `pretrained=EleutherAI/pythia-160m,dtype=float32`",
    )
    res = parser.parse_known_args()[0]
    return res


def pack_submission_logs(outputs_dir: str, dst_dir: str):
    if os.path.isdir(outputs_dir):
        zip_dir = os.path.join(dst_dir, "logs_public")
        os.makedirs(zip_dir, exist_ok=True)
        files_to_pack = glob.glob(os.path.join(outputs_dir, "*.json*"))
        for file_path in files_to_pack:
            file_name = os.path.split(file_path)[-1].lower()
            if file_name.startswith((SAMPLES_SUFFIX, RESULTS_SUFFIX)):
                # copy with possible truncation of outputs
                copy_and_truncate(file_path, zip_dir)
            else:
                print("Unknown file {fn}".format(fn=file_path))
        zip_path = shutil.make_archive(zip_dir, "zip", zip_dir)
        shutil.rmtree(zip_dir)
        print("Logs to add with public submission stored at", zip_path)
    else:
        raise ValueError(f"{outputs_dir} is not directory")


def create_submission(outputs_dir, dst_dir):
    os.makedirs(dst_dir, exist_ok=True)
    for task_name, task_cls in tqdm(_TASKS.items(), total=len(_TASKS)):
        print("Process task", task_name)
        task = task_cls(outputs_dir=outputs_dir, dst_dir=dst_dir)
        _ = task.convert()
        print("---------------------")
    print("Packing logs for public submission...")
    pack_submission_logs(outputs_dir, dst_dir)
    zip_path = shutil.make_archive(dst_dir, "zip", dst_dir)
    print("Submission stored at", zip_path)
    return zip_path


def preprocess_outputs_dir(outputs_dir: str, model_args: str) -> str:
    """
    User either provides "full" path to dir with jsons or provides path to
    folder of upper level and model_args to define subdir with jsons.
    If user explicitly provides model_args, parse it and use to define subdir.
    Otherwise, return the initial outputs_dir with no changes.
    """
    if model_args:
        # get model_name cleared of "pretrained=" and everything after first comma
        model_name = GeneralConfigTracker._get_model_name(model_args)
        # use func to find the name of subdir from model_name
        subdirectory = sanitize_model_name(model_name)
        # join paths
        full_path = os.path.join(outputs_dir, subdirectory)
        return full_path
    return outputs_dir


def truncate_outputs(path):
    """
    Function that takes `path` to file, reads it and substitute all 'arg_0' values
    of each item 'arguments' keys with their sha256 codes.
    """
    if path.endswith("json"):
        data = load_json(path)
    elif path.endswith("jsonl"):
        data = load_jsonl(path)
    else:
        raise ValueError("Undefined format of {directory} file".format(directory=path))
    for line in data:
        for key in line["arguments"]:
            if isinstance(line["arguments"][key]["arg_0"], str):
                line["arguments"][key]["arg_0"] = hashlib.sha256(
                    line["arguments"][key]["arg_0"].encode()
                ).hexdigest()
            else:
                line["arguments"][key]["arg_0"] = hashlib.sha256(
                    line["arguments"][key]["arg_0"][0].encode()
                ).hexdigest()
    return data


def copy_and_truncate(file_path, zip_dir):
    """
    For datasets in DATASETS_TO_TRUNCATION truncates the outputs in logs while copying
    the file into zip_dir. For other files just make copy.
    """
    for file in DATASETS_TO_TRUNCATION:
        if file in os.path.split(file_path)[-1]:
            data = truncate_outputs(file_path)
            name = os.path.split(file_path)[-1]
            save_jsonl(data, os.path.join(zip_dir, name))
            return
    shutil.copy2(file_path, zip_dir)
    return


def main():
    args = get_args()
    outputs_dir = preprocess_outputs_dir(args.outputs_dir, args.model_args)
    create_submission(outputs_dir, args.dst_dir)


if __name__ == "__main__":
    main()
