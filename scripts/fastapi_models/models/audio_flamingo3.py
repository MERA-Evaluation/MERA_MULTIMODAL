import os
from utils.base64_to_file import save_base64_to_file
from models.base_model import BaseModel


class AudioFlamingo3_MonoModalChatModel(BaseModel):
    def _generate(self, messages):
        conversation, tmp_files = [], []

        for m in messages:
            parts = []
            for p in m["content"]:
                t = p["type"]
                if t == "text":
                    parts.append({"type": "text", "text": p["text"]})
                elif t == "audio_url":
                    if not tmp_files:
                        b64 = p["audio_url"]["url"]
                        path = save_base64_to_file(b64, output_dir="tmp_audio")
                        tmp_files.append(path)
                        parts.append({"type": "audio", "path": path})
                else:
                    raise ValueError("Not known modality")
            conversation.append({"role": m["role"], "content": parts})

        input_dict = self.processor.apply_chat_template(
            conversation,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
        ).to(self.device)

        outputs = self.model.generate(**input_dict, max_new_tokens=self.max_new_tokens)

        gen_ids = outputs[:, input_dict.input_ids.shape[1]:]

        text = self.processor.batch_decode(gen_ids, skip_special_tokens=True)

        for p in tmp_files:
            try:
                os.remove(p)
            except Exception:
                pass

        return text[0]

    def init_model(self):
        from transformers import AudioFlamingo3ForConditionalGeneration, AutoProcessor
        self.model = AudioFlamingo3ForConditionalGeneration.from_pretrained(self.model_name, device_map="auto").eval()
        self.processor = AutoProcessor.from_pretrained(self.model_name)
