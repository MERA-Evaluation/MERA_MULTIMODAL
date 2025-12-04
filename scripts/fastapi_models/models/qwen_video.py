import os

from models.base_model import BaseModel
from utils.base64_to_file import save_base64_to_file
from qwen_vl_utils import process_vision_info


class Qwen2_5_VL_VideoChatModel(BaseModel):
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
                    parts.append({"type": "video", "video": f"file://{path}"})
            msgs.append({"role": m["role"], "content": parts})

        text = self.processor.apply_chat_template(
            msgs, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs, video_kwargs = process_vision_info(
            msgs, return_video_kwargs=True
        )
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
            **video_kwargs,
        ).to(self.device)

        generated = self.model.generate(**inputs, max_new_tokens=self.max_new_tokens)
        trimmed = [out[len(inp):] for inp, out in zip(inputs.input_ids, generated)]
        out = self.processor.batch_decode(
            trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

        for p in tmp_files:
            try:
                os.remove(p)
            except Exception:
                pass

        return out

    def init_model(self):
        from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

        self.processor = AutoProcessor.from_pretrained(
            self.model_name, trust_remote_code=self.trust_remote_code
        )
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            self.model_name,
            device_map="auto",
            torch_dtype="auto",
            trust_remote_code=self.trust_remote_code,
        ).eval()
