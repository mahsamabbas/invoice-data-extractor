import { describe, expect, it } from "vitest";
import { formatMoney } from "./format";

describe("formatMoney", () => {
  it("formats USD", () => {
    expect(formatMoney("USD", 78)).toMatch(/\$78/);
  });
  it("shows em dash for null", () => {
    expect(formatMoney("USD", null)).toBe("—");
  });
  it("falls back to USD when currency is missing", () => {
    expect(formatMoney(null, 12.5)).toMatch(/\$12\.50/);
  });
  it("formats a non-USD currency code", () => {
    expect(formatMoney("EUR", 10)).toMatch(/€|EUR/);
  });
});
