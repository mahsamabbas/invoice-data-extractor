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
