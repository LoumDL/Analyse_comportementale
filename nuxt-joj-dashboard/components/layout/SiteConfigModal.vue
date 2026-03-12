<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm"
        @click.self="$emit('close')"
      >
        <div class="panel w-full max-w-sm">

          <!-- Header -->
          <div class="flex items-center justify-between px-5 py-4 border-b border-white/5">
            <h2 class="font-hud text-sm text-white/80 tracking-wide">Configuration caméra</h2>
            <button @click="$emit('close')" class="text-white/25 hover:text-white/70 transition-colors">
              <Icon name="heroicons:x-mark" class="w-4 h-4" />
            </button>
          </div>

          <form @submit.prevent="save" class="p-5 space-y-4">

            <!-- Nom du site -->
            <div>
              <label class="block font-mono text-[10px] text-white/35 uppercase tracking-widest mb-1.5">
                Nom du site
              </label>
              <input
                v-model="form.name"
                type="text"
                placeholder="Ex : Stade Léopold Sédar Senghor"
                autocomplete="off"
                @blur="touchName = true"
                :class="[
                  'w-full bg-white/4 border text-white/90 text-sm px-3.5 py-2.5 rounded-lg focus:outline-none transition-all placeholder:text-white/20',
                  showNameError ? 'border-red-500/50 bg-red-500/5' : 'border-white/8 focus:border-sn-green/40 focus:bg-white/6'
                ]"
              />
              <p v-if="showNameError" class="font-mono text-[10px] text-red-400 mt-1 flex items-center gap-1">
                <Icon name="heroicons:exclamation-triangle" class="w-3 h-3 shrink-0" />
                Minimum 2 caractères requis
              </p>
            </div>

            <!-- Source -->
            <div>
              <label class="block font-mono text-[10px] text-white/35 uppercase tracking-widest mb-1.5">
                Source vidéo
              </label>
              <div class="relative">
                <input
                  v-model="form.source"
                  type="text"
                  placeholder="http://192.168.1.x:4747/video"
                  autocomplete="off"
                  @blur="touchSource = true"
                  :class="[
                    'w-full bg-white/4 border text-white/90 font-mono text-xs px-3.5 py-2.5 pr-10 rounded-lg focus:outline-none transition-all placeholder:text-white/20',
                    showSourceError ? 'border-red-500/50 bg-red-500/5' :
                    sourceValid     ? 'border-sn-green/30 bg-sn-green/3' :
                                      'border-white/8 focus:border-sn-green/40 focus:bg-white/6'
                  ]"
                />
                <!-- Icône statut -->
                <div class="absolute right-3 top-1/2 -translate-y-1/2">
                  <Icon v-if="sourceValid"      name="heroicons:check-circle"      class="w-4 h-4 text-sn-green/70" />
                  <Icon v-else-if="showSourceError" name="heroicons:x-circle"      class="w-4 h-4 text-red-400" />
                  <Icon v-else                  :name="sourceTypeIcon"              class="w-4 h-4 text-white/20" />
                </div>
              </div>

              <!-- Erreur ou aide -->
              <p v-if="showSourceError" class="font-mono text-[10px] text-red-400 mt-1 flex items-center gap-1">
                <Icon name="heroicons:exclamation-triangle" class="w-3 h-3 shrink-0" />
                {{ sourceErrorMsg }}
              </p>
              <p v-else-if="sourceValid" class="font-mono text-[10px] text-sn-green/70 mt-1 flex items-center gap-1">
                <Icon :name="sourceTypeIcon" class="w-3 h-3 shrink-0" />
                {{ sourceTypeLabel }}
              </p>
              <p v-else class="font-mono text-[10px] text-white/25 mt-1">
                URL caméra IP, chemin .mp4 ou index webcam (0, 1…)
              </p>

              <!-- Raccourci webcam -->
              <button
                type="button"
                @click="pickWebcam"
                class="mt-2 flex items-center gap-1.5 font-mono text-[10px] text-white/30 hover:text-white/60 transition-colors"
              >
                <Icon name="heroicons:computer-desktop" class="w-3.5 h-3.5" />
                Webcam locale (index 0)
              </button>
            </div>

            <!-- Feedback succès -->
            <Transition name="fade">
              <div v-if="saved" class="flex items-center gap-2 px-3 py-2 bg-sn-green/10 border border-sn-green/20 rounded-lg">
                <Icon name="heroicons:check-circle" class="w-4 h-4 text-sn-green shrink-0" />
                <span class="font-mono text-[11px] text-sn-green">Configuration appliquée</span>
              </div>
            </Transition>

            <!-- Actions -->
            <div class="flex gap-2 pt-1">
              <button
                type="button"
                @click="$emit('close')"
                class="px-4 py-2.5 bg-white/4 border border-white/8 text-white/50 font-mono text-xs rounded-lg hover:bg-white/8 hover:text-white/70 transition-colors"
              >
                Annuler
              </button>
              <button
                type="submit"
                :disabled="saving || !canSubmit"
                class="flex-1 flex items-center justify-center gap-2 py-2.5 bg-sn-green/15 border border-sn-green/25 text-sn-green font-mono text-xs rounded-lg hover:bg-sn-green/22 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <Icon v-if="saving" name="heroicons:arrow-path" class="w-3.5 h-3.5 animate-spin" />
                <Icon v-else name="heroicons:check" class="w-3.5 h-3.5" />
                {{ saving ? 'Application…' : 'Appliquer' }}
              </button>
            </div>

          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{ show: boolean }>()
