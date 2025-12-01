from __future__ import annotations
from abc import ABC, abstractmethod
import os

from utils.base64_to_file import save_base64_to_file


class BaseModel(ABC):
    def __init__(
        self,
        model_name: str,
        trust_remote_code: bool = True,
        device: str = "cuda",
        max_new_tokens: int = 10000,
        *args,
        **kwargs,
    ):
        self.model_name = model_name
        self.trust_remote_code = trust_remote_code
        self.device = device
        self.max_new_tokens = max_new_tokens
        self.gigaam_model = None
        self.init_model()

    @abstractmethod
    def _generate(self, request):
        raise NotImplementedError

    def generate(self, request):
        if os.getenv("PROCESS_AUDIO_WITH_GIGAAM"):
            for message in request:
                for content in message["content"]:
                    if content["type"] == "audio_url":
                        from transformers import AutoModel

                        audio_file = save_base64_to_file(content["audio_url"]["url"], output_dir="gigaam_tmp")

                        if self.gigaam_model is None:
                            revision = os.getenv("GIGAAM_REVISION", "e2e_rnnt")
                            self.gigaam_model = AutoModel.from_pretrained(
                                "ai-sage/GigaAM-v3",
                                revision=revision,
                                trust_remote_code=True,
                            ).to(self.device)

                        try:
                            transcription = self.gigaam_model.transcribe(audio_file)
                        except:
                            transcription = self.gigaam_model.transcribe_longform(audio_file)
                            transcription = "\n".join(t["transcription"] for t in transcription)

                        content["type"] = "text"
                        content["text"] = transcription
                        del content["audio_url"]

                        try:
                            os.remove(audio_file)
                        except:
                            print(f"Could not remove {audio_file}")

        return self._generate(request)

    @abstractmethod
    def init_model(self):
        raise NotImplementedError
