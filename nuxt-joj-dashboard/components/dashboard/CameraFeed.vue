<template>
  <div class="panel overflow-hidden h-full flex flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-2.5 border-b border-white/5 shrink-0">
      <div class="flex items-center gap-2">
        <!-- Point clignotant LIVE -->
        <span :class="['w-2 h-2 rounded-full shrink-0', streaming ? 'bg-sn-red pulse' : 'bg-white/20']" />
        <span class="font-mono text-[11px] text-white/70 truncate">
          {{ siteName }}
        </span>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="streaming" class="font-hud text-[10px] text-sn-red tracking-widest">LIVE</span>
        <span v-else class="font-mono text-[10px] text-white/30">HORS LIGNE</span>
        <!-- Timestamp -->
        <span class="font-mono text-[10px] text-white/30 tabular-nums">{{ currentTime }}</span>
      </div>
    </div>

    <!-- Flux vidéo -->
    <div class="relative flex-1 bg-black flex items-center justify-center overflow-hidden">
      <!-- Image MJPEG -->
      <img
        v-if="streamUrl"
        :src="streamUrl"
        class="w-full h-full object-contain"
        @load="onLoad"
        @error="onError"
        alt="Flux caméra"
      />

      <!-- Overlay : pas de flux -->
      <div v-if="!streaming" class="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/80">
        <Icon name="heroicons:video-camera-slash" class="w-10 h-10 text-white/20" />
        <p class="font-mono text-xs text-white/40">Flux caméra non disponible</p>
        <p class="font-mono text-[10px] text-white/25">Configurez une source via le bouton Caméra</p>
        <button
          @click="retry"
          class="flex items-center gap-2 px-3 py-1.5 bg-white/5 border border-white/10 text-white/50 font-mono text-[10px] rounded-lg hover:bg-white/10 transition-colors mt-1"
        >
          <Icon name="heroicons:arrow-path" class="w-3.5 h-3.5" />
          Reconnecter
        </button>
      </div>

      <!-- Overlay zones A/B/C/D (filigrane) -->
      <div v-if="streaming" class="absolute inset-0 pointer-events-none">
        <!-- Lignes de grille -->
        <div class="absolute top-0 bottom-0 left-1/2 w-px bg-white/10" />
        <div class="absolute left-0 right-0 top-1/2 h-px bg-white/10" />
        <!-- Labels zones -->
        <span class="absolute top-2 left-2 font-hud text-[10px] text-white/30">A</span>
        <span class="absolute top-2 right-2 font-hud text-[10px] text-white/30">B</span>
        <span class="absolute bottom-2 left-2 font-hud text-[10px] text-white/30">C</span>
        <span class="absolute bottom-2 right-2 font-hud text-[10px] text-white/30">D</span>
        <!-- Densité par zone -->
        <span
          v-for="(zone, key) in zones"
          :key="key"
          :class="['absolute font-mono text-[10px] font-bold px-1 py-0.5 rounded',
            zone.status === 'critical'  ? 'text-sn-red bg-sn-red/10' :
            zone.status === 'attention' ? 'text-sn-yellow bg-sn-yellow/10' :
                                          'text-sn-green bg-sn-green/10',
            key === 'A' ? 'top-6 left-2' :
            key === 'B' ? 'top-6 right-2' :
            key === 'C' ? 'bottom-6 left-2' :
                          'bottom-6 right-2'
          ]"
        >
          {{ zone.count }} pers · {{ zone.density.toFixed(1) }}/m²
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'

const sitesStore = useSitesStore()
const config     = useRuntimeConfig()

const siteName  = computed(() => sitesStore.site.name)
const zones     = computed(() => sitesStore.site.zones)
const streaming = ref(false)
const retryKey  = ref(0)   // incrémenté pour forcer le rechargement du src

const streamUrl = computed(() =>
  `${config.public.apiUrl}/api/stream?t=${retryKey.value}`
)

const currentTime = ref(dayjs().format('HH:mm:ss'))
useIntervalFn(() => { currentTime.value = dayjs().format('HH:mm:ss') }, 1000)

function onLoad()  { streaming.value = true  }
function onError() { streaming.value = false }

function retry() {
  streaming.value = false
  retryKey.value++
}

// Relance automatiquement si la config change (nouvelle URL caméra)
watch(() => sitesStore.site.name, () => retry())
</script>
