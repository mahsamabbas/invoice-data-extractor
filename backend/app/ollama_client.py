from __future__ import annotations

import base64
import json
from typing import Any

import httpx

from app.config import Settings
from app.prompts import EXTRACT_SYSTEM, EXTRACT_USER, REPAIR_USER


class OllamaError(Exception):
    def __init__(self, kind: str, detail: str):
        self.kind = kind  # "unreachable" | "bad_response"
        self.detail = detail
        super().__init__(detail)


async def ollama_reachable(settings: Settings, client: httpx.AsyncClient | None = None) -> bool:
    owns = client is None
    client = client or httpx.AsyncClient(timeout=5.0)
    try:
        r = await client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
        return r.status_code == 200
    except httpx.HTTPError:
        return False
    finally:
        if owns:
            await client.aclose()


async def chat_vision_json(
    settings: Settings,
    image_bytes: bytes,
    *,
    repair: bool = False,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    owns = client is None
    client = client or httpx.AsyncClient(timeout=settings.ollama_timeout_seconds)
    b64 = base64.b64encode(image_bytes).decode("ascii")
    user_content = REPAIR_USER if repair else EXTRACT_USER
    body = {
        "model": settings.ollama_vision_model,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": user_content, "images": [b64]},
        ],
    }
    try:
        r = await client.post(f"{settings.ollama_base_url.rstrip('/')}/api/chat", json=body)
        r.raise_for_status()
        content = r.json()["message"]["content"]
        if isinstance(content, list):
            # some multimodal replies return segments
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part) for part in content
            )
        return json.loads(content)
    except httpx.HTTPError as e:
        raise OllamaError("unreachable", str(e)) from e
    except (KeyError, TypeError, json.JSONDecodeError) as e:
        raise OllamaError("bad_response", str(e)) from e
    finally:
        if owns:
            await client.aclose()
