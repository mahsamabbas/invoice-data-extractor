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


def _near(a: float, b: float) -> bool:
    return abs(a - b) <= TOTAL_TOLERANCE


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
            lines_sum = float(sum(amounts))  # type: ignore[arg-type]
            total = float(data.total)
            tax = float(data.tax) if data.tax is not None else None
            subtotal = float(data.subtotal) if data.subtotal is not None else None

            # Tax invoices often have lines < total. Accept:
            # lines == total, lines+tax == total, or subtotal+tax == total.
            reconciled = (
                _near(lines_sum, total)
                or (tax is not None and _near(lines_sum + tax, total))
                or (subtotal is not None and tax is not None and _near(subtotal + tax, total))
            )

            if not reconciled:
                detail = f"Line items sum to {lines_sum:.2f}"
                if tax is not None:
                    detail += f" (+ tax {tax:.2f} = {lines_sum + tax:.2f})"
                if subtotal is not None:
                    detail += f"; subtotal {subtotal:.2f}"
                detail += f" but total is {total:.2f}."
                flags.append(Flag(code="total_mismatch", message=detail))
    return data.model_copy(update={"flags": flags, "unreadable": False})
