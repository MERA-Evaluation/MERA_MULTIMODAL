import logging
import onnxruntime as ort
import PIL.Image as Image
import sys
import os
import numpy as np
from typing import Any

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
from configure_logging import configure_logger


configure_logger()
logger = logging.getLogger(__name__)
logger.info(logging.INFO)


class NSFWFilter(Filter):
    """Implementation of Watermark detector"""

    ML_MODELS_CONFIG = {
        "nsfw": {
            "dirname": "models/image/nsfw",
            "filenames": ["nsfw_299.onnx"],
            "urls": [
                "https://rndml-stage.obs.ru-moscow-1.hc.sbercloud.ru/models/nsfw_299.onnx",
            ],
        }
    }
    categories = ["drawings", "hentai", "neutral", "porn", "sexy"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.transforms = lambda x: np.asarray(x.resize((299, 299))) / 255

        path = os.path.join(
            self.current_path,
            self.ML_MODELS_CONFIG["nsfw"]["dirname"],
            self.ML_MODELS_CONFIG["nsfw"]["filenames"][0],
        )

        self.ort_session = ort.InferenceSession(
            path,
            providers=[
                "CPUExecutionProvider",
                "CUDAExecutionProvider",
            ],
        )

    def apply_for_file(self, context_data: dict[str:Any]) -> dict[str, Any]:
        sample_path = context_data["path"]
        if os.path.exists(sample_path):
            try:
                paths = [sample_path]

                # preprocess
                imgs = list(map(lambda x: Image.open(x).convert(mode="RGB"), paths))
                tensors = list(map(self.transforms, imgs))

                # run
                res = self.ort_session.run(None, {"input": [tensors[0]]})[0][0]

                # convert result
                result_t = self.categories[res.tolist().index(max(res))]
                result = {"path": sample_path, "nsfw_type": result_t}
                return result
            except Exception:
                return {"path": sample_path, "nsfw_type": ""}


if __name__ == "__main__":
    runner: RunnerFilter = RunnerFilter(NSFWFilter)
    runner.run()
