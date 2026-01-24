#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

################################################################################
# run_evaluation.sh
#
# A flexible wrapper around lm_eval that splits a comma-separated task list,
# iterates over each, and handles failures without stopping the entire run.
# At the end, packages results for submission and cleans up temporary files.
#
# Usage: ./run_evaluation.sh [options]
#        ./run_evaluation.sh --help    # to show documentation below
################################################################################

# Print usage/help information
usage() {
  cat <<EOF

Usage: $0 [OPTIONS]

Tasks options:
  -t, --tasks TASK1,TASK2,...   Comma-separated list of tasks to evaluate
                                (overrides --modality if specified)
      --modality MOD1,MOD2,...  Modalities to evaluate: image | video | audio
                                Can specify multiple, e.g.: image,video
                                (default: image)
      --load_format FORMAT      Media loading format: base64 | bytes | object | files
                                (default: base64)

Model / runtime options:
  -m, --model ENGINE          lm_eval engine (hf | vllm | local-chat-completions)
  -a, --model_args ARGS       comma-separated key=val pairs for model init
  -g, --gen_kwargs JSON       comma-separated key=val pairs for generation kwargs
  -d, --device DEVICE         cuda | cpu
  -b, --batch_size SIZE       integer or "auto"
  -v, --verbosity LEVEL       DEBUG | INFO | WARNING | ERROR
      --compute_metrics       disable --predict_only (compute metrics instead of bypass)
      --no_log_samples        disable --log_samples (skip logging inputs/outputs)
      --use_cache PATH        enable --use_cache PATH (cache intermediate results)
      --trust_remote_code     pass --trust_remote_code into models or datasets init
      --no_chat_template      disables chat_template usage for model evaluation
      --system_instruction    system instruction text for model
      --no_multimodal_chat    disable passing multimodal args to chat history
  -o, --output_path DIR       directory for logs & results (default: "./results")
  -h, --help                  show this help message and exit

Examples:
  # Image tasks only (default):
  bash scripts/run_evaluation.sh \
    --model_args "pretrained=Qwen/Qwen2-VL-7B-Instruct,dtype=bfloat16" \
    --output_path ./mera_multimodal_results/Qwen2-VL-7B-Instruct

  # Video tasks only:
  bash scripts/run_evaluation.sh \
    --modality video \
    --model_args "pretrained=Qwen/Qwen2-VL-7B-Instruct,dtype=bfloat16" \
    --output_path ./mera_multimodal_results/Qwen2-VL-7B-Instruct

  # Image and video tasks:
  bash scripts/run_evaluation.sh \
    --modality image,video \
    --model_args "pretrained=Qwen/Qwen2-VL-7B-Instruct,dtype=bfloat16" \
    --output_path ./mera_multimodal_results/Qwen2-VL-7B-Instruct

  # All modalities (image, video, audio):
  bash scripts/run_evaluation.sh \
    --modality image,video,audio \
    --model_args "pretrained=Qwen/Qwen2-VL-7B-Instruct,dtype=bfloat16" \
    --output_path ./mera_multimodal_results/Qwen2-VL-7B-Instruct

  # Custom tasks, vllm, two GPUs:
  CUDA_VISIBLE_DEVICES="0,1" bash scripts/run_evaluation.sh \
    --tasks ruclevr,rumathvqa,realvqa \
    --model vllm \
    --model_args "pretrained=Qwen/Qwen2-VL-7B-Instruct,tensor_parallel_size=2" \
    --output_path ./mera_multimodal_results/Qwen2-VL-7B-Instruct

  # All modalities, API, save cache:
  OPENAI_API_KEY="..." bash scripts/run_evaluation.sh \
    --modality image,video,audio \
    --model openai-chat-completions \
    --device cpu \
    --model_args "model=gpt-4o,num_concurrent=8,timeout=90000" \
    --output_path ./mera_multimodal_results/gpt-4o \
    --use_cache ./models_cache/gpt-4o

  # Image tasks, vllm serve:
  bash scripts/run_evaluation.sh \
    --model local-chat-completions \
    --device cpu \
    --model_args "model=Qwen/Qwen2-VL-7B-Instruct,num_concurrent=8,timeout=200,base_url=http://localhost:8888/v1/chat/completions" \
    --output_path ./mera_multimodal_results/Qwen2-VL-7B-Instruct

  # Image tasks, pre-trained (base, no chat template) model:
  bash scripts/run_evaluation.sh \
    --model_args "pretrained=llava-hf/llava-v1.6-mistral-7b-hf,dtype=auto" \
    --output_path ./mera_multimodal_results/llava-v1.6-mistral-7b-hf \
    --no_chat_template

EOF
  exit 1
}

