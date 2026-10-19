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


def test_tax_invoice_lines_plus_tax_matches_total():
    """Williams-style tax invoice: line 500 + tax 50 = total 550 → no mismatch."""
    data = InvoiceExtraction(
        vendor="Williams Hospital",
        invoice_number="1001",
        currency="USD",
        line_items=[LineItem(description="X-ray", quantity=1, unit_price=500.0, amount=500.0)],
        subtotal=500.0,
        tax=50.0,
        total=550.0,
        flags=[],
    )
    assert apply_flags(data).flags == []


def test_tax_alone_reconciles_without_subtotal():
    data = InvoiceExtraction(
        vendor="Williams Hospital",
        invoice_number="1001",
        currency="USD",
        line_items=[LineItem(description="X-ray", quantity=1, unit_price=500.0, amount=500.0)],
        tax=50.0,
        total=550.0,
        flags=[],
    )
    assert apply_flags(data).flags == []
