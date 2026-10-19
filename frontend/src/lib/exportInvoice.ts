import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx";
import type { InvoiceExtraction } from "../types";
import { formatMoneyPlain, pdfSafeText } from "./format";

function safeName(value: string | null | undefined, fallback: string): string {
  const raw = (value ?? fallback).trim() || fallback;
  return raw.replace(/[^\w.\-]+/g, "_").slice(0, 60);
}

export function invoiceBasename(result: InvoiceExtraction): string {
  const num = safeName(result.invoice_number, "invoice");
  const vendor = safeName(result.vendor, "clearinvoice");
  return `ClearInvoice_${vendor}_${num}`;
}

function pdfMoney(result: InvoiceExtraction, amount: number | null | undefined): string {
  return formatMoneyPlain(result.currency, amount ?? null);
}

export function downloadExcel(result: InvoiceExtraction): void {
  const summary = [
    ["Field", "Value"],
    ["Vendor", result.vendor ?? ""],
    ["Invoice number", result.invoice_number ?? ""],
    ["Currency", result.currency ?? ""],
    ["Subtotal", result.subtotal ?? ""],
    ["Tax", result.tax ?? ""],
    ["Total", result.total ?? ""],
  ];

  const lines = [
    ["Description", "Quantity", "Unit price", "Amount"],
    ...result.line_items.map((item) => [
      item.description ?? "",
      item.quantity ?? "",
      item.unit_price ?? "",
      item.amount ?? "",
    ]),
  ];

  const flags =
    result.flags.length > 0
      ? [["Code", "Message"], ...result.flags.map((f) => [f.code, f.message])]
      : [["Code", "Message"], ["(none)", ""]];

  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(summary), "Summary");
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(lines), "Line items");
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(flags), "Flags");
  XLSX.writeFile(wb, `${invoiceBasename(result)}.xlsx`);
}

/**
 * Modern invoice PDF template — fixed column geometry so totals
 * snap to the Amount column (no free-floating misaligned numbers).
 */
