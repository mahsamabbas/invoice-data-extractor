import type { InvoiceExtraction } from "./types";

const base = import.meta.env.VITE_API_BASE ?? "http://localhost:8006";

export async function fetchSampleBlob(): Promise<Blob> {
  const r = await fetch(`${base}/sample`);
  if (!r.ok) throw new Error("Could not load sample invoice");
  return r.blob();
}

export async function extractInvoice(file: File): Promise<InvoiceExtraction> {
  const body = new FormData();
  body.append("file", file);
  const r = await fetch(`${base}/extract`, { method: "POST", body });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail ?? `Extract failed (${r.status})`);
  return data as InvoiceExtraction;
}
