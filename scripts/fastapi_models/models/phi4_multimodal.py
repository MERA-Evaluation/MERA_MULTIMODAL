import os
import soundfile as sf
from PIL import Image

from transformers import AutoModelForCausalLM, AutoProcessor, GenerationConfig

from models.base_model import BaseModel
from utils.base64_to_file import save_base64_to_file


class Phi4MultimodalChatModel(BaseModel):
    def generate(self, messages):
        dialog = []
        audios = []
        images = []
        audio_idx = 1
        image_idx = 1
        files = []

        for m in messages:
            role = m["role"]
            if role == "user":
                dialog.append("<|user|>")
            else:
                dialog.append("<|assistant|>")

            for part in m["content"]:
                t = part["type"]
                if t == "text":
                    dialog.append(part["text"])
                elif t == "audio_url":
                    b64 = part["audio_url"]["url"]
                    path = save_base64_to_file(b64, output_dir="tmp_audio")
                    files.append(path)
                    audio, sr = sf.read(path)
                    audios.append((audio, sr))
                    dialog.append(f"<|audio_{audio_idx}|>")
                    audio_idx += 1
                elif t == "image_url":
                    b64 = part["image_url"]["url"]
                    path = save_base64_to_file(b64, output_dir="tmp_image")
                    files.append(path)
                    img = Image.open(path).convert('RGB')
                    images.append(img)
                    dialog.append(f"<|image_{image_idx}|>")
                    image_idx += 1

            dialog.append("<|end|>")

        dialog.append("<|assistant|>")
        prompt = "".join(dialog)

        if audios:
            inputs = self.processor(
                text=prompt,
                audios=audios,
                return_tensors="pt"
            ).to(self.device)
        if images:
            inputs = self.processor(
                text=prompt,
                images=images,
                return_tensors="pt"
            ).to(self.device)
        else:
            inputs = self.processor(
                text=prompt,
                return_tensors="pt"
            ).to(self.device)

        generate_ids = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            generation_config=self.generation_config,
        )
        generate_ids = generate_ids[:, inputs["input_ids"].shape[1]:]
        response = self.processor.batch_decode(
            generate_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]

        for f in files:
            os.remove(f)

        return response

    def init_model(self):
        self.processor = AutoProcessor.from_pretrained(
            self.model_name,
            trust_remote_code=self.trust_remote_code,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map=self.device,
            trust_remote_code=self.trust_remote_code,
            attn_implementation="eager",
            _attn_implementation="eager",

        ).eval()
        self.generation_config = GenerationConfig.from_pretrained(self.model_name)