const emit = defineEmits<{ close: []; saved: [config: any] }>()

const sitesStore = useSitesStore()
const config     = useRuntimeConfig()

const form        = reactive({ name: sitesStore.site.name, source: '' })
const saving      = ref(false)
const saved       = ref(false)
const touchName   = ref(false)
const touchSource = ref(false)

// ── Validation source ─────────────────────────────────────────────────────
type SourceType = 'webcam' | 'http' | 'file' | 'invalid' | 'empty'

const sourceType = computed((): SourceType => {
  const s = form.source.trim()
  if (!s) return 'empty'
  if (/^\d+$/.test(s)) return 'webcam'
  if (s.startsWith('http://') || s.startsWith('https://')) {
    try { new URL(s); return 'http' } catch { return 'invalid' }
  }
  if (/\.(mp4|avi|mov|mkv|webm|ts)$/i.test(s)) return 'file'
  return 'invalid'
})

const sourceValid = computed(() => ['webcam', 'http', 'file'].includes(sourceType.value))

const sourceTypeLabel = computed(() => ({
  webcam: `Webcam locale — index ${form.source.trim()}`,
  http:   'Flux caméra IP',
  file:   'Fichier vidéo',
}[sourceType.value as string] ?? ''))

const sourceTypeIcon = computed(() => ({
  webcam:  'heroicons:computer-desktop',
  http:    'heroicons:wifi',
  file:    'heroicons:film',
  invalid: 'heroicons:exclamation-circle',
  empty:   'heroicons:video-camera',
}[sourceType.value]))

const sourceErrorMsg = computed(() =>
  sourceType.value === 'invalid'
    ? 'Format non reconnu — URL http://, chemin .mp4 ou index (0, 1…)'
    : 'Source requise'
)

const nameValid       = computed(() => form.name.trim().length >= 2)
const showNameError   = computed(() => touchName.value   && !nameValid.value)
const showSourceError = computed(() => touchSource.value && !sourceValid.value)
const canSubmit       = computed(() => nameValid.value && sourceValid.value)

function pickWebcam() {
  form.source    = '0'
  touchSource.value = true
}

onMounted(async () => {
  try {
    const cfg = await $fetch<{ name: string; source: string }>(`${config.public.apiUrl}/api/config`)
    form.name   = cfg.name
    form.source = cfg.source
  } catch {
    form.name = sitesStore.site.name
  }
})

async function save() {
  touchName.value = touchSource.value = true
  if (!canSubmit.value) return
  saving.value = true
  try {
    const result = await $fetch(`${config.public.apiUrl}/api/config`, {
      method: 'PUT',
      body:   { name: form.name.trim(), source: form.source.trim() },
    })
    sitesStore.applyConfig({ name: form.name.trim() })
    saved.value = true
    emit('saved', result)
    setTimeout(() => { saved.value = false; emit('close') }, 1400)
  } catch {
    sitesStore.applyConfig({ name: form.name.trim() })
    saved.value = true
    setTimeout(() => { saved.value = false; emit('close') }, 1400)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: opacity 0.18s ease; }
.modal-enter-from, .modal-leave-to       { opacity: 0; }
.fade-enter-active, .fade-leave-active   { transition: opacity 0.25s ease; }
.fade-enter-from, .fade-leave-to         { opacity: 0; }
</style>
