from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import gc

import torch

from models import MODELS_REGISTRY

app = FastAPI(title="Minimal Chat Completions Server", version="0.0.1")

LAST_USED_MODEL = None
LAST_USED_MODEL_PARAMS = None


@app.post("/v1/chat/completions")
async def chat_completions(req: Request):
    global LAST_USED_MODEL, LAST_USED_MODEL_PARAMS
    body = await req.json()

    params = {
        "model_name": body["model"],
        "max_new_tokens": body["max_completion_tokens"],
    }

    if LAST_USED_MODEL_PARAMS != params:
        if LAST_USED_MODEL:
            LAST_USED_MODEL = None

            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()

        LAST_USED_MODEL = MODELS_REGISTRY[params["model_name"]](**params)
        LAST_USED_MODEL_PARAMS = params

    messages = body["messages"]
    result = LAST_USED_MODEL.generate(messages)

    json_result = {
        "choices": [
            {
                "message": {
                    "content": result,
                },
                "index": 0,
            }
        ]
    }

    return JSONResponse(json_result)


@app.get("/v1/models")
async def list_models():
    return {"models": [{"id": k} for k in MODELS_REGISTRY.keys()]}
