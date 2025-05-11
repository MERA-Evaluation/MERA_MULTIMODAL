import logging
import onnxruntime as ort
from torchvision import transforms
import PIL.Image as Image
import sys
import os
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


class WatermarkFilter(Filter):
    """Implementation of Watermark detector"""

    ML_MODELS_CONFIG = {
        "watermark": {
            "dirname": "models/image/watermark",
            "filenames": ["watermark_det_test.onnx"],
            "urls": [
                "https://rndml-stage.obs.ru-moscow-1.hc.sbercloud.ru/models/image/watermark/watermark_det_test.onnx",
            ],
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.transforms = transforms.Compose(
            [
                transforms.Resize((320, 320)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )

        path = os.path.join(
            self.current_path,
            self.ML_MODELS_CONFIG["watermark"]["dirname"],
            self.ML_MODELS_CONFIG["watermark"]["filenames"][0],
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
                if isinstance(sample_path, str):
                    paths = [sample_path]
                else:
                    paths = sample_path

                imgs = list(map(lambda x: Image.open(x).convert(mode="RGB"), paths))

                tensors = list(map(self.transforms, imgs))

                output = []
                for i in range(len(tensors)):
                    output.append(
                        self.ort_session.run(None, {"input": [tensors[i]]})[0]
                    )

                result_t = list(map(lambda x: "no" if x[0][1] < 0 else "yes", output))
                result = {"path": sample_path, "watermark_detected": result_t[0]}
                return result
            except Exception:
                return {"path": sample_path, "watermark_detected": ""}


if __name__ == "__main__":
    runner: RunnerFilter = RunnerFilter(WatermarkFilter)
    runner.run()
