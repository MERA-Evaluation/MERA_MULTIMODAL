import os

from models.base_model import BaseModel
from utils.base64_to_file import save_base64_to_file

import math
import numpy as np
from PIL import Image
from moviepy import VideoFileClip
import tempfile
import librosa
import soundfile as sf
import torch


class MiniCPM(BaseModel):
    def get_video_chunk_content(self, video_path, flatten=True):
        video = VideoFileClip(video_path)

        if video.audio is not None:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_audio_file:
                temp_audio_file_path = temp_audio_file.name
                video.audio.write_audiofile(temp_audio_file_path, codec="pcm_s16le", fps=16000)
                audio_np, sr = librosa.load(temp_audio_file_path, sr=16000, mono=True)
        else:
            audio_np, sr = None, None
        num_units = math.ceil(video.duration)

        contents= []
        for i in range(num_units):
            frame = video.get_frame(i+1)
            image = Image.fromarray((frame).astype(np.uint8))
            if audio_np is not None:
                audio = audio_np[sr*i:sr*(i+1)]
                x = ["<unit>", image, audio]
            else:
                x = ["<unit>", image]
            if flatten:
                contents.extend(x)
            else:
                contents.append(x)

        return contents

    def _generate(self, messages):
        conversation, tmp_files = [], []

        for m in messages:
            parts = []
            first_audio = True
            for p in m["content"]:
                t = p["type"]
                if t == "text":
                    parts.append(p["text"])
                elif t == "image_url":
                    b64 = p["image_url"]["url"]
                    path = save_base64_to_file(b64, output_dir="tmp_image")
                    img = Image.open(path).convert('RGB')
                    parts.append(img)
                    tmp_files.append(path)
                elif t == "audio_url":
                    if not first_audio:
                        continue
                    first_audio = False
                    b64 = p["audio_url"]["url"]
                    path = save_base64_to_file(b64, output_dir="tmp_audio")
                    tmp_files.append(path)
                    audio_input, _ = librosa.load(path, sr=16000, mono=True)
                    parts.append(audio_input)
                else:
                    b64 = p["video_url"]["url"]
                    path = save_base64_to_file(b64, output_dir="tmp_video")
                    contents = self.get_video_chunk_content(path)
                    tmp_files.append(path)
                    parts.extend(contents)
            conversation.append({"role": m["role"], "content": parts})

        res = self.model.chat(
            msgs=conversation,
            tokenizer=self.tokenizer,
            max_new_tokens=self.max_new_tokens,
            use_tts_template=False,
            generate_audio=False,
            use_image_id=False,
            return_dict=True
        )

        for p in tmp_files:
            try:
                os.remove(p)
            except Exception:
                pass

        return res.text

    def init_model(self):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from unittest.mock import patch
        from transformers.dynamic_module_utils import get_imports

        def fixed_get_imports(filename: str | os.PathLike) -> list[str]:
            imports = get_imports(filename)
            if "flash_attn" in imports:
                imports.remove("flash_attn")
            return imports

        with patch("transformers.dynamic_module_utils.get_imports", fixed_get_imports):
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                attn_implementation='sdpa',
                torch_dtype=torch.bfloat16,
                init_vision=True,
                init_audio=True,
                init_tts=True
            )

            self.model = self.model.eval().cuda()
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
