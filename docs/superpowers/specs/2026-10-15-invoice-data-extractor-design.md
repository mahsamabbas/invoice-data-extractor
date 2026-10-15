# AI Invoice Data Extractor (ClearInvoice)

Design for App 7. Upload one synthetic invoice **image**, extract vendor, invoice number, currency, line items, and total via a local vision model, validate with Pydantic, and **flag** missing or inconsistent fields instead of guessing. No multi-page PDF pipeline, no ERP sync, no cloud Vision API required for the core demo.

## Decisions

| Topic | Choice |
| --- | --- |
| Product name | **ClearInvoice** (working brand for the UI) |
| Goal | Portfolio demo: image → structured invoice JSON with honest flags |
| Frontend | **Vue 3 + Vite + TypeScript + Tailwind CSS** (first Vue app in the portfolio) |
| Backend | **FastAPI + Pydantic v2** |
| Vision LLM | Local **Ollama** multimodal — default `qwen2.5vl` (OCR / document specialist); override via `OLLAMA_VISION_MODEL` |
| Cloud APIs | None required for core demo (no Gemini / OpenAI) |
| Persistence | **None** in v1 — extract is request-scoped only |
| Validation UX | Show extracted fields **and** clear warning flags (Approach A). Never invent missing values (`null` + flag) |
| Consistency | Server-side check: sum of line-item amounts vs `total` (tolerance `0.01`); mismatch → `total_mismatch` |
| Sample | Bundled synthetic invoice PNG under `samples/` |
| Ports | Frontend **3006**, API **8006**, Ollama **11434** |
| Repo | `invoice-data-extractor` → public under `mahsamabbas` |

## Architecture

Three runtime pieces on the developer machine:

1. **Browser + Vue 3 (Vite) + TypeScript + Tailwind** — ClearInvoice UI. Port **3006**.
2. **FastAPI** — upload validation, Ollama vision call, Pydantic parse, consistency flags. Port **8006**.
3. **Ollama on the host** (`http://127.0.0.1:11434`) — vision model. Dockerized API reaches Ollama via `host.docker.internal` (or `OLLAMA_BASE_URL`).

```
[Browser / ClearInvoice]
  dropzone · sample · preview · Extract · results + flags · JSON toggle
        │ HTTP only (multipart / JSON)
        ▼
[FastAPI :8006]
  validate file → base64 → Ollama chat (images[])
  parse JSON → InvoiceExtraction → add flags[]
        │
        ▼
[Ollama :11434]
  qwen2.5vl (or OLLAMA_VISION_MODEL)
```

**Hard rules:**

- Browser never calls Ollama.
- Model prompt: missing / unreadable fields must be `null`; do not invent.
- Flags are authoritative for “needs review”; model self-confidence is optional metadata only and does not gate the response.

## Schema

```text
LineItem
  description: str | null
  quantity: float | null
  unit_price: float | null
  amount: float | null

Flag
  code: str          # machine id
  message: str       # human-readable

InvoiceExtraction
  vendor: str | null
  invoice_number: str | null
  currency: str | null
  line_items: list[LineItem]
  total: float | null
  flags: list[Flag]
```

**Flag codes (v1):**

| Code | When |
| --- | --- |
| `missing_vendor` | `vendor` is null / blank |
| `missing_invoice_number` | `invoice_number` is null / blank |
| `missing_currency` | `currency` is null / blank |
| `missing_total` | `total` is null |
| `empty_line_items` | `line_items` empty |
| `total_mismatch` | all amounts + total present and `abs(sum(amounts) - total) > 0.01` |
| `unreadable_image` | model or heuristics indicate blank / non-invoice / unreadable |

Line-item amount, if both quantity and unit_price are present and amount is null, may be computed as `quantity * unit_price` for the sum check only — never invent vendor, invoice number, currency, or total from nothing.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | API up; Ollama reachable + model configured |
| `GET` | `/sample` | Returns bundled sample invoice image bytes |
| `POST` | `/extract` | Multipart `file` → `InvoiceExtraction` JSON |

