import logging
import onnxruntime as ort
from torchvision import transforms
import PIL.Image as Image
import sys
import os
import cv2
import torch
import numpy as np
from typing import Any
from math import ceil
from itertools import product


base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.extend(
    [
        os.path.join(base_dir, "base"),
        os.path.join(os.path.dirname(base_dir), "logging_configuration"),
    ]
)

from runner_filter import RunnerFilter
from base_filter import Filter
from configure_logging import configure_logger


configure_logger()
logger = logging.getLogger(__name__)


def decode(loc, priors, variances):
    """Decode locations from predictions using priors to undo
    the encoding we did for offset regression at train time.
    Args:
        loc (tensor): location predictions for loc layers,
            Shape: [num_priors,4]
        priors (tensor): Prior boxes in center-offset form.
            Shape: [num_priors,4].
        variances: (list[float]) Variances of priorboxes
    Return:
        decoded bounding box predictions
    """

    boxes = torch.cat(
        (
            priors[:, :2] + loc[:, :2] * variances[0] * priors[:, 2:],
            priors[:, 2:] * torch.exp(loc[:, 2:] * variances[1]),
        ),
        1,
    )
    boxes[:, :2] -= boxes[:, 2:] / 2
    boxes[:, 2:] += boxes[:, :2]
    return boxes


class PriorBox(object):
    def __init__(self, cfg, image_size=None, phase="train"):
        super(PriorBox, self).__init__()
        self.min_sizes = cfg["min_sizes"]
        self.steps = cfg["steps"]
        self.clip = cfg["clip"]
        self.image_size = image_size
        self.feature_maps = [
            [ceil(self.image_size[0] / step), ceil(self.image_size[1] / step)]
            for step in self.steps
        ]

    def forward(self):
        anchors = []
        for k, f in enumerate(self.feature_maps):
            min_sizes = self.min_sizes[k]
            for i, j in product(range(f[0]), range(f[1])):
                for min_size in min_sizes:
                    s_kx = min_size / self.image_size[1]
                    s_ky = min_size / self.image_size[0]
                    if min_size == 32:
                        dense_cx = [
                            x * self.steps[k] / self.image_size[1]
                            for x in [j + 0, j + 0.25, j + 0.5, j + 0.75]
                        ]
                        dense_cy = [
                            y * self.steps[k] / self.image_size[0]
                            for y in [i + 0, i + 0.25, i + 0.5, i + 0.75]
                        ]
                        for cy, cx in product(dense_cy, dense_cx):
                            anchors += [cx, cy, s_kx, s_ky]
                    elif min_size == 64:
                        dense_cx = [
                            x * self.steps[k] / self.image_size[1]
                            for x in [j + 0, j + 0.5]
                        ]
                        dense_cy = [
                            y * self.steps[k] / self.image_size[0]
                            for y in [i + 0, i + 0.5]
                        ]
                        for cy, cx in product(dense_cy, dense_cx):
                            anchors += [cx, cy, s_kx, s_ky]
                    else:
                        cx = (j + 0.5) * self.steps[k] / self.image_size[1]
                        cy = (i + 0.5) * self.steps[k] / self.image_size[0]
                        anchors += [cx, cy, s_kx, s_ky]
        output = torch.Tensor(anchors).view(-1, 4)
        if self.clip:
            output.clamp_(max=1, min=0)
        return output


class Preproc(object):
    def __init__(self):
        pass

    def __call__(self, raw_img):
        return preproc(raw_img)


def nms(dets, thresh):
    """Pure Python NMS baseline."""
    x1 = dets[:, 0]
    y1 = dets[:, 1]
    x2 = dets[:, 2]
    y2 = dets[:, 3]
    scores = dets[:, 4]

    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter)

        inds = np.where(ovr <= thresh)[0]
        order = order[inds + 1]

    return keep


def preproc(raw_img, resize=1):
    img = np.float32(raw_img)
    if resize != 1:
        img = cv2.resize(
            img, None, None, fx=resize, fy=resize, interpolation=cv2.INTER_LINEAR
        )
    im_height, im_width, _ = img.shape
    scale = torch.Tensor([img.shape[1], img.shape[0], img.shape[1], img.shape[0]])
    img -= (104, 117, 123)
    img = img.transpose(2, 0, 1)
    img = torch.from_numpy(img).unsqueeze(0)
    return img


