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
