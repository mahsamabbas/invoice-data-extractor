<script setup lang="ts">
import type { Flag } from "../types";

defineProps<{
  flags: Flag[];
}>();
</script>

<template>
  <div
    v-if="flags.length > 0"
    class="flag-enter mt-5 rounded-sm border border-amber-300/70 bg-[var(--color-warn-soft)] p-4"
  >
    <p
      class="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-[var(--color-warn)]"
    >
      <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M12 9v4m0 4h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"
        />
      </svg>
      Needs a human look
    </p>
    <ul class="flex flex-col gap-1.5">
      <li
        v-for="flag in flags"
        :key="flag.code"
        class="flex items-start gap-2 text-sm text-amber-900"
      >
        <span
          class="mt-0.5 shrink-0 rounded-sm bg-amber-200/70 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-amber-800"
        >
          {{ flag.code }}
        </span>
        <span>{{ flag.message }}</span>
      </li>
    </ul>
  </div>
</template>
