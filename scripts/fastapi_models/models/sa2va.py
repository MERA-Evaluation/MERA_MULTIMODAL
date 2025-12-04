import os
import uuid
import cv2
import numpy as np
import torch

from models.base_model import BaseModel
from utils.base64_to_file import save_base64_to_file


class Sa2VAVideoChatModel(BaseModel):
    def _generate(self, messages):
        tmp_paths = []
        frames_dir = None

        all_texts = []
        videos_b64 = []
        for m in messages:
            parts_text = []
            for p in m["content"]:
                if p["type"] == "text":
                    parts_text.append(p["text"])
                else:
                    videos_b64.append(p["video_url"]["url"])
            all_texts.append((m["role"], "".join(parts_text).strip()))

        if len(all_texts) == 0:
            user_text = ""
            past_text = ""
        else:
            roles, texts = zip(*all_texts)
            user_text = texts[-1]
            past_pairs = [f"{r}: {t}" for r, t in all_texts[:-1] if t]
            past_text = "\n".join(past_pairs)

        text_prompt = f"<image>{user_text}".strip() if user_text else "<image>"

        images_paths = None
        if videos_b64:
            v_b64 = videos_b64[0]
            video_path = save_base64_to_file(v_b64, output_dir="tmp_video", ext=".mp4")
            tmp_paths.append(video_path)

            frames_dir = os.path.join("tmp_video_frames", uuid.uuid4().hex)
            os.makedirs(frames_dir, exist_ok=True)
            images_paths = self._extract_uniform_frames(video_path, frames_dir, max_frames=5)
            tmp_paths.extend(images_paths)

        input_dict = {
            "text": text_prompt,
            "past_text": past_text,
            "mask_prompts": None,
            "tokenizer": self.tokenizer,
        }
        if images_paths:
            input_dict["video"] = images_paths

        with torch.no_grad():
            ret = self.model.predict_forward(**input_dict)

        answer = ret.get("prediction", "")

        for p in tmp_paths:
            try:
                os.remove(p)
            except Exception:
                pass
        if frames_dir:
            try:
                os.rmdir(frames_dir)
            except Exception:
                pass

        return answer

    def _extract_uniform_frames(self, video_path, out_dir, max_frames=5):
        cap = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        if total <= 0:
            ret, frame = cap.read()
            if ret:
                out_p = os.path.join(out_dir, "frame_0000.png")
                cv2.imwrite(out_p, frame)
                cap.release()
                return [out_p]
            cap.release()
            return []

        if total > max_frames:
            step = (total - 1) // (max_frames - 1)
            indices = [0] + list(range(1, total - 1, step))[1:max_frames - 1] + [total - 1]
            indices = indices[:max_frames]
        else:
            indices = list(range(total))

        paths = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret or frame is None:
                continue
            out_p = os.path.join(out_dir, f"frame_{idx:05d}.png")
            cv2.imwrite(out_p, frame)
            paths.append(out_p)

        cap.release()
        return paths

    def init_model(self):
        from transformers import AutoTokenizer, AutoModel

        self.model = AutoModel.from_pretrained(
            self.model_name,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            use_flash_attn=True,
            trust_remote_code=True,
        ).eval()

        if self.device == "cuda":
            self.model = self.model.cuda()

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            use_fast=False,
        )
