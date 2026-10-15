# ClearInvoice (AI Invoice Data Extractor) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build ClearInvoice — upload one synthetic invoice image, extract vendor / invoice number / currency / line items / total via local Ollama vision, validate with Pydantic, and surface honest flags for missing or inconsistent fields without guessing.

**Architecture:** Vue 3 SPA talks only to FastAPI. FastAPI validates the upload, sends the image to host Ollama (`qwen2.5vl`), parses strict JSON into Pydantic models, then appends server-side flags (missing fields, total mismatch). No database. Docker Compose runs frontend + backend; Ollama stays on the host.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, pydantic-settings, httpx, Pillow, pytest · Vue 3, Vite, TypeScript, Tailwind CSS v4, Vitest · Docker Compose · Ollama `qwen2.5vl`

## Global Constraints

- Spec: `docs/superpowers/specs/2026-10-15-invoice-data-extractor-design.md`
- Repo root: `invoice-data-extractor/` (work on `main`, no worktrees)
- Ports: frontend `3006`, API `8006`, Ollama `11434`
- Vision model: `qwen2.5vl` (env `OLLAMA_VISION_MODEL`); `OLLAMA_BASE_URL` default `http://127.0.0.1:11434`
- Upload: `image/png`, `image/jpeg`, `image/webp` only; max **5 MB**
- Total tolerance: `0.01` for `total_mismatch`
- Flag codes exactly: `missing_vendor`, `missing_invoice_number`, `missing_currency`, `missing_total`, `empty_line_items`, `total_mismatch`, `unreadable_image`
- Browser never calls Ollama. No Gemini/OpenAI required. No persistence.
- Tests never hit a live model (httpx mocked / monkeypatch only).
- Brand: **ClearInvoice**. UI direction: modern US fintech ledger — cool slate paper wash, deep teal ink `#0F766E`, warm paper `#F7F4EF`, display **Fraunces**, UI **Source Sans 3**. Forbidden: purple gradients, cream+terracotta serif cliché, Inter/Roboto/Arial, flat white-only, dashboard card grids in the hero.
- Git author: `mahsamabbas <6658043+mahsamabbas@users.noreply.github.com>`; strip Cursor co-author trailers.
- Python venv: `backend/.venv` via `uv` or `python3.12 -m venv`. Node 22.

## File map

| Path | Responsibility |
| --- | --- |
| `.gitignore` | Secrets, venv, node_modules, caches |
| `backend/app/config.py` | Settings |
| `backend/app/schemas.py` | `LineItem`, `Flag`, `InvoiceExtraction`, health models |
| `backend/app/flags.py` | Pure `apply_flags(extraction) -> InvoiceExtraction` |
| `backend/app/ollama_client.py` | Vision chat + JSON repair retry |
| `backend/app/extract.py` | Orchestrate bytes → extraction |
| `backend/app/routes.py` | `/health`, `/sample`, `/extract` |
| `backend/app/main.py` | App factory + CORS |
| `samples/sample_invoice.png` | Bundled synthetic invoice |
| `backend/scripts/generate_sample_invoice.py` | Pillow script that writes the sample |
| `frontend/src/styles.css` | Design tokens + atmosphere |
| `frontend/src/api.ts` | Typed fetch helpers |
| `frontend/src/types.ts` | Mirror API types |
| `frontend/src/components/*` | Dropzone, Preview, Results, Flags, App shell |
| `frontend/src/App.vue` | One-screen composition |
| `docker-compose.yml`, `*/Dockerfile` | One-command run |
| `README.md` | Delivery doc |

---

### Task 1: Repo scaffold + schemas + pure flag logic (TDD)

**Files:**
- Create: `.gitignore`, `backend/requirements.txt`, `backend/requirements-dev.txt`, `backend/pyproject.toml`, `backend/.env.example`
- Create: `backend/app/__init__.py`, `backend/app/config.py`, `backend/app/schemas.py`, `backend/app/flags.py`
- Test: `backend/tests/__init__.py`, `backend/tests/test_flags.py`

**Interfaces:**
- Produces: `Settings`, `get_settings()`; `LineItem`, `Flag`, `InvoiceExtraction`; `apply_flags(data: InvoiceExtraction) -> InvoiceExtraction`; constant `TOTAL_TOLERANCE = 0.01`

