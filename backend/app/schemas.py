import re

from pydantic import BaseModel, Field, field_validator

_NUMERIC_STRIP_RE = re.compile(r"[^0-9.\-]")


def _coerce_lenient_float(value: object) -> object:
    """Best-effort coercion of model output to a float.

    Vision models sometimes emit numbers as strings with currency symbols,
    thousands separators, or stray whitespace (e.g. "$1,234.56"). Rather than
    raising a 502 for the whole request, strip non-numeric characters and
    return None (not a parse error) when the result still can't be parsed so
    downstream missing_* flags can report it instead.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        cleaned = _NUMERIC_STRIP_RE.sub("", value.strip())
        if not cleaned or cleaned in {"-", "."}:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return value


class LineItem(BaseModel):
    description: str | None = None
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None

    @field_validator("quantity", "unit_price", "amount", mode="before")
    @classmethod
    def _lenient_numeric(cls, value: object) -> object:
        return _coerce_lenient_float(value)


class Flag(BaseModel):
    code: str
    message: str


class InvoiceExtraction(BaseModel):
    vendor: str | None = None
    invoice_number: str | None = None
    currency: str | None = None
    line_items: list[LineItem] = Field(default_factory=list)
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    flags: list[Flag] = Field(default_factory=list)
    unreadable: bool = False  # model hint; consumed by apply_flags then stripped from API if desired

    @field_validator("line_items", mode="before")
    @classmethod
    def _none_line_items_to_empty_list(cls, value: object) -> object:
        if value is None:
            return []
        return value

    @field_validator("subtotal", "tax", "total", mode="before")
    @classmethod
    def _lenient_money_fields(cls, value: object) -> object:
        return _coerce_lenient_float(value)

    @field_validator("unreadable", mode="before")
    @classmethod
    def _coerce_unreadable(cls, value: object) -> object:
        # Vision models often emit null / junk instead of a clean boolean.
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes"}:
                return True
            return False
        # lists/dicts/other junk → treat as readable (false); flags still catch empties
        return False


class HealthOut(BaseModel):
    status: str
    ollama: bool
    model: str