################################################################################
# Task sets by modality
################################################################################

# Image tasks
TASKS_IMAGE=(
  ruclevr
  rucommonvqa
  realvqa
  rumathvqa
  labtabvqa
  ruhhh_image
  weird
  unisciencevqa
  schoolsciencevqa
  runaturalsciencevqa
  rutie_vision
)

# Video tasks
TASKS_VIDEO=(
  realvideoqa
  commonvideoqa
  ruhhh_video
)

# Audio tasks
TASKS_AUDIO=(
  aquaria
  ruenvaqa
  ruslun
  rutie_audio
)

################################################################################
# Configurable parameters with defaults
################################################################################
TASKS=""                     # comma-separated input tasks (overrides MODALITY)
MODALITY="image"             # modalities: image | video | audio (comma-separated)
LOAD_FORMAT="base64"         # media loading format: base64 | bytes | object | files
MODEL="hf"                   # lm_eval engine
MODEL_ARGS=""                # model initialization parameters
GEN_KWARGS=""                # generation kwargs JSON string
DEVICE="cuda"                # default device
BATCH_SIZE=1                 # default batch size
VERBOSITY="ERROR"            # default verbosity level
PREDICT_ONLY=true            # include --predict_only by default
LOG_SAMPLES=true             # include --log_samples by default
USE_CACHE_PATH=""            # path for --use_cache (optional)
OUTPUT_PATH="./results"      # output/ log directory (required)
TRUST_REMOTE_CODE=false      # include --trust_remote_code by default
CHAT_TEMPLATE=true           # include --apply_chat_template and --fewshot_as_multiturn by default
SYSTEM_INSTRUCTION=""        # system instruction text (optional)
MULTIMODAL_CHAT=true         # include --pass_multimodal_args_to_chat_history by default

################################################################################
# Parse command-line arguments
################################################################################
while [[ $# -gt 0 ]]; do
  case "$1" in
    -t|--tasks)              TASKS="$2"; shift 2;;
    --modality)              MODALITY="$2"; shift 2;;
    --load_format)           LOAD_FORMAT="$2"; shift 2;;
    -m|--model)              MODEL="$2"; shift 2;;
    -a|--model_args)         MODEL_ARGS="$2"; shift 2;;
    -g|--gen_kwargs)         GEN_KWARGS="$2"; shift 2;;
    -d|--device)             DEVICE="$2"; shift 2;;
    -b|--batch_size)         BATCH_SIZE="$2"; shift 2;;
    -v|--verbosity)          VERBOSITY="$2"; shift 2;;
    --compute_metrics)       PREDICT_ONLY=false; shift;;
    --no_log_samples)        LOG_SAMPLES=false; shift;;
    --trust_remote_code)     TRUST_REMOTE_CODE=true; shift;;
    --no_chat_template)      CHAT_TEMPLATE=false; shift;;
    --system_instruction)    SYSTEM_INSTRUCTION="$2"; shift 2;;
    --no_multimodal_chat)    MULTIMODAL_CHAT=false; shift;;
    --use_cache)             USE_CACHE_PATH="$2"; shift 2;;
    -o|--output_path)        OUTPUT_PATH="$2"; shift 2;;
    -h|--help)               usage;;
    *) echo "Unknown option: $1" >&2; usage;;
  esac
done

################################################################################
# Build TASK_LIST based on --tasks or --modality
################################################################################
if [[ -n "$TASKS" ]]; then
  # Custom tasks provided via --tasks
  IFS=',' read -r -a TASK_LIST <<< "$TASKS"
else
  # Build task list from modalities
  TASK_LIST=()
  IFS=',' read -r -a MODALITIES <<< "$MODALITY"
  for mod in "${MODALITIES[@]}"; do
    case "$mod" in
      image)  TASK_LIST+=("${TASKS_IMAGE[@]}");;
      video)  TASK_LIST+=("${TASKS_VIDEO[@]}");;
      audio)  TASK_LIST+=("${TASKS_AUDIO[@]}");;
      *)      echo "Unknown modality: $mod (use: image | video | audio)" >&2; exit 1;;
    esac
  done
fi

################################################################################
# Immutable evaluation settings (do not change)
################################################################################
SEED=1234                         # fixed random seed for reproducibility
INCLUDE_PATH="./multimodal_tasks" # path to custom task definitions

################################################################################
# Prepare environment for HuggingFace & CUDA
################################################################################
mkdir -p "$OUTPUT_PATH"
export HF_DATASETS_CACHE="${OUTPUT_PATH}/ds_cache"
export HF_DATASETS_IN_MEMORY_MAX_SIZE=23400000
export TOKENIZERS_PARALLELISM=false
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export PYTHONPATH="$PWD"

