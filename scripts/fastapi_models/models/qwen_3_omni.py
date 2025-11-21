import os
import torch

from qwen_omni_utils import process_mm_info

from models.base_model import BaseModel
from utils.base64_to_file import save_base64_to_file


class Qwen3_Omni_MonoModalChatModel(BaseModel):
    def generate(self, messages):
        conversation, tmp_files = [], []

        for m in messages:
            parts = []
            for p in m["content"]:
                t = p["type"]
                if t == "text":
                    parts.append({"type": "text", "text": p["text"]})
                elif t == "image_url":
                    b64 = p["image_url"]["url"]
                    path = save_base64_to_file(b64, output_dir="tmp_image")
                    tmp_files.append(path)
                    parts.append({"type": "image", "image": f"file://{path}"})
                elif t == "audio_url":
                    b64 = p["audio_url"]["url"]
                    path = save_base64_to_file(b64, output_dir="tmp_audio")
                    tmp_files.append(path)
                    parts.append({"type": "audio", "audio": f"file://{path}"})
                else:
                    b64 = p["video_url"]["url"]
                    path = save_base64_to_file(b64, output_dir="tmp_video")
                    tmp_files.append(path)
                    parts.append({"type": "video", "video": f"file://{path}"})
            conversation.append({"role": m["role"], "content": parts})

        use_audio_in_video = False
        text = self.processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
        audios, images, videos = process_mm_info(conversation, use_audio_in_video=use_audio_in_video)
        inputs = self.processor(text=text, audio=audios, images=images, videos=videos,
                           return_tensors="pt", padding=True, use_audio_in_video=use_audio_in_video)
        inputs = inputs.to(self.device)

        with torch.amp.autocast("cuda"):
            text_ids, _ = self.model.generate(**inputs, use_audio_in_video=use_audio_in_video, max_new_tokens=self.max_new_tokens)

        gen_ids = text_ids[:, inputs["input_ids"].shape[1] :]

        text = self.processor.batch_decode(gen_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

        for p in tmp_files:
            try:
                os.remove(p)
            except Exception:
                pass

        return text

    def init_model(self):
        from transformers import Qwen3OmniMoeForConditionalGeneration, Qwen3OmniMoeProcessor

        self.model = Qwen3OmniMoeForConditionalGeneration.from_pretrained(
            self.model_name,
            dtype="bfloat16",
            device_map="auto",
            enable_audio_output=False,
        ).eval()
        self.processor = Qwen3OmniMoeProcessor.from_pretrained(self.model_name)
