import { describe, expect, it } from "vitest";
import { invoiceBasename } from "./exportInvoice";
import type { InvoiceExtraction } from "../types";

const base: InvoiceExtraction = {
  vendor: "Williams Hospital",
  invoice_number: "#1001",
  currency: "USD",
  line_items: [],
  subtotal: 500,
  tax: 50,
  total: 550,
  flags: [],
};

describe("invoiceBasename", () => {
  it("sanitizes vendor and invoice number for filenames", () => {
    expect(invoiceBasename(base)).toBe("ClearInvoice_Williams_Hospital__1001");
  });
});
