"""Write samples/sample_invoice.png — synthetic US invoice for demos."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "samples" / "sample_invoice.png"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (800, 1000), "#FFFFFF")
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    lines = [
        "NORTHWIND SUPPLIES LLC",
        "1847 Market Street, Suite 200",
        "San Francisco, CA 94103",
        "",
        "INVOICE",
        "Invoice #: INV-1042",
        "Date: October 1, 2026",
        "Bill To: BrightMart Commerce Studio",
        "",
        "Description              Qty    Unit     Amount",
        "------------------------------------------------",
        "A4 Copy Paper (case)       2    12.50     25.00",
        "Black Toner Cartridge      1    45.00     45.00",
        "Shipping                   1     8.00      8.00",
        "",
        "Subtotal                                    78.00",
        "Tax (0%)                                     0.00",
        "TOTAL USD                                   78.00",
        "",
        "Payment due within 30 days.",
    ]
    y = 40
    for line in lines:
        d.text((48, y), line, fill="#111111", font=font)
        y += 28
    img.save(OUT, "PNG")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