- [ ] **Step 1: Write failing flag tests**

```python
# backend/tests/test_flags.py
from app.flags import apply_flags
from app.schemas import InvoiceExtraction, LineItem


def test_complete_invoice_no_flags():
    data = InvoiceExtraction(
        vendor="Northwind Supplies LLC",
        invoice_number="INV-1042",
        currency="USD",
        line_items=[
            LineItem(description="Copy paper", quantity=2, unit_price=12.5, amount=25.0),
            LineItem(description="Toner", quantity=1, unit_price=45.0, amount=45.0),
        ],
        total=70.0,
        flags=[],
    )
    out = apply_flags(data)
    assert out.flags == []


def test_total_mismatch_flag():
    data = InvoiceExtraction(
        vendor="Acme",
        invoice_number="1",
        currency="USD",
        line_items=[LineItem(description="A", quantity=1, unit_price=10.0, amount=10.0)],
        total=99.0,
        flags=[],
    )
    codes = {f.code for f in apply_flags(data).flags}
    assert "total_mismatch" in codes


def test_missing_fields_and_empty_lines():
    data = InvoiceExtraction(
        vendor=None,
        invoice_number="  ",
        currency=None,
        line_items=[],
        total=None,
        flags=[],
    )
    codes = {f.code for f in apply_flags(data).flags}
    assert codes >= {
        "missing_vendor",
        "missing_invoice_number",
        "missing_currency",
        "missing_total",
        "empty_line_items",
    }


def test_amount_derived_from_qty_price_for_sum_only():
    data = InvoiceExtraction(
        vendor="Acme",
        invoice_number="1",
        currency="USD",
        line_items=[LineItem(description="A", quantity=2, unit_price=5.0, amount=None)],
        total=10.0,
        flags=[],
    )
    assert apply_flags(data).flags == []
```

- [ ] **Step 2: Run tests — expect fail**

```bash
cd backend && python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
PYTHONPATH=. pytest tests/test_flags.py -v
```

Expected: FAIL (import / module missing)

- [ ] **Step 3: Create scaffold + implementation**

`.gitignore`:

```gitignore
.DS_Store
.env
backend/.env
backend/.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
frontend/node_modules/
frontend/dist/
frontend/.env.local
*.pyc
```

`backend/requirements.txt`:

```text
fastapi>=0.115
uvicorn[standard]>=0.30
pydantic>=2.7
pydantic-settings>=2.4
httpx>=0.27
python-multipart>=0.0.9
Pillow>=10.0
```

`backend/requirements-dev.txt`:

```text
-r requirements.txt
pytest>=8
pytest-asyncio>=0.24
ruff>=0.6
```

`backend/pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]
```

`backend/.env.example`:

```env
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_VISION_MODEL=qwen2.5vl
OLLAMA_TIMEOUT_SECONDS=120
CORS_ORIGINS=http://localhost:3006
MAX_UPLOAD_BYTES=5242880
```

`backend/app/config.py`:

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_vision_model: str = "qwen2.5vl"
    ollama_timeout_seconds: float = 120.0
    cors_origins: str = "http://localhost:3006"
    max_upload_bytes: int = 5 * 1024 * 1024
    total_tolerance: float = 0.01
    sample_invoice_path: str = ""  # resolved relative to repo in routes


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

`backend/app/schemas.py`:

```python
from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str | None = None
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None


class Flag(BaseModel):
    code: str
    message: str


class InvoiceExtraction(BaseModel):
    vendor: str | None = None
    invoice_number: str | None = None
    currency: str | None = None
    line_items: list[LineItem] = Field(default_factory=list)
    total: float | None = None
    flags: list[Flag] = Field(default_factory=list)
    unreadable: bool = False  # model hint; consumed by apply_flags then stripped from API if desired


class HealthOut(BaseModel):
    status: str
    ollama: bool
    model: str
```

`backend/app/flags.py`:

