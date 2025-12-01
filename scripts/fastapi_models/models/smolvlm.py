import os
import torch

from models.base_model import BaseModel
from utils.base64_to_file import save_base64_to_file


class SmolVLM2VideoChatModel(BaseModel):
    def _generate(self, messages):
        msgs = []
        tmp_files = []

        for m in messages:
            parts = []
            for p in m["content"]:
                if p["type"] == "text":
                    parts.append({"type": "text", "text": p["text"]})
                else:
                    b64 = p["video_url"]["url"]
                    path = save_base64_to_file(b64, output_dir="tmp_video")
                    tmp_files.append(path)
                    parts.append({"type": "video", "path": path})
            msgs.append({"role": m["role"], "content": parts})
        inputs = self.processor.apply_chat_template(
            msgs,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.device, dtype=torch.bfloat16)

        out_ids = self.model.generate(**inputs, do_sample=False, max_new_tokens=self.max_new_tokens)
        text = self.processor.batch_decode(out_ids, skip_special_tokens=True)[0]

        for p in tmp_files:
            try:
                os.remove(p)
            except:
                pass

        return text

    def init_model(self):
        from transformers import AutoProcessor, AutoModelForImageTextToText

        self.processor = AutoProcessor.from_pretrained(
            self.model_name,
            trust_remote_code=self.trust_remote_code,
        )
        self.model = AutoModelForImageTextToText.from_pretrained(
            self.model_name,
            device_map=self.device,
            torch_dtype=torch.bfloat16,
            trust_remote_code=self.trust_remote_code,
        ).eval()
