import os
import requests

from models.base_model import BaseModel


class CustomVisionModel(BaseModel):
    def _generate(self, messages):
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_new_tokens,
            "response_format": {},
        }

        try:
            response = requests.post(self.base_url, verify=False, headers=self.headers, json=payload)
            response.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"CustomVisionModel: request failed: {e}")

        data = response.json()

        return data["choices"][0]["message"]["content"]

    def init_model(self):
        self.base_url = os.getenv("CUSTOM_VISION_MODEL_URL")
        self.token = os.getenv("CUSTOM_VISION_MODEL_TOKEN")
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "accept": "application/json"
        }
