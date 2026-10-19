<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";
import { fetchSampleBlob } from "../api";
import ImageLightbox from "./ImageLightbox.vue";

const emit = defineEmits<{
  "file-ready": [file: File | null];
}>();

const ACCEPTED_TYPES = ["image/png", "image/jpeg", "image/webp", "image/jpg"];

const fileInput = ref<HTMLInputElement | null>(null);
const isDragOver = ref(false);
const justAccepted = ref(false);
const sampleLoading = ref(false);
const localError = ref<string | null>(null);
const lightboxOpen = ref(false);

const currentFile = ref<File | null>(null);
const previewUrl = ref<string | null>(null);

const hasFile = computed(() => currentFile.value !== null);

function revokePreview() {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = null;
  }
}

function pulseAccepted() {
  justAccepted.value = false;
  requestAnimationFrame(() => {
    justAccepted.value = true;
    window.setTimeout(() => {
      justAccepted.value = false;
    }, 450);
  });
}

function acceptFile(file: File) {
  const type = file.type.toLowerCase();
  if (!ACCEPTED_TYPES.includes(type)) {
    localError.value = "Only PNG, JPEG, or WebP images are accepted.";
    return;
  }
  localError.value = null;
  revokePreview();
  currentFile.value = file;
  previewUrl.value = URL.createObjectURL(file);
  pulseAccepted();
  emit("file-ready", file);
}

function clearFile() {
  lightboxOpen.value = false;
  revokePreview();
  currentFile.value = null;
  localError.value = null;
  if (fileInput.value) fileInput.value.value = "";
  emit("file-ready", null);
}

function onInputChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) acceptFile(file);
}

function onDrop(event: DragEvent) {
  isDragOver.value = false;
  const file = event.dataTransfer?.files?.[0];
  if (file) acceptFile(file);
}

function onDragOver(event: DragEvent) {
  event.preventDefault();
  isDragOver.value = true;
}

function onDragLeave() {
  isDragOver.value = false;
}

function openPicker() {
  fileInput.value?.click();
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    openPicker();
  }
}

async function useSample() {
  sampleLoading.value = true;
  localError.value = null;
  try {
    const blob = await fetchSampleBlob();
    const file = new File([blob], "sample_invoice.png", { type: blob.type || "image/png" });
    acceptFile(file);
  } catch (err) {
    localError.value = err instanceof Error ? err.message : "Could not load sample invoice";
  } finally {
    sampleLoading.value = false;
  }
}

onBeforeUnmount(() => {
  revokePreview();
});
</script>

<template>
  <div
    class="group relative rounded-sm border border-[var(--color-line)] bg-white/70 p-5 backdrop-blur-sm transition-shadow"
    :class="{ 'drop-accepted': justAccepted }"
  >
    <div class="mb-4 flex items-center justify-between">
      <h2 class="brand text-xl text-[var(--color-ink-deep)]">Document</h2>
      <span
        v-if="hasFile"
        class="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--color-ink)]"
      >
        Ready
      </span>
    </div>

    <input
      ref="fileInput"
      type="file"
      accept="image/png,image/jpeg,image/webp"
      class="sr-only"
      @change="onInputChange"
    />

    <div
      v-if="!hasFile"
      role="button"
      tabindex="0"
      class="flex min-h-64 cursor-pointer flex-col items-center justify-center gap-3 rounded-sm border-2 border-dashed px-6 py-10 text-center transition-colors"
      :class="
        isDragOver
          ? 'border-[var(--color-ink)] bg-[var(--color-ink)]/[0.06]'
          : 'border-[var(--color-line)] bg-[var(--color-paper)]/60 hover:border-[var(--color-ink)]/60 hover:bg-[var(--color-ink)]/[0.03]'
      "
      @click="openPicker"
      @keydown="onKeydown"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop.prevent="onDrop"
    >
      <svg
        class="h-10 w-10 text-[var(--color-ink)]"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M12 16V4m0 0 4 4m-4-4-4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"
        />
      </svg>
      <div>
        <p class="font-semibold text-[var(--color-slate)]">Drop an invoice image</p>
        <p class="mt-1 text-sm text-slate-500">PNG, JPEG, or WebP · up to 5&nbsp;MB</p>
      </div>
      <div class="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-slate-400">
        <span class="h-px w-8 bg-[var(--color-line)]" />
        or
        <span class="h-px w-8 bg-[var(--color-line)]" />
      </div>
      <button
        type="button"
        class="rounded-sm border border-[var(--color-ink)]/30 bg-white px-4 py-2 text-sm font-semibold text-[var(--color-ink-deep)] shadow-sm transition hover:border-[var(--color-ink)] hover:bg-[var(--color-ink)]/[0.06]"
        :disabled="sampleLoading"
        @click.stop="useSample"
      >
        {{ sampleLoading ? "Loading sample…" : "Use sample invoice" }}
      </button>
    </div>

    <div v-else class="flex flex-col gap-3">
      <button
        type="button"
        class="group/preview relative overflow-hidden rounded-sm border border-[var(--color-line)] bg-[var(--color-slate)]/5 text-left"
        title="Open full-screen preview"
        @click="lightboxOpen = true"
      >
        <img
          :src="previewUrl ?? undefined"
          alt="Invoice preview"
          class="max-h-80 w-full object-contain transition group-hover/preview:opacity-95"
        />
        <span
          class="pointer-events-none absolute bottom-3 right-3 rounded-sm bg-[var(--color-slate)]/80 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-white opacity-90"
        >
          Click to enlarge
        </span>
      </button>
      <div class="flex items-center justify-between gap-3">
        <p class="truncate text-sm text-slate-600">{{ currentFile?.name }}</p>
        <div class="flex shrink-0 gap-2">
          <button
            type="button"
            class="rounded-sm border border-[var(--color-ink)]/30 bg-white px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-deep)] transition hover:border-[var(--color-ink)] hover:bg-[var(--color-ink)]/[0.06]"
            @click="lightboxOpen = true"
          >
            Full screen
          </button>
          <button
            type="button"
            class="rounded-sm border border-[var(--color-line)] bg-white px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-slate-600 transition hover:border-[var(--color-ink)] hover:text-[var(--color-ink-deep)]"
            @click="openPicker"
          >
            Replace
          </button>
          <button
            type="button"
            class="rounded-sm border border-[var(--color-line)] bg-white px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-slate-600 transition hover:border-red-300 hover:text-red-600"
            @click="clearFile"
          >
            Clear
          </button>
        </div>
      </div>
    </div>

    <p v-if="localError" class="mt-3 text-sm font-medium text-red-600">{{ localError }}</p>

    <ImageLightbox
      v-if="lightboxOpen && previewUrl"
      :src="previewUrl"
      :filename="currentFile?.name"
      @close="lightboxOpen = false"
    />
  </div>
</template>
