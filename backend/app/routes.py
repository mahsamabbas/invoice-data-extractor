from pathlib import Path

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse, Response

from app.config import get_settings
from app.extract import ExtractError, extract_invoice
from app.ollama_client import ollama_reachable
from app.schemas import HealthOut

router = APIRouter()

ALLOWED = {"image/png", "image/jpeg", "image/webp", "image/jpg"}


def _sample_path() -> Path:
    configured = get_settings().sample_invoice_path.strip()
    if configured:
        return Path(configured)
    # backend/app/routes.py → parents[2] = repo root
    return Path(__file__).resolve().parents[2] / "samples" / "sample_invoice.png"


@router.get("/health", response_model=HealthOut)
async def health():
    settings = get_settings()
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
