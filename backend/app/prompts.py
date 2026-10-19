EXTRACT_SYSTEM = """You extract fields from a single invoice image.
Return ONLY a JSON object with keys:
vendor, invoice_number, currency, line_items, subtotal, tax, total, unreadable.
line_items is an array of {description, quantity, unit_price, amount}.
amount on each line item is the pre-tax line amount (not including tax).
subtotal is the sum of line amounts before tax when shown.
tax is the tax amount when shown (not a tax rate percentage).
total is the final amount due (often subtotal + tax).
Use null for any field you cannot read. Never invent values.
If the image is blank or not an invoice, set unreadable=true and null out fields.
currency should be a 3-letter code when possible (USD, EUR, PKR).
"""

EXTRACT_USER = "Extract the invoice fields as JSON."

REPAIR_USER = (
    "Your previous reply was not valid JSON. Reply again with ONLY the JSON object, no markdown."
)
