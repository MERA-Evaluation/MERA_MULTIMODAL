import os
import librosa
import torch

from transformers import AutoProcessor, Qwen2AudioForConditionalGeneration

from models.base_model import BaseModel
from utils.base64_to_file import save_base64_to_file


class SeaLLMsAudioChatModel(BaseModel):
    def _generate(self, messages):
        audio_files = []
        audios = []
        sr = self.processor.feature_extractor.sampling_rate

        for m in messages:
            for part in m["content"]:
                if part["type"] != "text":
                    b64 = part["audio_url"]["url"]
                    audio_path = save_base64_to_file(b64, output_dir="tmp_audio")
                    audio_files.append(audio_path)
                    audio, _ = librosa.load(audio_path, sr=sr)
                    audios.append(audio)

        prompt = self.processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=False,
        )

        if audios:
            inputs = self.processor(
                text=prompt,
                audios=audios,
                sampling_rate=sr,
                return_tensors="pt",
                padding=True,
            )
        else:
            inputs = self.processor(
                text=prompt,
                return_tensors="pt",
                padding=True,
            )

        inputs = {k: v.to(self.device) for k, v in inputs.items() if v is not None}

        output_ids = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
            temperature=0.0,
        )
        gen_ids = output_ids[:, inputs["input_ids"].size(1):]

        response = self.processor.batch_decode(
            gen_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]

        for f in audio_files:
            os.remove(f)

        return response

    def init_model(self):
        self.processor = AutoProcessor.from_pretrained(
            self.model_name,
            trust_remote_code=self.trust_remote_code,
        )
        self.model = Qwen2AudioForConditionalGeneration.from_pretrained(
            self.model_name,
            device_map=self.device,
            torch_dtype="auto",
            trust_remote_code=self.trust_remote_code,
        ).eval()