# Set media loading format
case "$LOAD_FORMAT" in
  base64)  export LOAD_BASE64=1;;
  bytes)   export LOAD_BYTES=1;;
  object)  export LOAD_OBJECT=1;;
  files)   export LOAD_FILES=1;;
  *)       echo "Unknown load format: $LOAD_FORMAT (use: base64 | bytes | object | files)" >&2; exit 1;;
esac

################################################################################
# Build the common lm_eval flags array
################################################################################
COMMON_FLAGS=(
  --model         "$MODEL"
  --model_args    "$MODEL_ARGS"
  --device        "$DEVICE"
  --batch_size    "$BATCH_SIZE"
  --limit 10
)

$PREDICT_ONLY       && COMMON_FLAGS+=(--predict_only)
$LOG_SAMPLES        && COMMON_FLAGS+=(--log_samples)
$TRUST_REMOTE_CODE  && COMMON_FLAGS+=(--trust_remote_code)
$CHAT_TEMPLATE      && COMMON_FLAGS+=(--apply_chat_template --fewshot_as_multiturn)
$MULTIMODAL_CHAT    && COMMON_FLAGS+=(--pass_multimodal_args_to_chat_history)

COMMON_FLAGS+=(
  --seed          "$SEED"
  --verbosity     "$VERBOSITY"
  --include_path  "$INCLUDE_PATH"
  --output_path   "$OUTPUT_PATH"
)

[[ -n "$GEN_KWARGS"          ]] && COMMON_FLAGS+=(--gen_kwargs "$GEN_KWARGS")
[[ -n "$USE_CACHE_PATH"      ]] && COMMON_FLAGS+=(--use_cache  "$USE_CACHE_PATH")
[[ -n "$SYSTEM_INSTRUCTION"  ]] && COMMON_FLAGS+=(--system_instruction "$SYSTEM_INSTRUCTION")

################################################################################
# Stage 1: Run evaluations over each task, logging failures
################################################################################
echo "-> Evaluating ${#TASK_LIST[@]} task(s): ${TASK_LIST[*]}"
echo "  modality:            $MODALITY"
echo "  load_format:         $LOAD_FORMAT"
echo "  engine:              $MODEL"
echo "  model_args:          $MODEL_ARGS"
echo "  gen_kwargs:          $GEN_KWARGS"
echo "  device:              $DEVICE"
echo "  batch_size:          $BATCH_SIZE"
echo "  predict_only:        $PREDICT_ONLY"
echo "  log_samples:         $LOG_SAMPLES"
echo "  verbosity:           $VERBOSITY"
echo "  include_path:        $INCLUDE_PATH"
echo "  output_path:         $OUTPUT_PATH"
echo "  trust_remote_code:   $TRUST_REMOTE_CODE"
echo "  chat_template:       $CHAT_TEMPLATE"
echo "  multimodal_chat:     $MULTIMODAL_CHAT"
[[ -n "$USE_CACHE_PATH"     ]] && echo "  use_cache:           $USE_CACHE_PATH"
[[ -n "$SYSTEM_INSTRUCTION" ]] && echo "  system_instruction:  $SYSTEM_INSTRUCTION"
echo

FAIL_LOG="$OUTPUT_PATH/failures.log"
: > "$FAIL_LOG"  # clear previous failures

for task in "${TASK_LIST[@]}"; do
  echo "-> Task: $task"
  if ! lm_eval --tasks "$task" "${COMMON_FLAGS[@]}"; then
    code=$?
    ts=$(date +'%Y-%m-%d %H:%M:%S')
    echo "[$ts] Task '$task' failed (exit $code)" >> "$FAIL_LOG"
    echo "  ❌ logged failure"
  else
    echo "  ✅ success"
  fi
done

################################################################################
# Stage 2: Package outputs into submission format
################################################################################
echo "Packaging outputs into submission format..."
HF_DATASETS_CACHE="${OUTPUT_PATH}/ds_cache" \
HF_DATASETS_IN_MEMORY_MAX_SIZE=23400000 \
python scripts/log_to_submission.py \
  --outputs_dir "${OUTPUT_PATH}" \
  --dst_dir "${OUTPUT_PATH}_submission" \
  --model_args "${MODEL_ARGS}"

################################################################################
# Stage 3: Cleanup temporary files and directories
################################################################################
echo "Cleaning up caches and temp folders..."
rm -rf "${OUTPUT_PATH}/ds_cache"

echo "Done. All stages complete."
