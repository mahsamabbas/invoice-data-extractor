from __future__ import annotations

import httpx

from app.config import Settings
from app.flags import apply_flags
from app.ollama_client import OllamaError, chat_vision_json
from app.schemas import InvoiceExtraction


class ExtractError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


async def extract_invoice(
    image_bytes: bytes,
    content_type: str,
    settings: Settings,
    client: httpx.AsyncClient | None = None,
) -> InvoiceExtraction:
    del content_type  # reserved for future mime-aware prompts
    try:
        raw = await chat_vision_json(settings, image_bytes, client=client)
    except OllamaError as e:
        if e.kind == "unreachable":
            raise ExtractError(503, "Vision model unavailable. Is Ollama running?") from e
        # one repair
        try:
            raw = await chat_vision_json(settings, image_bytes, repair=True, client=client)
        except OllamaError as e2:
            code = 503 if e2.kind == "unreachable" else 502
            raise ExtractError(code, "Could not parse invoice JSON from the vision model.") from e2

    try:
        parsed = InvoiceExtraction.model_validate(raw)
    except Exception as e:
        raise ExtractError(502, "Vision model returned invalid invoice fields.") from e
    return apply_flags(parsed)
