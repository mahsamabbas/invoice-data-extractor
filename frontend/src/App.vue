<script setup lang="ts">
import { computed, ref } from "vue";
import DocumentStage from "./components/DocumentStage.vue";
import ExtractionPanel from "./components/ExtractionPanel.vue";
import { extractInvoice } from "./api";
import type { InvoiceExtraction } from "./types";

const file = ref<File | null>(null);
const result = ref<InvoiceExtraction | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

const canExtract = computed(() => file.value !== null && !loading.value);

function onFileReady(next: File | null) {
  file.value = next;
  result.value = null;
  error.value = null;
}

async function onExtract() {
  if (!file.value || loading.value) return;
  const f = file.value;
  loading.value = true;
  error.value = null;
  result.value = null;
  try {
    const extracted = await extractInvoice(f);
    if (file.value === f) {
      result.value = extracted;
    }
  } catch (err) {
    if (file.value === f) {
      error.value = err instanceof Error ? err.message : "Extraction failed";
    }
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="min-h-full px-5 py-8 md:px-10 md:py-10">
    <header class="mx-auto max-w-6xl mb-10">
      <p class="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--color-ink)]">
        Local vision · no cloud key
      </p>
      <h1 class="brand mt-2 text-5xl md:text-6xl text-[var(--color-ink-deep)]">
        ClearInvoice
      </h1>
      <p class="mt-3 max-w-xl text-lg text-slate-600">
        Drop a synthetic invoice. We read the fields, validate the math, and flag anything unclear —
        we never invent numbers.
      </p>
    </header>

    <main class="mx-auto grid max-w-6xl gap-8 lg:grid-cols-2 lg:gap-10">
      <div class="flex flex-col gap-4">
        <DocumentStage @file-ready="onFileReady" />

        <button
          type="button"
          class="brand relative w-full overflow-hidden rounded-sm bg-[var(--color-ink-deep)] px-6 py-3.5 text-lg font-semibold text-[var(--color-paper)] shadow-md transition disabled:cursor-not-allowed disabled:opacity-40 enabled:hover:bg-[var(--color-ink)]"
          :class="{ extracting: loading }"
          :disabled="!canExtract"
          @click="onExtract"
        >
          {{ loading ? "Extracting…" : "Extract invoice" }}
        </button>
      </div>

      <ExtractionPanel :result="result" :loading="loading" :error="error" />
    </main>
  </div>
</template>
