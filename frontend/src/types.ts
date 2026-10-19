export interface LineItem {
  description: string | null;
  quantity: number | null;
  unit_price: number | null;
  amount: number | null;
}

export interface Flag {
  code: string;
  message: string;
}

export interface InvoiceExtraction {
  vendor: string | null;
  invoice_number: string | null;
  currency: string | null;
  line_items: LineItem[];
  subtotal: number | null;
  tax: number | null;
  total: number | null;
  flags: Flag[];
}
