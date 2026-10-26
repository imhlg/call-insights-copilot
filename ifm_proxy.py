"""Tiny local proxy between Cline and the IFM API.

Why: IFM's K2 Horizon is strict about the request format:
  1. Message content must be plain text. Tools like Kilo Code send it as a
     list of parts, which IFM rejects ("Invalid value for 'messages.content'").
  2. Every assistant message in the history needs a `reasoning_content`
     field. Cline drops it, so turn 2 onward fails.
This proxy fixes both, then forwards the request to IFM (streaming included).
Works with Cline, Kilo Code, Roo Code or any OpenAI-compatible tool.

Setup (inside your venv):
    pip install fastapi uvicorn httpx

Run:
    uvicorn ifm_proxy:app --port 8787

In Cline, change only the Base URL to:
    http://localhost:8787/v1
Keep your IFM API key and Model ID as they are.
"""

import os

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse

# Use the same base URL you had in Cline (without a trailing slash).
IFM_BASE_URL = os.environ.get("IFM_BASE_URL", "https://api.ifm.ai/v1")

app = FastAPI()
client = httpx.AsyncClient(timeout=None)


def _forward_headers(request: Request) -> dict:
    # Strip stray whitespace (e.g. "Bearer " with a missing token is an illegal
    # header value for httpx/httpcore and crashes the upstream send with a 500).
    headers = {"Content-Type": "application/json"}
    auth = request.headers.get("authorization", "").strip()
    if auth:
        headers["Authorization"] = auth
    return headers


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()

    for message in body.get("messages", []):
        # Fix 1: IFM only accepts plain-text content. Some tools send content
        # as a list of parts ([{"type": "text", "text": "..."}]); join them.
        content = message.get("content")
        if isinstance(content, list):
            message["content"] = "\n".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            )
        elif content is None and message.get("role") != "assistant":
            message["content"] = ""

        # Fix 2: every assistant message must carry reasoning_content.
        if message.get("role") == "assistant":
            message.setdefault("reasoning_content", "")
            if message.get("content") is None and not message.get("tool_calls"):
                message["content"] = ""

    upstream = client.build_request(
        "POST",
        f"{IFM_BASE_URL}/chat/completions",
        json=body,
        headers=_forward_headers(request),
    )
    resp = await client.send(upstream, stream=True)
    content_type = resp.headers.get("content-type", "application/json")

    if body.get("stream"):
        async def stream_back():
            try:
                async for chunk in resp.aiter_raw():
                    yield chunk
            finally:
                await resp.aclose()

        return StreamingResponse(
            stream_back(), status_code=resp.status_code, media_type=content_type
        )

    data = await resp.aread()
    await resp.aclose()
    return Response(content=data, status_code=resp.status_code, media_type=content_type)


@app.get("/v1/models")
async def list_models(request: Request):
    resp = await client.get(f"{IFM_BASE_URL}/models", headers=_forward_headers(request))
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
    )
