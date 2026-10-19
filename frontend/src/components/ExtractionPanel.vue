<script setup lang="ts">
import { computed, ref } from "vue";
import type { InvoiceExtraction } from "../types";
import { formatMoney } from "../lib/format";
import { downloadExcel, downloadPdf } from "../lib/exportInvoice";
import FlagStrip from "./FlagStrip.vue";

const props = defineProps<{
  result: InvoiceExtraction | null;
  loading: boolean;
  error: string | null;
}>();

const showJson = ref(false);
const exportError = ref<string | null>(null);

function toggleJson() {
  showJson.value = !showJson.value;
}

function onDownloadPdf() {
  if (!props.result) return;
  exportError.value = null;
  try {
    downloadPdf(props.result);
  } catch (err) {
    exportError.value = err instanceof Error ? err.message : "Could not create PDF";
  }
}

function onDownloadExcel() {
  if (!props.result) return;
  exportError.value = null;
  try {
    downloadExcel(props.result);
  } catch (err) {
    exportError.value = err instanceof Error ? err.message : "Could not create Excel file";
  }
}

function money(amount: number | null | undefined) {
  return formatMoney(props.result?.currency ?? null, amount ?? null);
}

const fieldRows = computed(() => {
  const r = props.result;
  if (!r) return [];
  return [
    { label: "Vendor", value: r.vendor ?? "—", money: false, emphasize: true },
    { label: "Invoice number", value: r.invoice_number ?? "—", money: false, emphasize: false },
    { label: "Currency", value: r.currency ?? "—", money: false, emphasize: false },
    { label: "Subtotal", value: money(r.subtotal), money: true, emphasize: false },
    { label: "Tax", value: money(r.tax), money: true, emphasize: false },
    { label: "Total", value: money(r.total), money: true, emphasize: true },
  ];
});
</script>

