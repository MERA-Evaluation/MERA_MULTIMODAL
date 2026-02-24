import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
from load_media import get_video
from custom_metrics import process_results_template


def process_results(doc, results):
    return process_results_template(doc, results, func=doc_to_text)


def doc_to_text(doc):
    return doc["instruction"].format(**doc["inputs"])


def doc_to_video(doc):
    videos = [doc["inputs"]["video"]]
    return [get_video(video) for video in videos if video is not None]
