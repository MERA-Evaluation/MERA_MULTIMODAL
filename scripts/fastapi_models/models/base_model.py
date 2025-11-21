from __future__ import annotations
from abc import ABC, abstractmethod


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
        self.init_model()

    @abstractmethod
    def generate(self, request):
        raise NotImplementedError

    @abstractmethod
    def init_model(self):
        raise NotImplementedError
