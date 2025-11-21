import os

from transformers import AutoModelForCausalLM, AutoTokenizer

from models.base_model import BaseModel
from utils.base64_to_file import save_base64_to_file


class QwenAudioChatModel(BaseModel):
    def generate(self, messages):
        parts = []
        audio_files = []
        for m in messages:
            for part in m["content"]:
                t = part["type"]
                if t == "text":
                    parts.append({"text": part["text"]})
                else:
                    b64 = part["audio_url"]["url"]
                    audio_file_path = save_base64_to_file(b64, output_dir="tmp_audio")
                    audio_files.append(audio_file_path)
                    parts.append({"audio": audio_file_path})

        query = self.tokenizer.from_list_format(parts)
        response, _ = self.model.chat(self.tokenizer, query=query, max_new_tokens=self.max_new_tokens, history=None)
        if query in response:
            response = response[len(query):]

        for audio_file in audio_files:
            os.remove(audio_file)

        return response

    def init_model(self):
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=self.trust_remote_code
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            device_map=self.device,
            trust_remote_code=self.trust_remote_code
        ).eval()
