<template>
  <div class="h-full flex flex-col gap-4">

    <!-- En-tête -->
    <div class="flex items-center justify-between shrink-0">
      <div>
        <h1 class="font-hud text-base text-white/85 tracking-wide">Gestion des Caméras</h1>
        <p class="font-mono text-[10px] text-white/30 mt-0.5">
          {{ cameras.length }} caméra{{ cameras.length > 1 ? 's' : '' }} configurée{{ cameras.length > 1 ? 's' : '' }}
          · {{ activeCount }} active{{ activeCount > 1 ? 's' : '' }}
        </p>
      </div>
      <button
        @click="openModal()"
        class="flex items-center gap-2 px-4 py-2 bg-sn-green/15 border border-sn-green/30 text-sn-green font-mono text-xs rounded-lg hover:bg-sn-green/25 transition-colors"
      >
        <Icon name="heroicons:plus" class="w-4 h-4" />
        Ajouter une caméra
      </button>
    </div>

    <!-- Corps -->
    <div class="flex-1 min-h-0 grid grid-cols-3 gap-4">

      <!-- Grille caméras -->
      <div class="col-span-2 flex flex-col gap-3 overflow-y-auto">

        <!-- Vide -->
        <div v-if="!cameras.length" class="panel flex-1 flex flex-col items-center justify-center gap-3 text-center py-16">
          <Icon name="heroicons:video-camera-slash" class="w-12 h-12 text-white/15" />
          <p class="font-mono text-sm text-white/30">Aucune caméra configurée</p>
          <button @click="openModal()" class="text-sn-green font-mono text-xs hover:underline">+ Ajouter la première</button>
        </div>

        <!-- Carte caméra -->
        <div
          v-for="cam in cameras"
          :key="cam.id"
          class="panel p-4 flex items-start gap-4 hover:border-white/12 transition-colors"
        >
          <!-- Icône statut -->
          <div :class="[
            'w-10 h-10 rounded-xl flex items-center justify-center shrink-0',
            cam.active ? 'bg-sn-green/10 border border-sn-green/20' : 'bg-white/4 border border-white/8',
          ]">
            <Icon
              name="heroicons:video-camera"
              :class="['w-5 h-5', cam.active ? 'text-sn-green' : 'text-white/25']"
            />
          </div>

          <!-- Infos -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="font-mono text-sm text-white/80 font-semibold">{{ cam.name }}</span>
              <!-- Status dot -->
              <span
                :class="[
                  'w-1.5 h-1.5 rounded-full shrink-0',
                  cam.status === 'online'  ? 'bg-sn-green pulse' :
                  cam.status === 'offline' ? 'bg-sn-red' :
                                             'bg-white/30',
                ]"
              />
              <span :class="['font-mono text-[9px]',
                cam.status === 'online'  ? 'text-sn-green' :
                cam.status === 'offline' ? 'text-sn-red/80' :
                                           'text-white/30']">
                {{ cam.status === 'online' ? 'LIVE' : cam.status === 'offline' ? 'OFF' : '—' }}
              </span>
              <span v-if="!cam.active" class="font-mono text-[9px] text-white/25 border border-white/10 px-1.5 rounded">INACTIF</span>
            </div>

            <!-- Source -->
            <p class="font-mono text-[10px] text-white/35 truncate mb-2">
              <span class="text-white/20 mr-1">↗</span>
              {{ cam.source || 'Aucune source configurée' }}
            </p>

            <!-- Zones assignées -->
            <div class="flex items-center gap-1.5">
              <span class="font-mono text-[9px] text-white/25 mr-1">Zones :</span>
              <span
                v-for="z in (cam.zones.length ? cam.zones : ['—'])"
                :key="z"
                :class="[
                  'font-mono text-[10px] px-2 py-0.5 rounded border',
                  cam.zones.length
                    ? 'border-sn-green/25 bg-sn-green/8 text-sn-green'
                    : 'border-white/8 text-white/20',
                ]"
              >{{ z }}</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 shrink-0">
            <button
              v-if="cam.active && cam.source"
              @click="previewCam = cam"
              class="p-2 text-white/30 hover:text-sn-green hover:bg-sn-green/8 rounded-lg transition-colors"
              title="Voir le flux"
            >
              <Icon name="heroicons:play-circle" class="w-4 h-4" />
            </button>
            <button
              @click="openModal(cam)"
              class="p-2 text-white/30 hover:text-white/70 hover:bg-white/5 rounded-lg transition-colors"
              title="Modifier"
            >
              <Icon name="heroicons:pencil-square" class="w-4 h-4" />
            </button>
            <button
              @click="confirmDelete(cam)"
              class="p-2 text-white/20 hover:text-sn-red hover:bg-sn-red/8 rounded-lg transition-colors"
              title="Supprimer"
            >
              <Icon name="heroicons:trash" class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <!-- Panneau droit : plan de zones -->
      <div class="flex flex-col gap-3">
        <!-- Plan SVG -->
        <div class="panel p-4 flex-1 flex flex-col">
          <p class="font-mono text-[10px] text-white/40 uppercase tracking-widest mb-3">
            Plan des zones · couverture caméra
          </p>
          <div class="flex-1 relative">
            <svg viewBox="0 0 320 280" class="w-full h-full" style="max-height: 320px">
              <!-- Fond -->
              <rect width="320" height="280" fill="rgba(255,255,255,0.02)" rx="8" />

              <!-- Zone A -->
              <g @mouseenter="hoveredZone='A'" @mouseleave="hoveredZone=''" style="cursor:pointer">
                <rect x="10" y="10" width="140" height="120" rx="6"
                  :fill="zoneFill('A')" :stroke="zoneStroke('A')" stroke-width="1.5" />
                <text x="80" y="55" text-anchor="middle" class="zone-label" :fill="zoneLabelColor('A')">Zone A</text>
                <text x="80" y="72" text-anchor="middle" font-family="monospace" font-size="9" fill="rgba(255,255,255,0.4)">
                  {{ camerasForZone('A').join(', ') || '—' }}
                </text>
                <circle v-if="hasCamera('A')" cx="122" cy="22" r="5" fill="rgba(0,133,63,0.6)" />
                <text v-if="hasCamera('A')" x="122" y="26" text-anchor="middle" font-size="7" fill="white">📹</text>
              </g>

              <!-- Zone B -->
              <g @mouseenter="hoveredZone='B'" @mouseleave="hoveredZone=''" style="cursor:pointer">
                <rect x="170" y="10" width="140" height="120" rx="6"
                  :fill="zoneFill('B')" :stroke="zoneStroke('B')" stroke-width="1.5" />
                <text x="240" y="55" text-anchor="middle" class="zone-label" :fill="zoneLabelColor('B')">Zone B</text>
                <text x="240" y="72" text-anchor="middle" font-family="monospace" font-size="9" fill="rgba(255,255,255,0.4)">
                  {{ camerasForZone('B').join(', ') || '—' }}
                </text>
                <circle v-if="hasCamera('B')" cx="282" cy="22" r="5" fill="rgba(0,133,63,0.6)" />
                <text v-if="hasCamera('B')" x="282" y="26" text-anchor="middle" font-size="7" fill="white">📹</text>
              </g>

              <!-- Zone C -->
              <g @mouseenter="hoveredZone='C'" @mouseleave="hoveredZone=''" style="cursor:pointer">
                <rect x="10" y="150" width="140" height="120" rx="6"
                  :fill="zoneFill('C')" :stroke="zoneStroke('C')" stroke-width="1.5" />
                <text x="80" y="195" text-anchor="middle" class="zone-label" :fill="zoneLabelColor('C')">Zone C</text>
                <text x="80" y="212" text-anchor="middle" font-family="monospace" font-size="9" fill="rgba(255,255,255,0.4)">
                  {{ camerasForZone('C').join(', ') || '—' }}
                </text>
                <circle v-if="hasCamera('C')" cx="122" cy="162" r="5" fill="rgba(0,133,63,0.6)" />
                <text v-if="hasCamera('C')" x="122" y="166" text-anchor="middle" font-size="7" fill="white">📹</text>
              </g>

              <!-- Zone D -->
              <g @mouseenter="hoveredZone='D'" @mouseleave="hoveredZone=''" style="cursor:pointer">
                <rect x="170" y="150" width="140" height="120" rx="6"
                  :fill="zoneFill('D')" :stroke="zoneStroke('D')" stroke-width="1.5" />
                <text x="240" y="195" text-anchor="middle" class="zone-label" :fill="zoneLabelColor('D')">Zone D</text>
                <text x="240" y="212" text-anchor="middle" font-family="monospace" font-size="9" fill="rgba(255,255,255,0.4)">
                  {{ camerasForZone('D').join(', ') || '—' }}
                </text>
                <circle v-if="hasCamera('D')" cx="282" cy="162" r="5" fill="rgba(0,133,63,0.6)" />
                <text v-if="hasCamera('D')" x="282" y="166" text-anchor="middle" font-size="7" fill="white">📹</text>
              </g>

              <!-- Flèches d'entrée/sortie -->
              <path d="M155 70 L165 70" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" marker-end="url(#arrow)" />
              <path d="M155 210 L165 210" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" marker-end="url(#arrow)" />
              <path d="M80 135 L80 145" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" marker-end="url(#arrow)" />
              <path d="M240 135 L240 145" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" marker-end="url(#arrow)" />
              <defs>
                <marker id="arrow" viewBox="0 0 6 6" refX="3" refY="3" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M0,0 L0,6 L6,3 z" fill="rgba(255,255,255,0.2)" />
                </marker>
              </defs>
            </svg>
          </div>

          <!-- Légende -->
          <div class="flex items-center gap-4 mt-2 border-t border-white/5 pt-2">
            <div class="flex items-center gap-1.5">
              <div class="w-3 h-3 rounded bg-sn-green/20 border border-sn-green/40" />
              <span class="font-mono text-[9px] text-white/40">Couverte</span>
            </div>
            <div class="flex items-center gap-1.5">
              <div class="w-3 h-3 rounded bg-white/4 border border-white/8" />
              <span class="font-mono text-[9px] text-white/40">Non couverte</span>
            </div>
          </div>
        </div>

        <!-- Stats rapides -->
        <div class="panel p-4">
          <p class="font-mono text-[10px] text-white/40 uppercase tracking-widest mb-3">Couverture</p>
          <div class="space-y-2">
            <div v-for="z in allZones" :key="z" class="flex items-center gap-2">
              <span class="font-mono text-xs text-white/50 w-14">Zone {{ z }}</span>
              <div class="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                <div
                  :class="['h-full rounded-full transition-all', hasCamera(z) ? 'bg-sn-green' : 'bg-white/10']"
                  :style="{ width: hasCamera(z) ? '100%' : '0%' }"
                />
              </div>
              <span :class="['font-mono text-[9px] w-16 text-right', hasCamera(z) ? 'text-sn-green' : 'text-white/20']">
                {{ camerasForZone(z).join(', ') || 'Aucune' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal ajout/édition -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="closeModal" />
          <div class="relative bg-[#0D1120] border border-white/10 rounded-2xl w-full max-w-md shadow-2xl">

            <!-- En-tête modal -->
            <div class="flex items-center justify-between px-6 py-4 border-b border-white/8">
              <h2 class="font-hud text-sm text-white/85">
                {{ editingId ? 'Modifier la caméra' : 'Nouvelle caméra' }}
              </h2>
              <button @click="closeModal" class="text-white/30 hover:text-white/70 transition-colors">
                <Icon name="heroicons:x-mark" class="w-5 h-5" />
              </button>
            </div>

            <!-- Corps modal -->
            <div class="px-6 py-5 space-y-5">

              <!-- Nom -->
              <div>
                <label class="block font-mono text-[10px] text-white/35 uppercase tracking-widest mb-1.5">
                  Nom de la caméra
                </label>
                <input
                  v-model="form.name"
                  type="text"
                  placeholder="ex. Entrée principale"
                  @blur="touched.name = true"
                  class="w-full bg-white/4 border border-white/8 text-white/85 font-mono text-sm px-4 py-2.5 rounded-lg focus:outline-none focus:border-sn-green/40 transition-all placeholder:text-white/15"
                  :class="{ 'border-sn-red/50': touched.name && !form.name.trim() }"
                />
                <p v-if="touched.name && !form.name.trim()" class="font-mono text-[10px] text-sn-red/80 mt-1">
                  Le nom est requis
                </p>
              </div>

              <!-- Source -->
              <div>
                <label class="block font-mono text-[10px] text-white/35 uppercase tracking-widest mb-1.5">
                  Source (URL ou index webcam)
                </label>
                <div class="relative">
                  <input
                    v-model="form.source"
                    type="text"
                    placeholder="http://192.168.1.100/stream"
                    @blur="touched.source = true"
                    class="w-full bg-white/4 border border-white/8 text-white/85 font-mono text-xs px-4 py-2.5 pr-10 rounded-lg focus:outline-none transition-all placeholder:text-white/15"
                    :class="sourceClass"
                  />
                  <span class="absolute right-3 top-1/2 -translate-y-1/2 text-sm">
                    {{ sourceIcon }}
                  </span>
                </div>
                <p v-if="touched.source && sourceType === 'invalid'" class="font-mono text-[10px] text-sn-red/80 mt-1">
                  Format invalide — HTTP(S), RTSP, ou index numérique
                </p>
                <p v-else-if="touched.source && sourceType !== 'empty'" class="font-mono text-[10px] text-sn-green/70 mt-1">
                  Source {{ sourceType }} valide
                </p>
              </div>

              <!-- Zones assignées -->
              <div>
                <label class="block font-mono text-[10px] text-white/35 uppercase tracking-widest mb-2">
                  Zones couvertes
                </label>
                <div class="flex gap-2">
                  <button
                    v-for="z in allZones"
                    :key="z"
                    type="button"
                    @click="toggleZone(z)"
                    :class="[
                      'flex-1 py-2 rounded-lg border font-mono text-xs transition-all',
                      form.zones.includes(z)
                        ? 'bg-sn-green/15 border-sn-green/40 text-sn-green'
                        : 'bg-white/3 border-white/8 text-white/35 hover:border-white/20 hover:text-white/55',
                    ]"
                  >
                    {{ z }}
                  </button>
                </div>
              </div>

              <!-- Activer -->
              <div class="flex items-center justify-between py-2">
                <div>
                  <p class="font-mono text-xs text-white/70">Caméra active</p>
                  <p class="font-mono text-[10px] text-white/30 mt-0.5">Inclure dans la surveillance en temps réel</p>
                </div>
                <button
                  type="button"
                  @click="form.active = !form.active"
                  :class="[
                    'relative w-11 h-6 rounded-full border transition-all duration-200',
                    form.active
                      ? 'bg-sn-green/30 border-sn-green/50'
                      : 'bg-white/5 border-white/15',
                  ]"
                >
                  <span
                    :class="[
                      'absolute top-0.5 w-5 h-5 rounded-full transition-all duration-200',
                      form.active ? 'left-[22px] bg-sn-green' : 'left-0.5 bg-white/30',
                    ]"
                  />
                </button>
              </div>
            </div>

            <!-- Pied modal -->
            <div class="px-6 py-4 border-t border-white/8 flex gap-3 justify-end">
              <button
                @click="closeModal"
                class="px-4 py-2 font-mono text-xs text-white/40 hover:text-white/70 transition-colors"
              >
                Annuler
              </button>
              <button
                @click="saveCamera"
                :disabled="!canSave"
                class="px-5 py-2 bg-sn-green/15 border border-sn-green/30 text-sn-green font-mono text-xs rounded-lg hover:bg-sn-green/25 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {{ editingId ? 'Enregistrer' : 'Ajouter' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Modal suppression -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="deleteTarget" class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="deleteTarget = null" />
          <div class="relative bg-[#0D1120] border border-white/10 rounded-2xl w-full max-w-sm shadow-2xl p-6">
            <Icon name="heroicons:exclamation-triangle" class="w-8 h-8 text-sn-red/80 mb-3" />
            <h3 class="font-mono text-sm text-white/80 mb-1">Supprimer cette caméra ?</h3>
            <p class="font-mono text-[10px] text-white/35 mb-5">« {{ deleteTarget?.name }} » sera définitivement supprimée.</p>
            <div class="flex gap-3 justify-end">
              <button @click="deleteTarget = null" class="px-4 py-2 font-mono text-xs text-white/40 hover:text-white/70 transition-colors">
                Annuler
              </button>
              <button @click="doDelete" class="px-5 py-2 bg-sn-red/15 border border-sn-red/30 text-sn-red font-mono text-xs rounded-lg hover:bg-sn-red/25 transition-colors">
                Supprimer
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Modal aperçu flux -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="previewCam" class="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" @click="previewCam = null" />
          <div class="relative bg-[#0D1120] border border-white/10 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden">
            <div class="flex items-center justify-between px-4 py-3 border-b border-white/8">
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-sn-green pulse" />
                <span class="font-mono text-xs text-white/70">{{ previewCam?.name }}</span>
              </div>
              <button @click="previewCam = null" class="text-white/30 hover:text-white/70">
                <Icon name="heroicons:x-mark" class="w-5 h-5" />
              </button>
            </div>
            <div class="bg-black flex items-center justify-center" style="height: 50vh">
              <img
                v-if="previewCam"
                :src="previewCam.source"
                class="max-w-full max-h-full object-contain"
                alt="Flux caméra"
                @error="streamError = true"
              />
              <div v-if="streamError" class="text-center">
                <Icon name="heroicons:video-camera-slash" class="w-12 h-12 text-white/15 mb-2" />
                <p class="font-mono text-xs text-white/30">Flux indisponible</p>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<script setup lang="ts">
import type { Camera } from '~/stores/cameras'

const camerasStore = useCamerasStore()
const { cameras }  = storeToRefs(camerasStore)

const allZones = ['A', 'B', 'C', 'D']

const activeCount  = computed(() => cameras.value.filter(c => c.active).length)
const hoveredZone  = ref('')
const previewCam   = ref<Camera | null>(null)
const deleteTarget = ref<Camera | null>(null)
const streamError  = ref(false)

watch(previewCam, () => { streamError.value = false })

// --- Helpers plan SVG ---
function camerasForZone(z: string): string[] {
  return cameras.value.filter(c => c.zones.includes(z)).map(c => c.name)
}
function hasCamera(z: string): boolean { return camerasForZone(z).length > 0 }

function zoneFill(z: string): string {
  if (hoveredZone.value === z) return 'rgba(255,255,255,0.05)'
  return hasCamera(z) ? 'rgba(0,133,63,0.08)' : 'rgba(255,255,255,0.02)'
}
function zoneStroke(z: string): string {
  if (hoveredZone.value === z) return 'rgba(255,255,255,0.2)'
  return hasCamera(z) ? 'rgba(0,133,63,0.35)' : 'rgba(255,255,255,0.08)'
}
function zoneLabelColor(z: string): string {
  return hasCamera(z) ? 'rgba(0,200,80,0.8)' : 'rgba(255,255,255,0.3)'
}

// --- Modal ---
const showModal = ref(false)
const editingId = ref<string | null>(null)

const form    = reactive({ name: '', source: '', zones: [] as string[], active: true })
const touched = reactive({ name: false, source: false })

function openModal(cam?: Camera) {
  if (cam) {
    editingId.value = cam.id
    form.name    = cam.name
    form.source  = cam.source
    form.zones   = [...cam.zones]
    form.active  = cam.active
  } else {
    editingId.value = null
    form.name   = ''
    form.source = ''
    form.zones  = []
    form.active = true
  }
  touched.name   = false
  touched.source = false
  showModal.value = true
}

function closeModal() { showModal.value = false }

function toggleZone(z: string) {
  const idx = form.zones.indexOf(z)
  if (idx >= 0) form.zones.splice(idx, 1)
  else form.zones.push(z)
}

// Source validation
const sourceType = computed<'webcam' | 'http' | 'rtsp' | 'invalid' | 'empty'>(() => {
  const s = form.source.trim()
  if (!s) return 'empty'
  if (/^\d+$/.test(s)) return 'webcam'
  if (/^https?:\/\//i.test(s)) return 'http'
  if (/^rtsp:\/\//i.test(s)) return 'rtsp'
  return 'invalid'
})

const sourceIcon = computed(() => ({
  webcam:  '🎥',
  http:    '✅',
  rtsp:    '✅',
  invalid: '❌',
  empty:   '',
}[sourceType.value]))

const sourceClass = computed(() => ({
  'focus:border-sn-green/40 border-sn-green/30': sourceType.value !== 'empty' && sourceType.value !== 'invalid',
  'border-sn-red/40':   touched.source && sourceType.value === 'invalid',
  'border-white/8':     sourceType.value === 'empty' || (!touched.source && sourceType.value === 'invalid'),
}))

const canSave = computed(() =>
  form.name.trim() &&
  (sourceType.value !== 'invalid')
)

function saveCamera() {
  if (!canSave.value) return
  const payload = { name: form.name.trim(), source: form.source.trim(), zones: [...form.zones], active: form.active }
  if (editingId.value) camerasStore.updateCamera(editingId.value, payload)
  else camerasStore.addCamera(payload)
  closeModal()
}

function confirmDelete(cam: Camera) { deleteTarget.value = cam }
function doDelete() {
  if (deleteTarget.value) camerasStore.removeCamera(deleteTarget.value.id)
  deleteTarget.value = null
}

onMounted(() => camerasStore.restore())

useHead({ title: 'Caméras — JOJ Dakar 2026' })
</script>

<style scoped>
.zone-label { font-family: 'Orbitron', sans-serif; font-size: 13px; font-weight: 600; }
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
