<script setup lang="ts">
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
      <section class="rounded-sm border border-[var(--color-line)] bg-white/70 p-5 backdrop-blur-sm">
        <!-- Task 5: Dropzone + preview -->
        <p class="text-slate-500">Document stage coming next</p>
      </section>
      <section class="rounded-sm border border-[var(--color-line)] bg-white/70 p-5 backdrop-blur-sm">
        <!-- Task 5: Results -->
        <p class="text-slate-500">Extraction readout coming next</p>
      </section>
    </main>
  </div>
</template>
