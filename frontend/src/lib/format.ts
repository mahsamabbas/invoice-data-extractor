const VALID_CURRENCY_CODE_RE = /^[A-Za-z]{3}$/;

export function formatMoney(currency: string | null, amount: number | null): string {
  if (amount === null || amount === undefined) return "—";
  if (!currency || !VALID_CURRENCY_CODE_RE.test(currency)) {
    // Never invent a currency (e.g. default to USD) when we don't actually
    // know what currency the invoice is in. Show the bare numeric amount.
    return amount.toFixed(2);
  }
  try {
    return new Intl.NumberFormat("en-US", { style: "currency", currency: currency.toUpperCase() }).format(amount);
  } catch {
    return `${amount.toFixed(2)} ${currency}`.trim();
  }
}

/** PDF-safe money: Helvetica cannot draw ₹ / € / etc., so use "INR 1,234.00". */
export function formatMoneyPlain(currency: string | null, amount: number | null): string {
  if (amount === null || amount === undefined) return "-";
  const num = new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
  if (currency && VALID_CURRENCY_CODE_RE.test(currency)) {
    return `${currency.toUpperCase()} ${num}`;
  }
  return num;
}

/** Strip characters jsPDF Helvetica cannot render cleanly. */
export function pdfSafeText(value: string): string {
  return value
    .replace(/[\u20B9\u00A3\u00A5\u20AC\u00A2]/g, "") // currency symbols
    .replace(/[\u2013\u2014\u2212]/g, "-") // dashes
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, '"')
    .replace(/\u00A0/g, " ")
    .replace(/[^\x09\x0A\x0D\x20-\x7E]/g, "?");
}
