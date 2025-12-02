import os
import json
import requests
import hashlib

from models.base_model import BaseModel
from utils.base64_to_file import save_base64_to_file


class CustomModel(BaseModel):
    def _generate(self, messages):
        msgs = []

        for m in messages:
            text_content = ""
            attachments = []

            for p in m["content"]:
                if p["type"] == "text":
                    text_content += p["text"]
                else:
                    b64 = p["audio_url"]["url"]
                    b64_hash = hashlib.sha256(b64.encode("utf-8")).hexdigest()

                    if b64_hash in self.base_file_id_storage:
                        audio_id = self.base_file_id_storage[b64_hash]
                    else:
                        path = save_base64_to_file(b64, output_dir="tmp_audio")
                        audio_id = self.upload_file(path)["id"]
                        self.base_file_id_storage[b64_hash] = audio_id
                        json.dump(self.base_file_id_storage, open(self.base_file_id_storage_path, "w"), indent=4)

                    attachments.append(audio_id)

            msgs.append({"role": m["role"], "content": text_content, "attachments": attachments})

        result = self.shoot(msgs)["text"]
        return result

    def init_model(self):
        self.base_url = os.getenv("CUSTOM_MODEL_URL")
        self.base_file_id_storage_path = os.getenv("FILE_ID_STORAGE_PATH", "storage")
        os.makedirs(self.base_file_id_storage_path, exist_ok=True)
        self.base_file_id_storage_path = os.path.join(self.base_file_id_storage_path, "storage.json")
        try:
            self.base_file_id_storage = json.load(open(self.base_file_id_storage_path))
        except:
            self.base_file_id_storage = {}
        self.token = os.getenv("CUSTOM_MODEL_TOKEN")

    def upload_file(self, file_path) -> dict:
        url = f"{self.base_url}/files"

        access_token = self.token

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        with open(file_path, 'rb') as file:
            file_name = os.path.basename(file_path)
            file_type = file_path.split('.')[-1]
            file_type_to_mime = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'gif': 'image/gif',
                'bmp': 'image/bmp',
                'wav': 'audio/wav',
                'mp3': 'audio/mpeg',
            }
            files = {
                'file': (file_name, file, file_type_to_mime[file_type])
            }
            data = {
                "purpose": "general"
            }
            response = requests.post(url, verify=False, headers=headers, files=files, data=data)

        if response.status_code == 200:
            result = response.json()
            result["status"] = "success"
            result["status_code"] = response.status_code
        else:
            result = {
                "status": "error",
                "status_code": response.status_code,
            }

        return result

    def shoot(self, messages: list[dict]) -> dict:
        url = f"{self.base_url}/chat/completions"
        access_token = self.token

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        data = {
            "model": os.getenv("CUSTOM_MODEL_NAME"),
            "profanity_check": False,
            "messages": messages
        }

        response = requests.post(url, verify=False, headers=headers, json=data)

        if response.status_code == 200:
            repsjsn = response.json()
            result = {
                "text": repsjsn["choices"][0]["message"]["content"],
                "status": "success",
                "status_code": response.status_code
            }
        else:
            result = {
                "status": "error",
                "status_code": response.status_code,
            }

        return result
