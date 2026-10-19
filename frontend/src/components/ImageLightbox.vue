<script setup lang="ts">
import { onMounted, onBeforeUnmount } from "vue";

const props = defineProps<{
  src: string;
  filename?: string | null;
}>();

const emit = defineEmits<{
  close: [];
}>();

function onKey(event: KeyboardEvent) {
  if (event.key === "Escape") emit("close");
}

onMounted(() => {
  document.addEventListener("keydown", onKey);
  document.body.style.overflow = "hidden";
});

onBeforeUnmount(() => {
  document.removeEventListener("keydown", onKey);
  document.body.style.overflow = "";
});
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-[9999] flex flex-col bg-black/90"
      role="dialog"
      aria-modal="true"
      aria-label="Invoice full-screen preview"
    >
      <!-- Top bar -->
      <div
        class="flex shrink-0 items-center justify-between gap-4 border-b border-white/10 bg-black/50 px-4 py-3 sm:px-6"
      >
        <div class="min-w-0">
          <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-teal-300/90">
            Full screen preview
          </p>
          <p class="truncate text-sm font-medium text-white/90">
            {{ props.filename || "Invoice image" }}
          </p>
        </div>
        <button
          type="button"
          class="shrink-0 rounded-sm bg-white px-4 py-2 text-xs font-bold uppercase tracking-[0.12em] text-slate-900 transition hover:bg-teal-50"
          @click="emit('close')"
        >
          Close ✕
        </button>
      </div>

      <!-- Image fills remaining viewport -->
      <button
        type="button"
        class="flex min-h-0 flex-1 cursor-zoom-out items-center justify-center p-3 sm:p-6"
        aria-label="Close preview"
        @click="emit('close')"
      >
        <img
          :src="props.src"
          :alt="props.filename || 'Invoice'"
          class="max-h-full max-w-full object-contain shadow-2xl"
          @click.stop
        />
      </button>

      <p class="shrink-0 pb-3 text-center text-xs text-white/50">
        Esc · click outside image · or Close
      </p>
    </div>
  </Teleport>
</template>
