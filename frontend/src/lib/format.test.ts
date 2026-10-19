import { describe, expect, it } from "vitest";
import { formatMoney, formatMoneyPlain, pdfSafeText } from "./format";

describe("formatMoney", () => {
  it("formats USD", () => {
    expect(formatMoney("USD", 78)).toMatch(/\$78/);
  });
  it("shows em dash for null", () => {
    expect(formatMoney("USD", null)).toBe("—");
  });
  it("never invents USD when currency is missing", () => {
    expect(formatMoney(null, 12.5)).toBe("12.50");
  });
  it("formats a non-USD currency code", () => {
    expect(formatMoney("EUR", 10)).toMatch(/€|EUR/);
  });
  it("falls back to a plain number for an invalid currency code", () => {
    expect(formatMoney("XX", 12.5)).toBe("12.50");
    expect(formatMoney("TOOLONG", 7)).toBe("7.00");
    expect(formatMoney("", 3)).toBe("3.00");
  });
});

describe("formatMoneyPlain", () => {
  it("uses ASCII currency code for PDF-safe INR amounts", () => {
    expect(formatMoneyPlain("INR", 7226)).toBe("INR 7,226.00");
  });
  it("shows dash for null", () => {
    expect(formatMoneyPlain("INR", null)).toBe("-");
  });
});

describe("pdfSafeText", () => {
  it("strips rupee symbol that Helvetica cannot draw", () => {
    expect(pdfSafeText("₹240.00")).toBe("240.00");
  });
});
