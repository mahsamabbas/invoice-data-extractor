export function formatMoney(currency: string | null, amount: number | null): string {
  if (amount === null || amount === undefined) return "—";
  const code = currency && currency.length === 3 ? currency : "USD";
  try {
    return new Intl.NumberFormat("en-US", { style: "currency", currency: code }).format(amount);
  } catch {
    return `${amount.toFixed(2)} ${currency ?? ""}`.trim();
  }
}
