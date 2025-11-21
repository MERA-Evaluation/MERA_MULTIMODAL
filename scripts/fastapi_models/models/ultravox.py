import os
import librosa
import transformers

from models.base_model import BaseModel
from utils.base64_to_file import save_base64_to_file


class UltravoxChatModel(BaseModel):
    def generate(self, messages):
        audio_paths = []
        audio_arrays = []

        turns = []
        audio_path = None
        audio_array = None
        sr = 16000

        for m in messages:
            role = m["role"]
            text_parts = []
            for part in m["content"]:
                if part["type"] == "text":
                    text_parts.append(part["text"])
                else:
                    b64 = part["audio_url"]["url"]
                    audio_path = save_base64_to_file(b64, output_dir="tmp_audio")
                    audio_array, _ = librosa.load(audio_path, sr=sr)
                    text_parts.append("<|audio|>")
                    audio_paths.append(audio_path)
                    audio_arrays.append(audio_array)

            text = "".join(text_parts)
            if text or role != "assistant":
                turns.append({"role": role, "content": text})

        payload = {
            "turns": turns,
            "sampling_rate": sr,
        }
        if audio_array is not None:
            payload["audio"] = audio_arrays

        result = self.pipe(payload, max_new_tokens=self.max_new_tokens)

        for audio_path in audio_paths:
            os.remove(audio_path)

        return result

    def init_model(self):
        self.pipe = transformers.pipeline(
            model=self.model_name,
            trust_remote_code=self.trust_remote_code,
            device_map=self.device,
            dtype="auto",
        )
