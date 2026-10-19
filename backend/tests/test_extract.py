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
async def test_extract_unreadable_image_yields_flag_not_502():
    """Vision model flags an unreadable image with null line_items and
    currency-formatted numeric strings; this must not raise a 502 and must
    surface the unreadable_image flag via apply_flags."""
    payload = {
        "message": {
            "content": json.dumps(
                {
                    "vendor": None,
                    "invoice_number": None,
                    "currency": None,
                    "line_items": None,
                    "total": "$--",
                    "unreadable": True,
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
    assert out.line_items == []
    assert out.total is None
    codes = {f.code for f in out.flags}
    assert "unreadable_image" in codes
    assert "missing_total" in codes
    assert "empty_line_items" in codes


@pytest.mark.asyncio
async def test_extract_unreadable_null_coerces_to_false():
    """qwen2.5vl often emits unreadable: null on readable invoices; must not 502."""
    payload = {
        "message": {
            "content": json.dumps(
                {
                    "vendor": "NORTHWIND SUPPLIES LLC",
                    "invoice_number": "INV-1042",
                    "currency": "USD",
                    "line_items": [
                        {
                            "description": "A4 Copy Paper (case)",
                            "quantity": "2",
                            "unit_price": "12.50",
                            "amount": "25.00",
                        }
                    ],
                    "total": "25.00",
                    "unreadable": None,
                }
            )
        }
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    settings = Settings(ollama_base_url="http://ollama.test")
    async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
        out = await extract_invoice(b"fake-png", "image/png", settings, client=client)
    assert out.vendor == "NORTHWIND SUPPLIES LLC"
    assert out.unreadable is False
    assert "unreadable_image" not in {f.code for f in out.flags}


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