class FaceDetectionFilter(Filter):
    """Implementation of face detector"""

    ML_MODELS_CONFIG = {
        "face_detection": {
            "dirname": "models/image/face_detection",
            "filenames": ["face_detection.onnx"],
            "urls": [
                "https://rndml-stage.obs.ru-moscow-1.hc.sbercloud.ru/models/image/face_detection/face_detection.onnx",
            ],
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.transforms = transforms.Compose(
            [
                Preproc(),
                transforms.Resize((1024, 1024)),
            ]
        )

        path = os.path.join(
            self.current_path,
            self.ML_MODELS_CONFIG["face_detection"]["dirname"],
            self.ML_MODELS_CONFIG["face_detection"]["filenames"][0],
        )

        self.ort_session = ort.InferenceSession(
            path,
            providers=[
                "CPUExecutionProvider",
                "CUDAExecutionProvider",
            ],
        )

    def _postprocess(self, res: list, img: Image) -> int:
        # configuration
        cfg = {
            "name": "FaceBoxes",
            # 'min_dim': 1024,
            # 'feature_maps': [[32, 32], [16, 16], [8, 8]],
            # 'aspect_ratios': [[1], [1], [1]],
            "min_sizes": [[32, 64, 128], [256], [512]],
            "steps": [32, 64, 128],
            "variance": [0.1, 0.2],
            "clip": False,
            "loc_weight": 2.0,
            "gpu_train": True,
        }
        resize = 1

        confidence_threshold = 0.05
        top_k = 5000
        keep_top_k = 750
        nms_threshold = 0.3
        cpu = True
        vis_thres = 0.5
        im_height, im_width = 1024, 1024
        scale = torch.Tensor([img.size[1], img.size[0], img.size[1], img.size[0]])

        # end of config
        # _____________
        # face boxes extraction

        loc, conf = torch.Tensor(res[0]), torch.Tensor(res[1])

        priorbox = PriorBox(cfg, image_size=(im_height, im_width))
        priors = priorbox.forward()
        # priors = priors.to(device)
        prior_data = priors.data

        boxes = decode(loc.data.squeeze(0), prior_data, cfg["variance"])
        boxes = boxes * scale / resize
        boxes = boxes.cpu().numpy()
        scores = conf.squeeze(0).data.cpu().numpy()[:, 1]

        # ignore low scores
        inds = np.where(scores > confidence_threshold)[0]
        boxes = boxes[inds]
        scores = scores[inds]

        # keep top-K before NMS
        order = scores.argsort()[::-1][:top_k]
        boxes = boxes[order]
        scores = scores[order]

        # do NMS
        dets = np.hstack((boxes, scores[:, np.newaxis])).astype(np.float32, copy=False)
        # keep = py_cpu_nms(dets, args.nms_threshold)
        keep = nms(dets, nms_threshold)  # , force_cpu=cpu)
        dets = dets[keep, :]

        # keep top-K faster NMS
        dets = dets[:keep_top_k, :]

        # for b in dets:
        #     x1, y1, x2, y2, score = b[0], b[1], b[2], b[3], b[4]

        return len(dets)

    def apply_for_file(self, context_data: dict[str:Any]) -> dict[str, Any]:
        sample_path = context_data["path"]
        if os.path.exists(sample_path):
            try:
                raw_img = Image.open(sample_path).convert(mode="RGB")

                tensor = self.transforms(raw_img)
                res = self.ort_session.run(None, {"input": [tensor[0]]})

                n_faces = self._postprocess(res, raw_img)

                result = {"path": sample_path, "faces_count": n_faces}
                return result
            except Exception as err:
                logger.warning(f"{err}")
                return {"path": sample_path, "faces_count": ""}


if __name__ == "__main__":
    runner: RunnerFilter = RunnerFilter(FaceDetectionFilter)
    runner.run()