export function downloadPdf(result: InvoiceExtraction): void {
  const doc = new jsPDF({ unit: "pt", format: "letter" });
  const pageW = doc.internal.pageSize.getWidth();
  const pageH = doc.internal.pageSize.getHeight();

  const ink = { r: 15, g: 118, b: 110 };
  const inkDeep = { r: 17, g: 94, b: 89 };
  const slate = { r: 30, g: 41, b: 59 };
  const muted = { r: 100, g: 116, b: 139 };
  const paper = { r: 247, g: 244, b: 239 };
  const line = { r: 214, g: 211, b: 209 };

  const marginX = 44;
  const contentW = pageW - marginX * 2;
  // Exact column widths that sum to contentW (must stay in sync with totals box)
  const col = {
    desc: Math.round(contentW * 0.46),
    qty: Math.round(contentW * 0.10),
    unit: Math.round(contentW * 0.22),
    amt: 0,
  };
  col.amt = contentW - col.desc - col.qty - col.unit;

  // --- Header band ---
  doc.setFillColor(ink.r, ink.g, ink.b);
  doc.rect(0, 0, pageW, 88, "F");

  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(22);
  doc.text("ClearInvoice", marginX, 38);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(220, 240, 238);
  doc.text("Extracted invoice  ·  review before sending", marginX, 56);

  doc.setFont("helvetica", "bold");
  doc.setFontSize(11);
  doc.setTextColor(255, 255, 255);
  doc.text("INVOICE", pageW - marginX, 38, { align: "right" });
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.text(pdfSafeText(`# ${result.invoice_number ?? "-"}`), pageW - marginX, 56, {
    align: "right",
  });

  let y = 118;

  // --- Party / meta cards ---
  const cardGap = 16;
  const cardW = (contentW - cardGap) / 2;
  const cardH = 78;

  // Left card: Bill from / vendor
  doc.setFillColor(paper.r, paper.g, paper.b);
  doc.roundedRect(marginX, y, cardW, cardH, 4, 4, "F");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(8);
  doc.setTextColor(ink.r, ink.g, ink.b);
  doc.text("VENDOR", marginX + 14, y + 18);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.setTextColor(slate.r, slate.g, slate.b);
  const vendorLines = doc.splitTextToSize(
    pdfSafeText(result.vendor ?? "Unknown vendor"),
    cardW - 28,
  );
  doc.text(vendorLines.slice(0, 2), marginX + 14, y + 38);

  // Right card: meta
  const rightCardX = marginX + cardW + cardGap;
  doc.setFillColor(paper.r, paper.g, paper.b);
  doc.roundedRect(rightCardX, y, cardW, cardH, 4, 4, "F");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(8);
  doc.setTextColor(ink.r, ink.g, ink.b);
  doc.text("DETAILS", rightCardX + 14, y + 18);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(slate.r, slate.g, slate.b);
  const detailRows: [string, string][] = [
    ["Invoice #", pdfSafeText(result.invoice_number ?? "-")],
    ["Currency", pdfSafeText(result.currency ?? "-")],
  ];
  let dy = y + 36;
  for (const [k, v] of detailRows) {
    doc.setTextColor(muted.r, muted.g, muted.b);
    doc.text(k, rightCardX + 14, dy);
    doc.setTextColor(slate.r, slate.g, slate.b);
    doc.setFont("helvetica", "bold");
    doc.text(v, rightCardX + cardW - 14, dy, { align: "right" });
    doc.setFont("helvetica", "normal");
    dy += 16;
  }

  y += cardH + 28;

  // --- Line items table ---
  const body =
    result.line_items.length > 0
      ? result.line_items.map((item) => [
          pdfSafeText(item.description ?? "-"),
          item.quantity == null ? "-" : String(item.quantity),
          pdfMoney(result, item.unit_price),
          pdfMoney(result, item.amount),
        ])
      : [["No line items extracted", "-", "-", "-"]];

  autoTable(doc, {
    startY: y,
    head: [["Description", "Qty", "Unit price", "Amount"]],
    body,
    tableWidth: contentW,
    margin: { left: marginX, right: marginX },
    theme: "plain",
    headStyles: {
      fillColor: [inkDeep.r, inkDeep.g, inkDeep.b],
      textColor: 255,
      fontStyle: "bold",
      fontSize: 9,
      cellPadding: { top: 10, bottom: 10, left: 10, right: 10 },
    },
    bodyStyles: {
      fontSize: 9,
      textColor: [slate.r, slate.g, slate.b],
      cellPadding: { top: 9, bottom: 9, left: 10, right: 10 },
      lineColor: [line.r, line.g, line.b],
      lineWidth: 0.4,
    },
    alternateRowStyles: {
      fillColor: [252, 250, 247],
    },
    columnStyles: {
      0: { cellWidth: col.desc, halign: "left", overflow: "linebreak" },
      1: { cellWidth: col.qty, halign: "center" },
      2: { cellWidth: col.unit, halign: "right" },
      3: { cellWidth: col.amt, halign: "right", fontStyle: "bold" },
    },
    didDrawPage: () => {
      // footer on each page
      doc.setFont("helvetica", "normal");
      doc.setFontSize(8);
      doc.setTextColor(muted.r, muted.g, muted.b);
      doc.text("ClearInvoice  ·  generated locally", marginX, pageH - 24);
      doc.text("Page " + String(doc.getCurrentPageInfo().pageNumber), pageW - marginX, pageH - 24, {
        align: "right",
      });
    },
  });

  // @ts-expect-error lastAutoTable injected by plugin
  y = (doc.lastAutoTable?.finalY ?? y) + 20;

  // --- Totals panel: same right edge as Amount column ---
  const totalsW = col.unit + col.amt;
  const totalsX = marginX + col.desc + col.qty;
  const rowH = 22;
  const totals: { label: string; value: string; strong?: boolean }[] = [
    { label: "Subtotal", value: pdfMoney(result, result.subtotal) },
    { label: "Tax", value: pdfMoney(result, result.tax) },
    { label: "Total due", value: pdfMoney(result, result.total), strong: true },
  ];
  const boxH = totals.length * rowH + 20;

  doc.setFillColor(paper.r, paper.g, paper.b);
  doc.roundedRect(totalsX, y, totalsW, boxH, 4, 4, "F");
  doc.setDrawColor(ink.r, ink.g, ink.b);
  doc.setLineWidth(1.2);
  doc.line(totalsX, y, totalsX + totalsW, y);

  let ty = y + 18;
  const valueRight = totalsX + totalsW - 12;
  const labelLeft = totalsX + 12;

  for (const row of totals) {
    if (row.strong) {
      doc.setFillColor(ink.r, ink.g, ink.b);
      doc.roundedRect(totalsX + 4, ty - 12, totalsW - 8, rowH, 3, 3, "F");
      doc.setTextColor(255, 255, 255);
      doc.setFont("helvetica", "bold");
    } else {
      doc.setTextColor(slate.r, slate.g, slate.b);
      doc.setFont("helvetica", "normal");
    }
    doc.setFontSize(10);
    doc.text(row.label, labelLeft, ty);
    doc.text(row.value, valueRight, ty, { align: "right" });
    ty += rowH;
  }

  y += boxH + 18;

  // --- Flags ---
  if (result.flags.length > 0) {
    const flagBoxH = 18 + result.flags.length * 14 + 10;
    doc.setFillColor(255, 247, 237);
    doc.roundedRect(marginX, y, contentW, flagBoxH, 4, 4, "F");
    doc.setFont("helvetica", "bold");
    doc.setFontSize(9);
    doc.setTextColor(180, 83, 9);
    doc.text("Needs review", marginX + 12, y + 16);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(120, 53, 15);
    let fy = y + 32;
    for (const flag of result.flags) {
      doc.text(pdfSafeText(`- ${flag.code}: ${flag.message}`), marginX + 12, fy, {
        maxWidth: contentW - 24,
      });
      fy += 14;
    }
  }

  doc.save(`${invoiceBasename(result)}.pdf`);
}
