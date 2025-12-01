import os
import requests

from models.base_model import BaseModel


class APIModel(BaseModel):
    def _generate(self, messages):
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_new_tokens,
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=600,
            )
            response.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"APIModel: request failed: {e}")

        data = response.json()

        return data["choices"][0]["message"]["content"]

    def init_model(self):
        base_url = os.getenv("FASTAPI_OPENAI_API_URL", "http://localhost")
        port = os.getenv("FASTAPI_OPENAI_API_PORT", "8000")

        base_url = base_url.rstrip("/")

        self.api_url = f"{base_url}:{port}/v1/chat/completions"