**`POST /extract` errors:**

| Case | Status |
| --- | --- |
| Missing file, wrong MIME, over size limit | `400` |
| Ollama unreachable / timeout | `503` |
| Model returns unparseable JSON after one repair retry | `502` |

Accepted types: `image/png`, `image/jpeg`, `image/webp`. Max size: **5 MB**.

## Frontend — ClearInvoice

**Concept:** One-screen extractor. Brand-first header, invoice preview as the visual anchor, results as a structured readout — not a dashboard of cards.

| Token | Choice |
| --- | --- |
| Brand | **ClearInvoice** as hero-level wordmark |
| Atmosphere | Cool paper / ledger feel: soft slate wash, subtle grid or grain — not flat white, not purple gradient, not cream/terracotta |
| Accent | Deep teal ink on warm paper tone |
| Type | Distinctive pair (e.g. display **Fraunces** or **Newsreader**; UI **Source Sans 3** / **IBM Plex Sans**) — no Inter/Roboto/Arial default stack |
| Layout | Top brand · left/center preview + upload · right (or below on mobile) fields + table + flags |

**Motion (2–3):**

1. Dropzone accept — brief border/scale confirm.
2. Extracting — progress pulse on CTA / skeleton on result pane.
3. Flags appear — soft slide-in warning strip.

**Regions:**

- Upload / Use sample / image preview
- **Extract** primary CTA
- Field summary (vendor, number, currency, total)
- Line-items table
- Warning strip when `flags.length > 0`
- Optional “View JSON”

## Backend modules

| Module | Responsibility |
| --- | --- |
| `config` | Ports, Ollama URL/model, max upload size, total tolerance |
| `schemas` | Pydantic `LineItem`, `Flag`, `InvoiceExtraction` |
| `ollama_client` | Chat-with-image, timeout, one JSON repair retry |
| `validate_extract` | Null/blank flags + total mismatch |
| `routes` | `/health`, `/sample`, `/extract` |
| `sample` | Path to bundled synthetic PNG |

## Testing

pytest with Ollama **mocked**:

1. **Normal:** fixture image bytes + mocked model JSON → 200, key fields populated, no critical inventing.
2. **Failure / flags:** empty upload → `400`; **and/or** mocked response with mismatched total → `total_mismatch` in `flags`.

Frontend: light Vitest for any pure format/helpers if present; manual smoke for Vue UI.

## Docker & run

- `docker-compose.yml`: frontend (nginx) + backend; Ollama on host via `host.docker.internal`
- `.env.example` only in git (`OLLAMA_BASE_URL`, `OLLAMA_VISION_MODEL`, CORS / ports)
- README: stack, API, pull `qwen2.5vl`, Docker + local, tests, limitations

```bash
ollama serve
ollama pull qwen2.5vl

cd invoice-data-extractor
docker compose up --build
# http://localhost:3006  ·  API http://localhost:8006
```

## Out of scope (v1)

- Multi-page PDF / batch folders
- Persistence / history / auth
- Real vendor APIs, payments, accounting export
- Cloud Gemini Vision (optional later; not required)
- Automatic “fix” of wrong totals (flag only)

## Known limitations (ship with honesty)

- Local 7B-class vision quality varies; synthetic clear invoices are the happy path.
- Handwriting, heavy skew, and tiny scans may yield nulls + `unreadable_image`.
- No calibrated confidence score — flags and human review are the guard.
- Single image per request; restart does not keep past extractions.

## Delivery checklist

1. Public GitHub repo + README + `.env.example` (no secrets)
2. Working core flow + screenshot
3. pytest: ≥1 normal + ≥1 failure/flag case
4. Brief limitations + what was built
5. Commits authored as **mahsamabbas** only (no Cursor co-author trailer)
