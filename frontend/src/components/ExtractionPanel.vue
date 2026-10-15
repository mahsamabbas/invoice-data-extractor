<script setup lang="ts">
import { ref } from "vue";
import type { InvoiceExtraction } from "../types";
import { formatMoney } from "../lib/format";
import FlagStrip from "./FlagStrip.vue";

const props = defineProps<{
  result: InvoiceExtraction | null;
  loading: boolean;
  error: string | null;
}>();

const showJson = ref(false);

function toggleJson() {
  showJson.value = !showJson.value;
}

function cellMoney(currency: string | null | undefined, amount: number | null | undefined) {
  return formatMoney(currency ?? null, amount ?? null);
}
</script>

<template>
  <div class="rounded-sm border border-[var(--color-line)] bg-white/70 p-5 backdrop-blur-sm">
    <div class="mb-4 flex items-center justify-between">
      <h2
        class="brand text-xl text-[var(--color-ink-deep)]"
        :class="{ extracting: props.loading }"
      >
        Extraction
      </h2>
      <span
        v-if="props.loading"
        class="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--color-ink)]"
      >
        Reading…
      </span>
      <span
        v-else-if="props.result"
        class="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--color-ink)]"
      >
        Done
      </span>
    </div>

    <!-- Error state -->
    <div
      v-if="props.error"
      class="rounded-sm border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700"
    >
      {{ props.error }}
    </div>

    <!-- Loading skeleton -->
    <div v-else-if="props.loading" class="flex flex-col gap-4">
      <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div v-for="n in 4" :key="n" class="flex flex-col gap-2">
          <div class="h-3 w-16 animate-pulse rounded-sm bg-[var(--color-line)]/70" />
          <div class="h-5 w-full animate-pulse rounded-sm bg-[var(--color-line)]/50" />
        </div>
      </div>
      <div class="flex flex-col gap-2">
        <div v-for="n in 3" :key="n" class="h-8 w-full animate-pulse rounded-sm bg-[var(--color-line)]/40" />
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!props.result"
      class="flex min-h-64 flex-col items-center justify-center gap-2 rounded-sm border border-dashed border-[var(--color-line)] bg-[var(--color-paper)]/50 py-10 text-center"
    >
      <p class="font-semibold text-slate-500">No extraction yet</p>
      <p class="max-w-xs text-sm text-slate-400">
        Upload or choose the sample invoice, then run Extract to see the fields here.
      </p>
    </div>

    <!-- Result -->
    <div v-else class="flex flex-col gap-5">
      <dl class="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div class="flex flex-col gap-1">
          <dt class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Vendor</dt>
          <dd class="truncate text-base font-semibold text-[var(--color-slate)]">
            {{ props.result.vendor ?? "—" }}
          </dd>
        </div>
        <div class="flex flex-col gap-1">
          <dt class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Invoice #</dt>
          <dd class="truncate text-base font-semibold text-[var(--color-slate)]">
            {{ props.result.invoice_number ?? "—" }}
          </dd>
        </div>
        <div class="flex flex-col gap-1">
          <dt class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Currency</dt>
          <dd class="truncate text-base font-semibold text-[var(--color-slate)]">
            {{ props.result.currency ?? "—" }}
          </dd>
        </div>
        <div class="flex flex-col gap-1">
          <dt class="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Total</dt>
          <dd class="brand truncate text-lg font-semibold text-[var(--color-ink-deep)]">
            {{ cellMoney(props.result.currency, props.result.total) }}
          </dd>
        </div>
      </dl>

      <div v-if="props.result.line_items.length > 0" class="overflow-x-auto">
        <table class="w-full border-collapse text-sm">
          <thead>
            <tr class="border-b border-[var(--color-line)] text-left text-xs uppercase tracking-[0.12em] text-slate-400">
              <th class="py-2 pr-3 font-semibold">Description</th>
              <th class="py-2 px-3 text-right font-semibold">Qty</th>
              <th class="py-2 px-3 text-right font-semibold">Unit price</th>
              <th class="py-2 pl-3 text-right font-semibold">Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, idx) in props.result.line_items"
              :key="idx"
              class="border-b border-dashed border-[var(--color-line)]/80"
              :class="idx % 2 === 1 ? 'bg-[var(--color-paper)]/50' : ''"
            >
              <td class="py-2 pr-3 text-[var(--color-slate)]">{{ item.description ?? "—" }}</td>
              <td class="py-2 px-3 text-right tabular-nums text-slate-600">{{ item.quantity ?? "—" }}</td>
              <td class="py-2 px-3 text-right tabular-nums text-slate-600">
                {{ cellMoney(props.result.currency, item.unit_price) }}
              </td>
              <td class="py-2 pl-3 text-right tabular-nums font-semibold text-[var(--color-slate)]">
                {{ cellMoney(props.result.currency, item.amount) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="text-sm text-slate-400">No line items detected.</p>

      <FlagStrip :flags="props.result.flags" />

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
