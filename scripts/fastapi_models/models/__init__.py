try:
    from models.qwen_audio import QwenAudioChatModel
except:
    QwenAudioChatModel = None

try:
    from models.phi4_multimodal import Phi4MultimodalChatModel
except:
    Phi4MultimodalChatModel = None

try:
    from models.seallms_audio import SeaLLMsAudioChatModel
except:
    SeaLLMsAudioChatModel = None

try:
    from models.ultravox import UltravoxChatModel
except:
    UltravoxChatModel = None

try:
    from models.qwen_video import Qwen2_5_VL_VideoChatModel
except:
    Qwen2_5_VL_VideoChatModel = None

try:
    from models.qwen_video2 import Qwen2_VL_VideoChatModel
except:
    Qwen2_VL_VideoChatModel = None

try:
    from models.qwen_video3 import Qwen3_VL_VideoChatModel
except:
    Qwen3_VL_VideoChatModel = None

try:
    from models.smolvlm import SmolVLM2VideoChatModel
except:
    SmolVLM2VideoChatModel = None

try:
    from models.internvl import InternVL35VideoChatModel
except:
    InternVL35VideoChatModel = None

try:
    from models.qwen_2_5_omni import Qwen2_5_Omni_MonoModalChatModel
except:
    Qwen2_5_Omni_MonoModalChatModel = None

try:
    from models.qwen_3_omni import Qwen3_Omni_MonoModalChatModel
except:
    Qwen3_Omni_MonoModalChatModel = None

try:
    from models.audio_flamingo3 import AudioFlamingo3_MonoModalChatModel
except:
    AudioFlamingo3_MonoModalChatModel = None

try:
    from models.minicpm import MiniCPM
except:
    MiniCPM = None

try:
    from models.llava_next import LlavaNext
except:
    LlavaNext = None

MODELS_REGISTRY = {
    "nvidia/audio-flamingo-3": AudioFlamingo3_MonoModalChatModel,
    "nvidia/audio-flamingo-3-hf": AudioFlamingo3_MonoModalChatModel,

    "Qwen/Qwen-Audio-Chat": QwenAudioChatModel,
    "microsoft/Phi-4-multimodal-instruct": Phi4MultimodalChatModel,
    "SeaLLMs/SeaLLMs-Audio-7B": SeaLLMsAudioChatModel,

    "fixie-ai/ultravox-v0_2": UltravoxChatModel,
    "fixie-ai/ultravox-v0_3": UltravoxChatModel,
    "fixie-ai/ultravox-v0_3-llama-3_2-1b": UltravoxChatModel,
    "fixie-ai/ultravox-v0_4": UltravoxChatModel,
    "fixie-ai/ultravox-v0_4-mistral_nemo": UltravoxChatModel,
    "fixie-ai/ultravox-v0_4_1-mistral-nemo": UltravoxChatModel,
    "fixie-ai/ultravox-v0_4_1-llama-3_1-8b": UltravoxChatModel,
    "fixie-ai/ultravox-v0_5-llama-3_2-1b": UltravoxChatModel,
    "fixie-ai/ultravox-v0_5-llama-3_1-8b": UltravoxChatModel,
    "fixie-ai/ultravox-v0_6-gemma-3-27b": UltravoxChatModel,
    "fixie-ai/ultravox-v0_6-qwen-3-32b": UltravoxChatModel,
    "fixie-ai/ultravox-v0_6-llama-3_1-8b": UltravoxChatModel,

    "Qwen/Qwen2-VL-2B-Instruct": Qwen2_VL_VideoChatModel,
    "Qwen/Qwen2-VL-7B-Instruct": Qwen2_VL_VideoChatModel,
    "Qwen/Qwen2-VL-72B-Instruct": Qwen2_VL_VideoChatModel,

    "Qwen/Qwen2.5-VL-3B-Instruct": Qwen2_5_VL_VideoChatModel,
    "Qwen/Qwen2.5-VL-7B-Instruct": Qwen2_5_VL_VideoChatModel,
    "Qwen/Qwen2.5-VL-32B-Instruct": Qwen2_5_VL_VideoChatModel,
    "Qwen/Qwen2.5-VL-72B-Instruct": Qwen2_5_VL_VideoChatModel,

    "Qwen/Qwen3-VL-2B-Instruct": Qwen3_VL_VideoChatModel,
    "Qwen/Qwen3-VL-4B-Instruct": Qwen3_VL_VideoChatModel,
    "Qwen/Qwen3-VL-8B-Instruct": Qwen3_VL_VideoChatModel,
    "Qwen/Qwen3-VL-30B-A3B-Instruct": Qwen3_VL_VideoChatModel,
    "Qwen/Qwen3-VL-32B-Instruct": Qwen3_VL_VideoChatModel,

    "Qwen/Qwen3-Omni-30B-A3B-Instruct": Qwen3_Omni_MonoModalChatModel,
    "Qwen/Qwen2.5-Omni-3B": Qwen2_5_Omni_MonoModalChatModel,
    "Qwen/Qwen2.5-Omni-7B": Qwen2_5_Omni_MonoModalChatModel,

    "HuggingFaceTB/SmolVLM2-256M-Video-Instruct": SmolVLM2VideoChatModel,
    "HuggingFaceTB/SmolVLM2-2.2B-Instruct": SmolVLM2VideoChatModel,
    "HuggingFaceTB/SmolVLM2-Instruct": SmolVLM2VideoChatModel,

    "OpenGVLab/InternVL3-1B": InternVL35VideoChatModel,
    "OpenGVLab/InternVL3-2B": InternVL35VideoChatModel,
    "OpenGVLab/InternVL3-8B": InternVL35VideoChatModel,
    "OpenGVLab/InternVL3-9B": InternVL35VideoChatModel,

    "OpenGVLab/InternVL3-1B-Instruct": InternVL35VideoChatModel,
    "OpenGVLab/InternVL3-2B-Instruct": InternVL35VideoChatModel,
    "OpenGVLab/InternVL3-8B-Instruct": InternVL35VideoChatModel,
    "OpenGVLab/InternVL3-9B-Instruct": InternVL35VideoChatModel,

    "OpenGVLab/InternVL3_5-1B": InternVL35VideoChatModel,
    "OpenGVLab/InternVL3_5-2B": InternVL35VideoChatModel,
    "OpenGVLab/InternVL3_5-4B": InternVL35VideoChatModel,
    "OpenGVLab/InternVL3_5-8B": InternVL35VideoChatModel,

    "OpenGVLab/InternVL3_5-1B-Instruct": InternVL35VideoChatModel,
    "OpenGVLab/InternVL3_5-2B-Instruct": InternVL35VideoChatModel,
    "OpenGVLab/InternVL3_5-4B-Instruct": InternVL35VideoChatModel,
    "OpenGVLab/InternVL3_5-8B-Instruct": InternVL35VideoChatModel,

    "openbmb/MiniCPM-o-2_6": MiniCPM,

    "llava-hf/LLaVA-NeXT-Video-7B-hf": LlavaNext,
    "llava-hf/LLaVA-NeXT-Video-34B-hf": LlavaNext,
}
