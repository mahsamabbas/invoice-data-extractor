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