```python
from app.schemas import Flag, InvoiceExtraction, LineItem

TOTAL_TOLERANCE = 0.01


def _blank(value: str | None) -> bool:
    return value is None or not str(value).strip()


def _line_amount(item: LineItem) -> float | None:
    if item.amount is not None:
        return float(item.amount)
    if item.quantity is not None and item.unit_price is not None:
        return float(item.quantity) * float(item.unit_price)
    return None


def apply_flags(data: InvoiceExtraction) -> InvoiceExtraction:
    flags: list[Flag] = []
    if getattr(data, "unreadable", False):
        flags.append(Flag(code="unreadable_image", message="Image looks blank or unreadable as an invoice."))
    if _blank(data.vendor):
        flags.append(Flag(code="missing_vendor", message="Vendor name was not found."))
    if _blank(data.invoice_number):
        flags.append(Flag(code="missing_invoice_number", message="Invoice number was not found."))
    if _blank(data.currency):
        flags.append(Flag(code="missing_currency", message="Currency was not found."))
    if data.total is None:
        flags.append(Flag(code="missing_total", message="Invoice total was not found."))
    if not data.line_items:
        flags.append(Flag(code="empty_line_items", message="No line items were found."))
    else:
        amounts = [_line_amount(i) for i in data.line_items]
        if data.total is not None and all(a is not None for a in amounts):
            summed = sum(amounts)  # type: ignore[arg-type]
            if abs(summed - float(data.total)) > TOTAL_TOLERANCE:
                flags.append(
                    Flag(
                        code="total_mismatch",
                        message=f"Line items sum to {summed:.2f} but total is {float(data.total):.2f}.",
                    )
                )
    return data.model_copy(update={"flags": flags, "unreadable": False})
```

- [ ] **Step 4: Run tests — expect pass**

```bash
cd backend && source .venv/bin/activate && PYTHONPATH=. pytest tests/test_flags.py -v
```

Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add .gitignore backend/
git -c user.name=mahsamabbas -c user.email=6658043+mahsamabbas@users.noreply.github.com commit -m "$(cat <<'EOF'
feat: add ClearInvoice schemas and flag validation

EOF
)"
```

---

### Task 2: Ollama vision client + extract orchestration (mocked TDD)

**Files:**
- Create: `backend/app/ollama_client.py`, `backend/app/extract.py`, `backend/app/prompts.py`
- Test: `backend/tests/test_extract.py`

**Interfaces:**
- Consumes: `Settings`, `InvoiceExtraction`, `apply_flags`
- Produces: `async def extract_invoice(image_bytes: bytes, content_type: str, settings: Settings, client: httpx.AsyncClient | None = None) -> InvoiceExtraction`
- Produces: `async def ollama_reachable(settings, client=None) -> bool`
- Raises: `ExtractError(status_code: int, detail: str)` for 502/503 mapping

- [ ] **Step 1: Write failing extract tests**

```python
# backend/tests/test_extract.py
import json
import pytest
import httpx
from app.config import Settings
from app.extract import ExtractError, extract_invoice


def _mock_transport(handler):
    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_extract_happy_path():
    payload = {
        "message": {
            "content": json.dumps(
                {
                    "vendor": "Northwind Supplies LLC",
                    "invoice_number": "INV-1042",
                    "currency": "USD",
                    "line_items": [
                        {
                            "description": "Copy paper",
                            "quantity": 2,
                            "unit_price": 12.5,
                            "amount": 25.0,
                        }
                    ],
                    "total": 25.0,
                    "unreadable": False,
                }
            )
        }
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/api/chat")
        return httpx.Response(200, json=payload)

    settings = Settings(ollama_base_url="http://ollama.test")
    async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
        out = await extract_invoice(b"fake-png", "image/png", settings, client=client)
    assert out.vendor == "Northwind Supplies LLC"
    assert out.flags == []


@pytest.mark.asyncio
async def test_extract_ollama_down_is_503():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    settings = Settings(ollama_base_url="http://ollama.test")
    async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
        with pytest.raises(ExtractError) as exc:
            await extract_invoice(b"x", "image/png", settings, client=client)
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_extract_bad_json_after_repair_is_502():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, json={"message": {"content": "NOT JSON {"}})

    settings = Settings(ollama_base_url="http://ollama.test")
    async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
        with pytest.raises(ExtractError) as exc:
            await extract_invoice(b"x", "image/png", settings, client=client)
    assert exc.value.status_code == 502
    assert calls["n"] == 2  # initial + one repair