<template>
  <div class="rounded-sm border border-[var(--color-line)] bg-white/80 p-5 shadow-[0_1px_0_rgba(15,23,42,0.04)] backdrop-blur-sm md:p-6">
    <div class="mb-5 flex items-end justify-between gap-3 border-b border-[var(--color-line)] pb-4">
      <div>
        <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-ink)]">
          Results
        </p>
        <h2
          class="brand mt-1 text-2xl text-[var(--color-ink-deep)]"
          :class="{ extracting: props.loading }"
        >
          Extraction
        </h2>
      </div>
      <span
        v-if="props.loading"
        class="mb-1 shrink-0 rounded-sm bg-[var(--color-ink)]/10 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--color-ink)]"
      >
        Reading…
      </span>
      <span
        v-else-if="props.result"
        class="mb-1 shrink-0 rounded-sm bg-emerald-50 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-emerald-700"
      >
        Done
      </span>
    </div>

    <div
      v-if="props.error"
      class="rounded-sm border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700"
    >
      {{ props.error }}
    </div>

    <div v-else-if="props.loading" class="flex flex-col gap-3">
      <div
        v-for="n in 6"
        :key="n"
        class="flex items-center justify-between gap-4 border-b border-dashed border-[var(--color-line)]/70 py-3"
      >
        <div class="h-3 w-24 animate-pulse rounded-sm bg-[var(--color-line)]/70" />
        <div class="h-4 w-40 animate-pulse rounded-sm bg-[var(--color-line)]/50" />
      </div>
      <div class="mt-2 h-24 animate-pulse rounded-sm bg-[var(--color-line)]/35" />
    </div>

    <div
      v-else-if="!props.result"
      class="flex min-h-64 flex-col items-center justify-center gap-2 rounded-sm border border-dashed border-[var(--color-line)] bg-[var(--color-paper)]/50 py-10 text-center"
    >
      <p class="font-semibold text-slate-500">No extraction yet</p>
      <p class="max-w-xs text-sm text-slate-400">
        Upload or choose the sample invoice, then run Extract to see every field here.
      </p>
    </div>

    <div v-else class="flex flex-col gap-6">
      <!-- All scalar fields as full-width label | value rows -->
      <section
        aria-label="Invoice fields"
        class="overflow-hidden rounded-sm border border-[var(--color-line)] bg-[var(--color-paper)]/40"
      >
        <div
          v-for="(row, idx) in fieldRows"
          :key="row.label"
          class="grid grid-cols-1 gap-1 px-4 py-3.5 sm:grid-cols-[9.5rem_1fr] sm:items-baseline sm:gap-6"
          :class="[
            idx < fieldRows.length - 1 ? 'border-b border-[var(--color-line)]/80' : '',
            idx % 2 === 1 ? 'bg-white/50' : '',
            row.emphasize ? 'bg-[var(--color-ink)]/[0.03]' : '',
          ]"
        >
          <p class="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">
            {{ row.label }}
          </p>
          <p
            class="min-w-0 break-words text-[var(--color-slate)]"
            :class="
              row.emphasize
                ? 'brand text-xl font-semibold text-[var(--color-ink-deep)]'
                : 'text-base font-semibold'
            "
          >
            <span :class="row.money ? 'tabular-nums whitespace-nowrap' : ''">{{ row.value }}</span>
          </p>
        </div>
      </section>

      <!-- Line items -->
      <section aria-label="Line items">
        <div class="mb-2 flex items-baseline justify-between gap-2">
          <p class="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">
            Line items
          </p>
          <p class="text-xs text-slate-400">
            {{ props.result.line_items.length }}
            {{ props.result.line_items.length === 1 ? "row" : "rows" }}
          </p>
        </div>

        <div
          v-if="props.result.line_items.length > 0"
          class="overflow-x-auto rounded-sm border border-[var(--color-line)]"
        >
          <table class="w-full min-w-[22rem] border-collapse text-sm">
            <thead>
              <tr class="bg-[var(--color-paper)]/80 text-left text-[11px] uppercase tracking-[0.12em] text-slate-400">
                <th class="px-3 py-2.5 font-semibold">Description</th>
                <th class="px-3 py-2.5 text-right font-semibold">Qty</th>
                <th class="px-3 py-2.5 text-right font-semibold">Unit price</th>
                <th class="px-3 py-2.5 text-right font-semibold">Amount</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(item, idx) in props.result.line_items"
                :key="idx"
                class="border-t border-[var(--color-line)]/80"
                :class="idx % 2 === 1 ? 'bg-[var(--color-paper)]/40' : 'bg-white/60'"
              >
                <td class="max-w-[16rem] px-3 py-2.5 break-words text-[var(--color-slate)]">
                  {{ item.description ?? "—" }}
                </td>
                <td class="px-3 py-2.5 text-right tabular-nums whitespace-nowrap text-slate-600">
                  {{ item.quantity ?? "—" }}
                </td>
                <td class="px-3 py-2.5 text-right tabular-nums whitespace-nowrap text-slate-600">
                  {{ money(item.unit_price) }}
                </td>
                <td class="px-3 py-2.5 text-right tabular-nums whitespace-nowrap font-semibold text-[var(--color-slate)]">
                  {{ money(item.amount) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p
          v-else
          class="rounded-sm border border-dashed border-[var(--color-line)] px-3 py-4 text-sm text-slate-400"
        >
          No line items detected.
        </p>
      </section>

      <FlagStrip :flags="props.result.flags" />

      <section
        aria-label="Export"
        class="flex flex-col gap-3 rounded-sm border border-[var(--color-line)] bg-[var(--color-paper)]/50 p-4"
      >
        <div>
          <p class="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">
            Take away
          </p>
          <p class="mt-1 text-sm text-slate-500">
            Download a regenerated invoice PDF or a spreadsheet of these fields.
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            type="button"
            class="rounded-sm bg-[var(--color-ink-deep)] px-4 py-2.5 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-paper)] transition hover:bg-[var(--color-ink)]"
            @click="onDownloadPdf"
          >
            Download PDF
          </button>
          <button
            type="button"
            class="rounded-sm border border-[var(--color-ink)]/40 bg-white px-4 py-2.5 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--color-ink-deep)] transition hover:border-[var(--color-ink)] hover:bg-[var(--color-ink)]/[0.06]"
            @click="onDownloadExcel"
          >
            Download Excel
          </button>
        </div>
        <p v-if="exportError" class="text-sm font-medium text-red-600">{{ exportError }}</p>
      </section>

      <div>
        <button
          type="button"
          class="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--color-ink)] underline decoration-dotted underline-offset-4 hover:text-[var(--color-ink-deep)]"
          @click="toggleJson"
        >
          {{ showJson ? "Hide JSON" : "View JSON" }}
        </button>
        <pre
          v-if="showJson"
          class="mt-2 max-h-72 overflow-auto rounded-sm border border-[var(--color-line)] bg-[var(--color-slate)]/95 p-3 text-xs text-emerald-200"
        >{{ JSON.stringify(props.result, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>
