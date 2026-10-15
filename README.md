# ClearInvoice

ClearInvoice turns an invoice image (PNG, JPEG, or WebP) into structured data: vendor, invoice number, currency, line items, and total. It never guesses. Missing or inconsistent fields (for example, line items that don't add up to the total) are **flagged** instead of filled in. Vision runs locally through Ollama, so no cloud API key is needed and nothing is stored.

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | Vue 3, Vite, Tailwind CSS 4 (port 3006) |
| Backend | FastAPI, Uvicorn (port 8006) |
| Vision model | Ollama, `qwen2.5vl` (override with `OLLAMA_VISION_MODEL`) |
| Validation | Pydantic v2 schemas + flag rules (`total_mismatch` tolerance 0.01) |

## API

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | `{status, ollama, model}`; `degraded` when Ollama is unreachable |
| GET | `/sample` | Bundled synthetic sample invoice (PNG) |
| POST | `/extract` | Multipart `file` upload; returns extraction + `flags` |

`/extract` errors: `400` bad/empty/oversized/unsupported upload, `502` invalid model output, `503` Ollama unavailable.

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama endpoint (`http://host.docker.internal:11434` in Docker) |
| `OLLAMA_VISION_MODEL` | `qwen2.5vl` | Vision model tag |
| `OLLAMA_TIMEOUT_SECONDS` | `120` | Model request timeout |
| `CORS_ORIGINS` | `http://localhost:3006` | Comma-separated allowed origins |
| `MAX_UPLOAD_BYTES` | `5242880` | Upload limit (5 MB) |
| `SAMPLE_INVOICE_PATH` | repo `samples/sample_invoice.png` | Override sample file location |
| `VITE_API_BASE` | `http://localhost:8006` | Backend URL for the frontend (build-time) |

See [`.env.example`](.env.example).

## Run with Docker

```bash
ollama pull qwen2.5vl      # on the host; Ollama must be running
docker compose up --build
```

- UI: http://localhost:3006
- Health: http://localhost:8006/health

The backend reaches the host's Ollama via `host.docker.internal`.

## Run locally

```bash
ollama pull qwen2.5vl

# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --port 8006 --reload

# frontend (new terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev -- --port 3006
```

## Tests

```bash
cd backend && PYTHONPATH=. pytest -v   # Ollama is mocked
cd frontend && npx vitest run
```

## Limitations

- Accuracy depends on the local vision model; small or noisy scans may extract poorly. Flags surface gaps rather than hide them.
- No persistence: no database, no history; each upload is processed in memory.
- Single-image invoices only (no multi-page PDFs); 5 MB limit.
- First request after starting Ollama can be slow while the model loads.

## Design and plan

- [Design spec](docs/superpowers/specs/2026-10-15-invoice-data-extractor-design.md)
- [Implementation plan](docs/superpowers/plans/2026-10-15-invoice-data-extractor.md)