```

- [ ] **Step 2: Run — expect fail**

```bash
PYTHONPATH=. pytest tests/test_extract.py -v
```

Expected: FAIL (modules missing)

- [ ] **Step 3: Implement client + extract**

`backend/app/prompts.py`:

```python
EXTRACT_SYSTEM = """You extract fields from a single invoice image.
Return ONLY a JSON object with keys:
vendor, invoice_number, currency, line_items, total, unreadable.
line_items is an array of {description, quantity, unit_price, amount}.
Use null for any field you cannot read. Never invent values.
If the image is blank or not an invoice, set unreadable=true and null out fields.
currency should be a 3-letter code when possible (USD, EUR, PKR).
"""

EXTRACT_USER = "Extract the invoice fields as JSON."

REPAIR_USER = (
    "Your previous reply was not valid JSON. Reply again with ONLY the JSON object, no markdown."
)
```

`backend/app/ollama_client.py`:

```python
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
```

`backend/app/extract.py`:

```python
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
```

- [ ] **Step 4: Run — expect pass**

```bash
PYTHONPATH=. pytest tests/test_extract.py tests/test_flags.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/prompts.py backend/app/ollama_client.py backend/app/extract.py backend/tests/test_extract.py
git -c user.name=mahsamabbas -c user.email=6658043+mahsamabbas@users.noreply.github.com commit -m "$(cat <<'EOF'
feat: add Ollama vision extract path with mocked tests

