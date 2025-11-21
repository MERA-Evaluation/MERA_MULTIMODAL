import av
import torch
import numpy as np
import os

from models.base_model import BaseModel
from utils.base64_to_file import save_base64_to_file


class LlavaNext(BaseModel):
    def generate(self, messages):
        msgs = []
        tmp_files = []

        for m in messages:
            parts = []
            for p in m["content"]:
                if p["type"] == "text":
                    parts.append({"type": "text", "text": p["text"]})
                else:
                    b64 = p["video_url"]["url"]
                    video_path = save_base64_to_file(b64, output_dir="tmp_video")
                    tmp_files.append(video_path)
                    parts.append({"type": "video"})
            msgs.append({"role": m["role"], "content": parts})

        prompt = self.processor.apply_chat_template(msgs, add_generation_prompt=True)
        container = av.open(video_path)

        total_frames = container.streams.video[0].frames
        indices = np.arange(0, total_frames, total_frames / 8).astype(int)
        clip = self.read_video_pyav(container, indices)
        inputs_video = self.processor(text=prompt, videos=clip, padding=True, return_tensors="pt").to(self.model.device)

        input_ids_len = inputs_video.input_ids.size(1)

        output = self.model.generate(**inputs_video, max_new_tokens=self.max_new_tokens, do_sample=False)
        text = self.processor.decode(output[0][input_ids_len:], skip_special_tokens=True)

        for p in tmp_files:
            try:
                os.remove(p)
            except:
                pass

        return text

    def read_video_pyav(self, container, indices):
        '''
        Decode the video with PyAV decoder.
        Args:
            container (`av.container.input.InputContainer`): PyAV container.
            indices (`List[int]`): List of frame indices to decode.
        Returns:
            result (np.ndarray): np array of decoded frames of shape (num_frames, height, width, 3).
        '''
        frames = []
        container.seek(0)
        start_index = indices[0]
        end_index = indices[-1]
        for i, frame in enumerate(container.decode(video=0)):
            if i > end_index:
                break
            if i >= start_index and i in indices:
                frames.append(frame)
        return np.stack([x.to_ndarray(format="rgb24") for x in frames])

    def init_model(self):
        from transformers import LlavaNextVideoProcessor, LlavaNextVideoForConditionalGeneration

        self.model = LlavaNextVideoForConditionalGeneration.from_pretrained(
            self.model_name,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
        ).to(self.device).eval()

        self.processor = LlavaNextVideoProcessor.from_pretrained(self.model_name)
