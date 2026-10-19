# ClearInvoice — AI Invoice Data Extractor

Upload one invoice **image** (PNG, JPEG, or WebP). A local vision model reads the fields; Pydantic validates them; the UI shows every field plus honest **flags** when something is missing or the math does not add up. The app never invents vendor names, totals, or line items.

Demo / portfolio use — not an accounting system, OCR SaaS, or multi-page PDF pipeline.

**Flow:** Browser upload → FastAPI → Ollama vision (`qwen2.5vl`) returns JSON → Pydantic coerce + `apply_flags` → Vue field sheet. Optional: fullscreen image preview, **Download PDF** (regenerated invoice), **Download Excel**.

## What’s included

- Sample synthetic invoice + custom image upload (5 MB max)
- Extraction of vendor, invoice number, currency, line items, **subtotal**, **tax**, and total
- Server-side consistency checks (line sum, line sum + tax, or subtotal + tax ≈ total)
- Flag codes instead of guessing (`missing_*`, `total_mismatch`, `unreadable_image`, …)
- Full-screen lightbox for the source image (Esc / click outside to close)
- Client-side **PDF** invoice (modern aligned template, ASCII-safe currency e.g. `INR 7,226.00`)
- Client-side **Excel** workbook (Summary / Line items / Flags sheets)
- Docker Compose one-command run; browser never calls Ollama

## Concept

ClearInvoice is a **vision → structured JSON → validate → flag** demo:

1. **Grounding:** The model is prompted to use `null` when a field is unreadable — no invented numbers.
2. **Lenient parse:** Strings like `"$50.00"` or `"unreadable": null` are coerced so the API does not 502 on common model quirks.
3. **Math flags:** Tax invoices often have `lines ≠ total`. Reconciliation accepts `lines + tax` or `subtotal + tax` within a `0.01` tolerance.
4. **Human in the loop:** Flags and optional PDF/Excel exports are for review — not auto-posting to a ledger.

## Tech stack

| Layer | Choices |
| --- | --- |
| Frontend | **Vue 3**, TypeScript, **Vite 6** |
| Styling | **Tailwind CSS v4** (`@tailwindcss/vite`), Fraunces + Source Sans 3, ledger/teal ClearInvoice UI |
| PDF export | `jspdf` + `jspdf-autotable` (browser-side regenerated invoice) |
| Excel export | `xlsx` (SheetJS) — Summary / Line items / Flags |
| Backend | Python 3.12, **FastAPI**, Uvicorn |
| Validation | **Pydantic v2** + `pydantic-settings` |
| Vision LLM | Local [Ollama](https://ollama.com) multimodal — default **`qwen2.5vl`** |
| HTTP client | `httpx` (Ollama `/api/chat` with base64 image) |
| Uploads | `python-multipart` |
| Sample asset | **Pillow** script generates `samples/sample_invoice.png` |
| Delivery | Docker Compose (nginx frontend + FastAPI backend; Ollama on host) |
| Tests | Backend: `pytest` (Ollama mocked). Frontend: Vitest |

### Libraries & smaller pieces

**Backend**

- `fastapi` / `uvicorn[standard]` — `/health`, `/sample`, `/extract`
- `pydantic` / `pydantic-settings` — `LineItem`, `InvoiceExtraction`, env config
- `httpx` — Ollama chat + vision; MockTransport in tests
- `python-multipart` — multipart image upload
- `Pillow` — synthetic sample invoice generator
- `app/flags.py` — pure flag rules (`TOTAL_TOLERANCE = 0.01`)
- `app/ollama_client.py` — vision JSON + one repair retry
- `app/extract.py` — orchestrate bytes → validated extraction

**Frontend**

- `vue` / `vite` / `typescript` — ClearInvoice SPA
- `tailwindcss` — field-sheet layout, motions (drop / extract / flags)
- `jspdf` / `jspdf-autotable` — modern PDF template (header band, cards, aligned totals)
- `xlsx` — Excel download
- `ImageLightbox.vue` — Teleport fullscreen preview
- Vitest — `formatMoney`, `formatMoneyPlain`, export basename helpers

**API surface (browser → FastAPI only)**

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness; `{ status, ollama, model }` (`degraded` if Ollama down) |
| `GET` | `/sample` | Bundled sample invoice PNG |
| `POST` | `/extract` | Multipart `file` → extraction JSON + `flags` |

The browser never calls Ollama. PDF and Excel are generated entirely in the browser from the extraction payload.

### Flag codes

| Code | When |
| --- | --- |
| `missing_vendor` | Vendor blank / null |
| `missing_invoice_number` | Invoice number blank / null |
| `missing_currency` | Currency blank / null |
| `missing_total` | Total null |
| `empty_line_items` | No line items |
| `total_mismatch` | Lines (and tax/subtotal if present) do not reconcile with total |
| `unreadable_image` | Model marked the image unreadable |

## Ports

| Service | URL |
| --- | --- |
| Frontend | http://localhost:3006 |
| API | http://localhost:8006 |
| Ollama | http://localhost:11434 |

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama endpoint (`http://host.docker.internal:11434` in Docker) |
| `OLLAMA_VISION_MODEL` | `qwen2.5vl` | Vision model tag |
| `OLLAMA_TIMEOUT_SECONDS` | `120` | Model request timeout |
| `CORS_ORIGINS` | `http://localhost:3006` | Comma-separated allowed origins |
| `MAX_UPLOAD_BYTES` | `5242880` | Upload limit (5 MB) |
| `SAMPLE_INVOICE_PATH` | repo `samples/sample_invoice.png` | Override sample path (Docker uses `/samples/...`) |
| `VITE_API_BASE` | `http://localhost:8006` | Backend URL baked into the frontend at build time |

See [`.env.example`](.env.example).

## 1. Install Ollama and pull the vision model

```bash
ollama serve          # if not already running
ollama pull qwen2.5vl
```

Chat-only models like `qwen2.5:7b` are **not** enough — ClearInvoice needs a multimodal tag.

## 2a. Run with Docker

```bash
docker compose up --build
```

- UI: http://localhost:3006  
- Health: http://localhost:8006/health  

Backend reaches host Ollama via `host.docker.internal`.

## 2b. Run locally

```bash
# backend
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example .env
uvicorn app.main:app --reload --port 8006

# frontend (other terminal)
cd frontend
npm install
cp ../.env.example .env.local
npm run dev
```

## Tests

```bash
cd backend && source .venv/bin/activate && PYTHONPATH=. pytest -v
cd frontend && npx vitest run
```

Ollama is mocked in backend tests; no live model required for CI-style runs.

## Limitations

- Local vision quality varies; clear invoices work best. Handwriting / heavy skew → nulls + flags.
- No database, auth, batch folders, or multi-page PDF ingest.
- Regenerated PDF/Excel reflect **extracted** fields (not a pixel-perfect copy of the source scan).
- CORS default is `localhost:3006` (not `127.0.0.1`).
- First vision call after pulling a model can be slow while weights load.

## Design and plan

- [Design spec](docs/superpowers/specs/2026-10-15-invoice-data-extractor-design.md)
- [Implementation plan](docs/superpowers/plans/2026-10-15-invoice-data-extractor.md)