EOF
)"
```

---

### Task 3: Sample invoice asset + HTTP routes + API tests

**Files:**
- Create: `backend/scripts/generate_sample_invoice.py`, `samples/sample_invoice.png`, `backend/app/routes.py`, `backend/app/main.py`
- Test: `backend/tests/test_api.py`

**Interfaces:**
- Produces: `create_app() -> FastAPI` with routes `GET /health`, `GET /sample`, `POST /extract`
- Sample path: repo-relative `samples/sample_invoice.png`

- [ ] **Step 1: Generate synthetic US-style invoice PNG**

`backend/scripts/generate_sample_invoice.py`:

```python
"""Write samples/sample_invoice.png — synthetic US invoice for demos."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "samples" / "sample_invoice.png"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (800, 1000), "#FFFFFF")
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    lines = [
        "NORTHWIND SUPPLIES LLC",
        "1847 Market Street, Suite 200",
        "San Francisco, CA 94103",
        "",
        "INVOICE",
        "Invoice #: INV-1042",
        "Date: October 1, 2026",
        "Bill To: BrightMart Commerce Studio",
        "",
        "Description              Qty    Unit     Amount",
        "------------------------------------------------",
        "A4 Copy Paper (case)       2    12.50     25.00",
        "Black Toner Cartridge      1    45.00     45.00",
        "Shipping                   1     8.00      8.00",
        "",
        "Subtotal                                    78.00",
        "Tax (0%)                                     0.00",
        "TOTAL USD                                   78.00",
        "",
        "Payment due within 30 days.",
    ]
    y = 40
    for line in lines:
        d.text((48, y), line, fill="#111111", font=font)
        y += 28
    img.save(OUT, "PNG")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
```

Run:

```bash
cd backend && source .venv/bin/activate && python scripts/generate_sample_invoice.py
```

Expected: `samples/sample_invoice.png` exists

- [ ] **Step 2: Write failing API tests**

```python
# backend/tests/test_api.py
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas import InvoiceExtraction, LineItem


@pytest.fixture
def client(tmp_path, monkeypatch):
    sample = Path(__file__).resolve().parents[2] / "samples" / "sample_invoice.png"
    assert sample.exists()
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_health(client):
    with patch("app.routes.ollama_reachable", new=AsyncMock(return_value=True)):
        r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_sample(client):
    r = client.get("/sample")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")
    assert len(r.content) > 100


def test_extract_requires_file(client):
    r = client.post("/extract")
    assert r.status_code == 400


def test_extract_success(client):
    fake = InvoiceExtraction(
        vendor="Northwind Supplies LLC",
        invoice_number="INV-1042",
        currency="USD",
        line_items=[LineItem(description="A", quantity=1, unit_price=1.0, amount=1.0)],
        total=1.0,
        flags=[],
    )
    with patch("app.routes.extract_invoice", new=AsyncMock(return_value=fake)):
        files = {"file": ("inv.png", b"fakepng", "image/png")}
        r = client.post("/extract", files=files)
    assert r.status_code == 200
    assert r.json()["vendor"] == "Northwind Supplies LLC"


def test_extract_rejects_pdf(client):
    files = {"file": ("inv.pdf", b"%PDF", "application/pdf")}
    r = client.post("/extract", files=files)
    assert r.status_code == 400
```

- [ ] **Step 3: Implement routes + main**

`backend/app/routes.py`:

```python
from pathlib import Path

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from app.config import Settings, get_settings
from app.extract import ExtractError, extract_invoice
from app.ollama_client import ollama_reachable
from app.schemas import HealthOut

router = APIRouter()

ALLOWED = {"image/png", "image/jpeg", "image/webp", "image/jpg"}


def _sample_path() -> Path:
    # backend/app/routes.py → parents[2] = repo root
    return Path(__file__).resolve().parents[2] / "samples" / "sample_invoice.png"


@router.get("/health", response_model=HealthOut)
async def health(settings: Settings = None):
    settings = settings or get_settings()
    ok = await ollama_reachable(settings)
    return HealthOut(status="ok" if ok else "degraded", ollama=ok, model=settings.ollama_vision_model)


@router.get("/sample")
async def sample():
    path = _sample_path()
    if not path.exists():
        return JSONResponse({"detail": "Sample invoice missing"}, status_code=404)
    return Response(content=path.read_bytes(), media_type="image/png")


@router.post("/extract")
async def extract(file: UploadFile | None = File(default=None)):
    settings = get_settings()
    if file is None or not file.filename:
        return JSONResponse({"detail": "Upload an invoice image file."}, status_code=400)
    content_type = (file.content_type or "").lower()
    if content_type == "image/jpg":
        content_type = "image/jpeg"
    if content_type not in ALLOWED:
        return JSONResponse(
            {"detail": "Only PNG, JPEG, or WebP images are accepted."},
            status_code=400,
        )
    data = await file.read()
    if not data:
        return JSONResponse({"detail": "File is empty."}, status_code=400)
    if len(data) > settings.max_upload_bytes:
        return JSONResponse({"detail": "File exceeds 5 MB limit."}, status_code=400)
    try:
        result = await extract_invoice(data, content_type, settings)
    except ExtractError as e:
        return JSONResponse({"detail": e.detail}, status_code=e.status_code)
    return result
```

`backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="ClearInvoice", version="0.1.0")
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["http://localhost:3006"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
```

Fix `health` signature to avoid `settings: Settings = None` antipattern — use `Depends` if needed; for simplicity call `get_settings()` inside as shown in extract.

- [ ] **Step 4: Run API tests**

```bash
PYTHONPATH=. pytest tests/ -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add samples/ backend/app/routes.py backend/app/main.py backend/scripts/ backend/tests/test_api.py
git -c user.name=mahsamabbas -c user.email=6658043+mahsamabbas@users.noreply.github.com commit -m "$(cat <<'EOF'
feat: add ClearInvoice API routes and sample invoice

EOF
)"
```

---

### Task 4: Vue scaffold + ClearInvoice design system (unique modern UI)

**Files:**
- Create: `frontend/` via `npm create vite@latest` (vue-ts), then Tailwind v4
- Create: `frontend/src/styles.css`, `frontend/index.html`, `frontend/src/App.vue` shell, `frontend/.env.example`
- No heavy tests yet — visual shell must load on `:3006`

**UI direction (non-negotiable):**

| Token | Value |
| --- | --- |
| Brand | **ClearInvoice** wordmark as hero (not a tiny nav logo) |
| Display font | Fraunces (Google Fonts) |
| UI font | Source Sans 3 |
| Ink | `#0F766E` (teal) |
| Paper | `#F7F4EF` |
| Slate wash | radial + subtle ledger grid background |
| Accent warn | `#B45309` amber for flags |
| Forbidden | purple glow, Inter, cream+terracotta broadsheet, card-grid hero |

Layout: **one composition** — left: document stage (dropzone + preview); right: extraction readout. Mobile: stack preview then results.

- [ ] **Step 1: Scaffold Vue + Tailwind**

```bash
cd /Users/azc/Desktop/azc/mahsamabbas_repos/invoice-data-extractor
npm create vite@latest frontend -- --template vue-ts
cd frontend && npm install && npm install -D tailwindcss @tailwindcss/vite
```

`frontend/vite.config.ts`:

```ts
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: { port: 3006, strictPort: true },
});
```

`frontend/.env.example`:

```env
VITE_API_BASE=http://localhost:8006
```

`frontend/index.html` — load fonts:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>ClearInvoice</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Source+Sans+3:wght@400;500;600;700&display=swap"
      rel="stylesheet"
    />
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

`frontend/src/styles.css`:

```css
@import "tailwindcss";

@theme {
  --font-display: "Fraunces", ui-serif, Georgia, serif;
  --font-sans: "Source Sans 3", ui-sans-serif, system-ui, sans-serif;
  --color-ink: #0f766e;
  --color-ink-deep: #115e59;
  --color-paper: #f7f4ef;
  --color-slate: #1e293b;
  --color-warn: #b45309;
  --color-warn-soft: #fff7ed;
  --color-line: #d6d3d1;
}

html,
body,
#app {
  height: 100%;
  margin: 0;
}

body {
  font-family: var(--font-sans);
  color: var(--color-slate);
  background:
    radial-gradient(1200px 600px at 10% -10%, rgba(15, 118, 110, 0.12), transparent 60%),
    radial-gradient(900px 500px at 100% 0%, rgba(30, 41, 59, 0.08), transparent 55%),
    linear-gradient(180deg, #eef2f0 0%, var(--color-paper) 45%, #ebe6df 100%);
  background-attachment: fixed;
}

body::before {
  content: "";
  pointer-events: none;
  position: fixed;
  inset: 0;
  opacity: 0.35;
  background-image:
    linear-gradient(rgba(30, 41, 59, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(30, 41, 59, 0.04) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: radial-gradient(ellipse at center, black 40%, transparent 80%);
}

.brand {
  font-family: var(--font-display);
  letter-spacing: -0.03em;
}

@keyframes drop-pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.01); }
  100% { transform: scale(1); }
}
.drop-accepted {
  animation: drop-pulse 420ms ease;
  box-shadow: 0 0 0 2px var(--color-ink);
}

@keyframes flag-in {
  from { opacity: 0; transform: translateY(-6px); }
  to { opacity: 1; transform: translateY(0); }
}
.flag-enter {
  animation: flag-in 320ms ease-out;
}

@keyframes extract-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.72; }
}
.extracting {
  animation: extract-pulse 1.1s ease-in-out infinite;
}
```

`frontend/src/App.vue` shell (placeholder regions):

```vue
<script setup lang="ts">
</script>

<template>
  <div class="min-h-full px-5 py-8 md:px-10 md:py-10">
    <header class="mx-auto max-w-6xl mb-10">
      <p class="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--color-ink)]">
        Local vision · no cloud key
      </p>
      <h1 class="brand mt-2 text-5xl md:text-6xl text-[var(--color-ink-deep)]">
        ClearInvoice
      </h1>
      <p class="mt-3 max-w-xl text-lg text-slate-600">
        Drop a synthetic invoice. We read the fields, validate the math, and flag anything unclear —
        we never invent numbers.
      </p>
    </header>

    <main class="mx-auto grid max-w-6xl gap-8 lg:grid-cols-2 lg:gap-10">
      <section class="rounded-sm border border-[var(--color-line)] bg-white/70 p-5 backdrop-blur-sm">
        <!-- Task 5: Dropzone + preview -->
        <p class="text-slate-500">Document stage coming next</p>
      </section>
      <section class="rounded-sm border border-[var(--color-line)] bg-white/70 p-5 backdrop-blur-sm">
        <!-- Task 5: Results -->
        <p class="text-slate-500">Extraction readout coming next</p>
      </section>
    </main>
  </div>
</template>
```

Wire `main.ts` to import `./styles.css`.

- [ ] **Step 2: Smoke run**

```bash
cd frontend && cp .env.example .env.local && npm run dev
```

Expected: http://localhost:3006 shows ClearInvoice brand + two-pane shell with ledger atmosphere

- [ ] **Step 3: Commit**

```bash
git add frontend/
git -c user.name=mahsamabbas -c user.email=6658043+mahsamabbas@users.noreply.github.com commit -m "$(cat <<'EOF'
feat: scaffold ClearInvoice Vue UI with ledger design system

EOF
)"
```

---

### Task 5: Upload, extract API client, results + flags UI

**Files:**
- Create: `frontend/src/types.ts`, `frontend/src/api.ts`, `frontend/src/lib/format.ts`
- Create: `frontend/src/components/DocumentStage.vue`, `frontend/src/components/ExtractionPanel.vue`, `frontend/src/components/FlagStrip.vue`
- Modify: `frontend/src/App.vue`
- Test: `frontend/src/lib/format.test.ts` (Vitest)

**Interfaces:**
- `extractInvoice(file: File): Promise<InvoiceExtraction>`
- `fetchSampleBlob(): Promise<Blob>`
- `formatMoney(currency: string | null, amount: number | null): string`

- [ ] **Step 1: Types + API + format helper + Vitest**

```ts
// frontend/src/types.ts
export interface LineItem {
  description: string | null;
  quantity: number | null;
  unit_price: number | null;
  amount: number | null;
}

export interface Flag {
  code: string;
  message: string;
}

export interface InvoiceExtraction {
  vendor: string | null;
  invoice_number: string | null;
  currency: string | null;
  line_items: LineItem[];
  total: number | null;
  flags: Flag[];
}
```

```ts
// frontend/src/api.ts
import type { InvoiceExtraction } from "./types";

const base = import.meta.env.VITE_API_BASE ?? "http://localhost:8006";

export async function fetchSampleBlob(): Promise<Blob> {
  const r = await fetch(`${base}/sample`);
  if (!r.ok) throw new Error("Could not load sample invoice");
  return r.blob();
}

export async function extractInvoice(file: File): Promise<InvoiceExtraction> {
  const body = new FormData();
  body.append("file", file);
  const r = await fetch(`${base}/extract`, { method: "POST", body });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail ?? `Extract failed (${r.status})`);
  return data as InvoiceExtraction;
}
```

```ts
// frontend/src/lib/format.ts
export function formatMoney(currency: string | null, amount: number | null): string {
  if (amount === null || amount === undefined) return "—";
  const code = currency && currency.length === 3 ? currency : "USD";
  try {
    return new Intl.NumberFormat("en-US", { style: "currency", currency: code }).format(amount);
  } catch {
    return `${amount.toFixed(2)} ${currency ?? ""}`.trim();
  }
}
```

```ts
// frontend/src/lib/format.test.ts
import { describe, expect, it } from "vitest";
import { formatMoney } from "./format";

describe("formatMoney", () => {
  it("formats USD", () => {
    expect(formatMoney("USD", 78)).toMatch(/\$78/);
  });
  it("shows em dash for null", () => {
    expect(formatMoney("USD", null)).toBe("—");
  });
});
```

Add vitest:

```bash
cd frontend && npm install -D vitest && npx vitest run
```

- [ ] **Step 2: Build DocumentStage + ExtractionPanel + FlagStrip**

`DocumentStage.vue` responsibilities:
- Drag/drop + file input (png/jpeg/webp)
- “Use sample invoice” button → `fetchSampleBlob` → File named `sample_invoice.png`
- Image preview (`URL.createObjectURL`)
- Apply `.drop-accepted` class briefly on successful drop
- Emit `file-ready(File | null)`

`FlagStrip.vue`:
- Props: `flags: Flag[]`
- If empty, render nothing
- Else amber strip with `.flag-enter`, list messages

`ExtractionPanel.vue`:
- Props: `result: InvoiceExtraction | null`, `loading: boolean`, `error: string | null`
- Loading: skeleton rows + `.extracting` on header
- Fields: Vendor, Invoice #, Currency, Total (use `formatMoney`)
- Table of line items
- `<FlagStrip />`
- Toggle “View JSON” `<pre>`

`App.vue` wires:
- state: file, previewUrl, result, loading, error
- Extract CTA disabled without file or while loading
- On Extract → `extractInvoice(file)`

Motion checklist: drop pulse, extract pulse, flag slide-in — all three present.

- [ ] **Step 3: Manual smoke with mocked backend optional**

With backend up (Ollama optional for UI-only; extract needs mock or live):

```bash
# terminal A
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8006
# terminal B
cd frontend && npm run dev
```

Happy path: Use sample → Extract → fields + possible flags.

- [ ] **Step 4: Commit**

```bash
git add frontend/
git -c user.name=mahsamabbas -c user.email=6658043+mahsamabbas@users.noreply.github.com commit -m "$(cat <<'EOF'
feat: wire ClearInvoice upload, extract, and results UI

EOF
)"
```

---

### Task 6: Docker Compose + README + final polish

**Files:**
- Create: `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `frontend/nginx.conf`, `README.md`, root `.env.example`
- Modify: UI microcopy / empty states if needed

- [ ] **Step 1: Docker files**

`backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY samples /samples
ENV SAMPLE_INVOICE_PATH=/samples/sample_invoice.png
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]
```

Update `_sample_path()` to honor `SAMPLE_INVOICE_PATH` env if set (small config addition).

`frontend/Dockerfile` — multi-stage Vite build + nginx on port 80; compose maps `3006:80`.

`frontend/nginx.conf` — SPA fallback + optional `/api` proxy not required (browser calls `VITE_API_BASE` baked at build).

`docker-compose.yml`:

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8006:8006"
    environment:
      OLLAMA_BASE_URL: http://host.docker.internal:11434
      OLLAMA_VISION_MODEL: qwen2.5vl
      CORS_ORIGINS: http://localhost:3006
      SAMPLE_INVOICE_PATH: /samples/sample_invoice.png
    extra_hosts:
      - "host.docker.internal:host-gateway"
  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
      args:
        VITE_API_BASE: http://localhost:8006
    ports:
      - "3006:80"
    depends_on:
      - backend
```

- [ ] **Step 2: README**

Include: ClearInvoice description, stack table (Vue 3, FastAPI, Ollama `qwen2.5vl`, Pydantic), API table, env vars, Docker + local run, tests, limitations (local VLM quality, no persistence), link to design/plan specs.

- [ ] **Step 3: Verify**

```bash
ollama pull qwen2.5vl
cd backend && PYTHONPATH=. pytest -v
cd frontend && npx vitest run
docker compose up --build
```

Expected: UI on `:3006`, health on `:8006/health`, sample extract works when Ollama is up.

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml backend/Dockerfile frontend/Dockerfile frontend/nginx.conf README.md .env.example backend/app/
git -c user.name=mahsamabbas -c user.email=6658043+mahsamabbas@users.noreply.github.com commit -m "$(cat <<'EOF'
chore: add Docker Compose, README, and delivery polish

EOF
)"
```

---

## Spec coverage checklist

| Spec requirement | Task |
| --- | --- |
| Vue 3 + FastAPI + Ollama vision | 2, 4, 5 |
| Extract vendor, number, currency, lines, total | 2, 3, 5 |
| Flag missing / inconsistent; no guessing | 1, 2 |
| `total_mismatch` tolerance 0.01 | 1 |
| `/health`, `/sample`, `/extract` | 3 |
| 400 / 502 / 503 mapping | 2, 3 |
| Sample synthetic invoice | 3 |
| Ports 3006 / 8006 | 4, 6 |
| Unique ClearInvoice UI + motions | 4, 5 |
| pytest normal + failure | 1, 2, 3 |
| Docker + README + `.env.example` | 6 |
| No DB / no cloud key required | all |

## Self-review notes

- No TBD/TODO placeholders left in steps.
- `apply_flags` / `extract_invoice` / route names consistent across tasks.
- Docker sample path uses `SAMPLE_INVOICE_PATH` — implement that env read in Task 6 when adjusting `_sample_path`.
- Ollama tag `qwen2.5vl` matches current Ollama library naming; override via env if local tag differs (`qwen2.5-vl`).
