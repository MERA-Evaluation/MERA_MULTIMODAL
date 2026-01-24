# MERA Multimodal

<p align="center">
  <picture>
    <img alt="MERA Multimodal" src="mera-logo.svg" style="max-width: 100%;">
  </picture>
</p>

<p align="center">
    <a href="https://opensource.org/licenses/MIT">
    <img alt="License" src="https://img.shields.io/badge/License-MIT-yellow.svg">
    </a>
    <a href="https://github.com/MERA-Evaluation/MERA_MULTIMODAL/tree/main">
    <img alt="Release" src="https://img.shields.io/badge/release-v1.0.0-blue">
    </a>

</p>

<h2 align="center">
    <p> MERA Multimodal: A Unified Framework for Evaluating Multimodal LLMs (Image, Audio, Video).
</p>
</h2>

## 🚀 About

**MERA Multimodal** brings together a domain-specific collection of evaluation tasks for large multimodal models (MLLMs) under one roof. Built on top of the [Language Model Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness) (v0.4.9), it enables researchers and practitioners to:

- **Compare models** on identical tasks and metrics
- **Reproduce results** with fixed prompts and few-shot settings
- **Submit** standardized ZIP archives for leaderboard integration

MERA is an independent open project of the [AI Alliance](https://a-ai.ru/) at the intersection of academia and industry. We are developing new tests for evaluating large multimodal models (with images, audio, and video).

> **Data leakage and data contamination are critical issues in benchmarking. Therefore, for all private tests, we use images, audio, and video created from scratch that are not available on the web and, as a consequence, cannot be in the training of models. For the same reason, evaluation results on public tasks are not included in the model ranking.**


## 🔍 Datasets Overview

### Image-to-Text Tasks

| Name | Task Name | Type | Metrics | Size |
| --- | --- | --- | --- | --- |
| ruCommonVQA | rucommonvqa | Public | EM, JS | 3015 |
| ruCLEVR | ruclevr | Public | EM, JS | 1148 |
| WEIRD | weird | Public | EM, JS | 814 |
| ruNaturalScienceVQA | runaturalsciencevqa | Public | EM, JS | 363 |
| LabTabVQA | labtabvqa | Private | EM, JS | 339 |
| RealVQA | realvqa | Private | EM, JS | 773 |
| ruHHH-Image | ruhhh_image | Private | group_EM, group_JS | 595 |
| ruMathVQA | rumathvqa | Private | EM, JS | 502 |
| ruTiE-Image | rutie_vision_gen | Private | EM, JS | 1500 |
| SchoolScienceVQA | schoolsciencevqa | Private | EM, JS | 4227 |
| UniScienceVQA | unisciencevqa | Private | EM, JS | 7432 |

### Audio-to-Text Tasks

| Name | Task Name | Type | Metrics | Size |
| --- | --- | --- | --- | --- |
| ruEnvAQA | ruenvaqa | Public | EM, JS | 596 |
| RuSLUn | ruslun | Public | EM, F1 | 741 |
| AQUARIA | aquaria | Private | EM, JS | 738 |
| ruTiE-Audio | rutie_audio_gen | Private | EM, JS | 1500 |

### Video-to-Text Tasks

| Name | Task Name | Type | Metrics | Size |
| --- | --- | --- | --- | --- |
| CommonVideoQA | commonvideoqa | Public | EM, JS | 1200 |
| RealVideoQA | realvideoqa | Private | EM, JS | 671 |
| ruHHH-Video | ruhhh_video | Private | group_EM, group_JS | 911 |

Datasets are available in the [🤗HF Hub collection](https://huggingface.co/collections/MERA-evaluation/mera-multimodality-675859d796c41b994ae860b4).


## 🛠 Getting Started <a name="evaluation"></a>

### Clone the repository with submodule

First, you need to clone the MERA_MULTIMODAL repository and load the submodule:

```bash
### Go to the folder where the repository will be cloned ###
mkdir mera_multimodal
cd mera_multimodal

### Clone & install core libs ###
git clone --recurse-submodules https://github.com/MERA-Evaluation/MERA_MULTIMODAL.git
cd MERA_MULTIMODAL
```

If you have cloned the repository with no submodules downloaded (empty directory), run this code to fix it:

```bash
git submodule update --init --recursive
```

### Installing dependencies

**Remote Scoring**: quick setup for cloud-based scoring — install only core dependencies, run the evaluation, and submit the resulting ZIP archive to our website to get the score.

Install lm-eval library and optional packages for evaluations:

```bash
### Install lm-eval ###
cd lm-evaluation-harness
pip install -e .

### Install required dependencies for audio datasets ###
pip install librosa soundfile

### Install required dependencies for video datasets ###
pip install torchcodec av decord

### Install additional libs for models evaluation [Optional] ###
# vLLM engine
pip install -e ".[vllm]"
# API scoring (for vLLM serving and closed API models)
pip install -e ".[api]"

### Go to MERA_MULTIMODAL folder ###
cd ../
```

### Running evaluations

We provide multiple ways to run evaluations depending on your setup.

#### Image datasets

> Via transformers:

```bash
HF_DATASETS_CACHE="ds_cache" HF_TOKEN="YOUR_TOKEN" CUDA_VISIBLE_DEVICES=0 lm-eval \
    --model hf-multimodal \
    --model_args pretrained=Qwen/Qwen2-VL-2B-Instruct,dtype=bfloat16 \
    --device cuda \
    --output_path="$PWD/results" \
    --batch_size=1 \
    --predict_only \
    --log_samples \
    --seed 1234 \
    --num_fewshot=0 \
    --trust_remote_code \
    --apply_chat_template \
    --fewshot_as_multiturn \
    --include_path ./multimodal_tasks \
    --tasks weird,labtabvqa
```

> Via vLLM:

```bash
LOAD_BASE64=1 HF_DATASETS_CACHE="ds_cache" HF_TOKEN="YOUR_TOKEN" CUDA_VISIBLE_DEVICES=0 lm-eval \
    --model vllm-vlm \
    --model_args pretrained=Qwen/Qwen2-VL-2B-Instruct,dtype=bfloat16 \
    --device cuda \
    --output_path="$PWD/results" \
    --batch_size=1 \
    --predict_only \
    --log_samples \
    --seed 1234 \
    --num_fewshot=0 \
    --trust_remote_code \
    --apply_chat_template \
    --fewshot_as_multiturn \
    --pass_multimodal_args_to_chat_history \
    --include_path ./multimodal_tasks \
    --tasks ruclevr,rumathvqa
```

> Via vLLM serve:

```bash
CUDA_VISIBLE_DEVICES=0 vllm serve Qwen/Qwen2-VL-2B-Instruct \
    --trust-remote-code \
    --limit-mm-per-prompt '{"image": 20}' \
    --seed 1234 \
    --port 1231 \
    --dtype bfloat16
```

```bash
OPENAI_API_KEY="EMPTY" HF_DATASETS_CACHE="ds_cache" LOAD_BASE64=1 HF_TOKEN="YOUR_TOKEN" lm-eval \
    --model openai-chat-completions \
    --model_args model=Qwen/Qwen2-VL-2B-Instruct,base_url="http://localhost:1231/v1/chat/completions",num_concurrent=2,max_retries=3,timeout=90000 \
    --output_path="$PWD/results" \
    --batch_size=1 \
    --predict_only \
    --log_samples \
    --seed 1234 \
    --num_fewshot=0 \
    --trust_remote_code \
    --apply_chat_template \
    --fewshot_as_multiturn \
    --pass_multimodal_args_to_chat_history \
    --include_path ./multimodal_tasks \
    --tasks uniscienceqa
```

#### Video datasets

> Via transformers:

Currently tested and working models: `llava-hf/LLaVA-NeXT-Video-7B-hf` (LLaVA-NeXT-Video family), `Qwen/Qwen2-VL-2B-Instruct` (Qwen VL family).

```bash
HF_DATASETS_CACHE="ds_cache" HF_TOKEN="YOUR_TOKEN" CUDA_VISIBLE_DEVICES=0 lm-eval \
    --model hf_video_llava \
    --model_args pretrained=llava-hf/LLaVA-NeXT-Video-7B-hf,dtype=bfloat16 \
    --device cuda \
    --output_path="$PWD/results" \
    --batch_size=1 \
    --predict_only \
    --log_samples \
    --seed 1234 \
    --num_fewshot=0 \
    --trust_remote_code \
    --apply_chat_template \
    --fewshot_as_multiturn \
    --include_path ./multimodal_tasks \
    --tasks ruhhh_video,commonvideoqa,realvideoqa
```

> Video to frames conversion:

Use `pass_multimodal_args_to_chat_history` and `replace_videos_with_images_amount` flags. The latter specifies how many frames to uniformly sample from the video.

```bash
HF_DATASETS_CACHE="ds_cache" HF_TOKEN="YOUR_TOKEN" CUDA_VISIBLE_DEVICES=0 lm-eval \
    --model vllm-vlm \
    --model_args pretrained=Qwen/Qwen2-VL-2B-Instruct,dtype=bfloat16 \
    --device cuda \
    --output_path="$PWD/results" \
    --batch_size=1 \
    --predict_only \
    --log_samples \
    --seed 1234 \
    --num_fewshot=0 \
    --trust_remote_code \
    --apply_chat_template \
    --fewshot_as_multiturn \
    --pass_multimodal_args_to_chat_history \
    --replace_videos_with_images_amount 1 \
    --include_path ./multimodal_tasks \
    --tasks ruhhh_video,commonvideoqa,realvideoqa
```

#### Audio datasets

Audio models don't have a universal interface, so different modules are used for different model families.

> Qwen/Qwen2-Audio-7B-Instruct:

```bash
HF_DATASETS_CACHE="ds_cache" HF_TOKEN="YOUR_TOKEN" CUDA_VISIBLE_DEVICES=0 lm-eval \
    --model hf-audiolm-qwen \
    --model_args pretrained=Qwen/Qwen2-Audio-7B-Instruct,dtype=bfloat16 \
    --device cuda \
    --output_path="$PWD/results" \
    --batch_size=1 \
    --predict_only \
    --log_samples \
    --seed 1234 \
    --num_fewshot=0 \
    --trust_remote_code \
    --apply_chat_template \
    --fewshot_as_multiturn \
    --include_path ./multimodal_tasks \
    --tasks ruenvaqa,aquaria
```

> Audio models via vLLM:

```bash
CUDA_VISIBLE_DEVICES=0 vllm serve fixie-ai/ultravox-v0_5-llama-3_1-8b \
    --trust-remote-code \
    --limit-mm-per-prompt '{"audio": 20}' \
    --seed 1234 \
    --port 1231 \
    --dtype bfloat16
```

```bash
OPENAI_API_KEY="EMPTY" HF_DATASETS_CACHE="ds_cache" HF_TOKEN="YOUR_TOKEN" lm-eval \
    --model openai-chat-completions \
    --model_args model=fixie-ai/ultravox-v0_5-llama-3_1-8b,base_url="http://localhost:1231/v1/chat/completions",num_concurrent=1,max_retries=3,timeout=90000 \
    --output_path="rutie_audio_results" \
    --batch_size=1 \
    --predict_only \
    --log_samples \
    --seed 1234 \
    --num_fewshot=3 \
    --trust_remote_code \
    --apply_chat_template \
    --fewshot_as_multiturn \
    --pass_multimodal_args_to_chat_history \
    --include_path ./multimodal_tasks \
    --tasks rutie_audio_gen
```

<details>
<summary>More audio model examples...</summary>

> Qwen/Qwen-Audio-Chat (may not work on some transformers versions):

```bash
pip install matplotlib transformers_stream_generator tensorboard transformers==4.44.2 numpy==1.26
```

```bash
HF_DATASETS_CACHE="ds_cache" HF_TOKEN="YOUR_TOKEN" CUDA_VISIBLE_DEVICES=0 lm-eval \
    --model hf-audiolm-qwen-audio-chat \
    --model_args pretrained=Qwen/Qwen-Audio-Chat,dtype=bfloat16 \
    --device cuda \
    --output_path="$PWD/results" \
    --batch_size=1 \
    --predict_only \
    --log_samples \
    --seed 1234 \
    --num_fewshot=0 \
    --trust_remote_code \
    --apply_chat_template \
    --fewshot_as_multiturn \
    --include_path ./multimodal_tasks \
    --tasks ruenvaqa
```

> openbmb/MiniCPM-o-2_6 (doesn't work on latest transformers versions):

```bash
pip install vector_quantize_pytorch vocos transformers==4.44.2 numpy==1.26
```

```bash
HF_DATASETS_CACHE="ds_cache" HF_TOKEN="YOUR_TOKEN" CUDA_VISIBLE_DEVICES=0 lm-eval \
    --model hf-audiolm-minicpm \
    --model_args pretrained=openbmb/MiniCPM-o-2_6,dtype=bfloat16 \
    --device cuda \
    --output_path="$PWD/res" \
    --batch_size=1 \
    --predict_only \
    --log_samples \
    --seed 1234 \
    --num_fewshot=0 \
    --trust_remote_code \
    --apply_chat_template \
    --fewshot_as_multiturn \
    --include_path ./multimodal_tasks \
    --tasks aquaria
```

> fixie-ai/ultravox-v0_2 (and other ultravox models):

```bash
pip install numpy==1.26
```

```bash
HF_DATASETS_CACHE="ds_cache" HF_TOKEN="YOUR_TOKEN" CUDA_VISIBLE_DEVICES=0 lm-eval \
    --model hf-audiolm-ultravox \
    --model_args pretrained=fixie-ai/ultravox-v0_2,dtype=bfloat16 \
    --device cuda \
    --output_path="$PWD/res" \
    --batch_size=1 \
    --predict_only \
    --log_samples \
    --seed 1234 \
    --num_fewshot=0 \
    --trust_remote_code \
    --apply_chat_template \
    --fewshot_as_multiturn \
    --include_path ./multimodal_tasks \
    --tasks aquaria
```

</details>

#### Preparing submission archive

```bash
python scripts/log_to_submission.py \
    --outputs_dir <output_path from evaluation script> \
    --dst_dir <where to save the archive> \
    --model_args <model_args string from evaluation script>
```

<details>
<summary>FastAPI service for custom models...</summary>

For some models, specific inference code is required that is not described in the general harness modules. We provide a FastAPI wrapper that allows you to add support for almost any model with minimal effort. Code is available at [/scripts/fastapi_models/](/scripts/fastapi_models/).

To add your own model, create a `.py` file with a class inherited from [BaseModel](scripts/fastapi_models/models/base_model.py). Then implement `generate` and `init_model` methods. Example: [Qwen2.5-Omni](scripts/fastapi_models/models/qwen_2_5_omni.py).

After adding the required models, start the server:

```bash
uvicorn main:app --port 1234
```

Then run evaluation via openai-chat-completions, sending requests to http://localhost:1234 (pass in `base_url`).

</details>

<details>
<summary>lm-eval modifications and features...</summary>

1. **Object loading modes** via environment variables `LOAD_BYTES`, `LOAD_BASE64`, `LOAD_OBJECT`, `LOAD_FILES`:
   - `LOAD_BYTES=1` - object as bytes
   - `LOAD_BASE64=1` - object as dict with `url` key containing base64 string
   - `LOAD_OBJECT=1` - Python object (e.g., PIL.Image for images) - **default**
   - `LOAD_FILES=1` - dict with `type` and path to local file

2. **Tensor Parallel mode** for transformers:
   ```bash
   HARNESS_TENSOR_PARALLEL=1 accelerate launch --num_processes <TP_SIZE> lm-eval \
       --model hf-multimodal \
       --model_args pretrained=<MODEL_NAME>,tp_plan="auto" \
       <OTHER ARGUMENTS>
   ```

3. **`--pass_multimodal_args_to_chat_history`** flag passes multimodal data directly in the role dict.

4. **`--replace_videos_with_images_amount N`** converts video to N uniformly sampled frames.

5. **Image resizing** via `--model_args` parameters: `image_width`, `image_height`, `image_max_side`.

6. **Caching** via `--use_cache PATH/TO/CACHE/FILE` to resume interrupted evaluations.

</details>

<details>
<summary>Notes on ruTiE-Image and ruTiE-Audio...</summary>

`ruTiE` (rutie_audio_gen, rutie_vision_gen) must be run with `pass_multimodal_args_to_chat_history` flag.

ruTiE builds a dialog history where each new question includes previous questions and model answers. Use `--num_fewshot N` to limit history size (N previous questions). For all other datasets, use `--num_fewshot 0`.

Recommended: start with `--num_fewshot 5`, decrease to 0 if OOM occurs. If ruTiE still fails with 0, use rutie_audio_default or rutie_vision_default instead.

</details>


## 📁 Repository Structure

```text
MERA_MULTIMODAL/
├── multimodal_tasks/            # Code for each task
├── datasets/                    # Task descriptions, metadata, readme
├── docs/                        # Additional documentation and design notes
│   ├── dataset_formatting.md    # Dataset formatting requirements
│   ├── model_scoring.md         # How to use lm-eval to evaluate the LMs
│   ├── task_codebase.md         # How to add a new task to the codebase
│   └── skills_tax.md            # MLLM skills taxonomy
├── skills/                      # Skills taxonomy data
├── scripts/                     # Helpers: run evaluations, FastAPI service, scoring
├── tests/                       # Automated testing for datasets
├── lm-evaluation-harness/       # Submodule (codebase)
└── utils/                       # Utility scripts
```


## 💪 How to Join the Leaderboard

Follow these steps to see your model on the Leaderboard:

1. **Run Remote Scoring**
   Evaluate the benchmark in the **Remote Scoring** regime (see [🛠 Getting Started](#evaluation) above). Pay attention that for **private** tasks we do not provide golden answers, so no local scoring is provided.
   > You'll end up with a logs folder **and** a ready-to-submit zip archive like `Qwen2.5-0.5B-Instruct_submission.zip`.

2. **Submit on the website**
   Head over to [Create Submission](https://mera.a-ai.ru/ru/multimodal/submits/create), upload the archive, and move on to the form.

3. **Fill in Model Details**
   Provide accurate information about the model and evaluation. These details are crucial for reproducibility—if something is missing, administrators may ping you (or your Submission might be rejected).

4. **Wait for Scoring** ⏳
   Scoring usually wraps up in **~2 hours**.

5. **Publish your result**
   Once scoring finishes, click **"Submit for moderation"**. After approval, your model goes **Public** and appears on the [Leaderboard](https://mera.a-ai.ru/ru/multimodal/leaderboard).

Good luck, and happy benchmarking! 🎉


## 🤝 Contributing

MERA is open for collaboration and adding new datasets! We are expanding MERA to new modalities (video, audio, images) and invite the community to participate in developing new challenging tasks.

### Steps to Add a New Task:
0) Develop a dataset (contributor's side, see [dataset requirements](docs/dataset_review.md))
1) Convert the dataset to MERA format ([guide](docs/dataset_formatting.md))
2) Validate the dataset with automated testing ([guide](docs/dataset_testing.md))
3) Upload the dataset to 🤗HF Hub ([guide](docs/dataset_hf.md))
4) Submit the dataset for review to MERA organizers ([guide](docs/dataset_hf.md))
5) Write evaluation code using lm-harness ([guide](docs/task_codebase.md))
6) Measure human baseline ([guide](docs/human_baseline.md))
7) Benchmark baseline models on the dataset
8) Final moderation — and your dataset is officially added!

### Collaboration Rewards

We offer a [contribution scoring system](docs/collab_bonus.md) for:
- Codebase contributors (features, bugfixes)
- Authors of new datasets for MERA
- Participation in academic paper writing
- Dataset and code review
- Organizational work

Based on collaboration points, participants will be offered co-authorship in an A*/Q1 academic paper on the multimodal part of the MERA project.

Feel free to email any questions & feedback at mera@a-ai.ru.


## 📝 License

Distributed under the MIT License. See LICENSE for details.
