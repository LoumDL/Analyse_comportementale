<template>
  <header class="flex items-center justify-between px-6 py-3 border-b border-white/5 bg-[#060911]/80 backdrop-blur-sm shrink-0">
    <!-- Left: titre -->
    <div>
      <h1 class="font-hud text-sm text-white/90 tracking-widest uppercase">
        Centre de Commandement Sécurité
      </h1>
      <p class="font-mono text-[10px] mt-0.5 flex items-center gap-2">
        <span class="text-white/40">Jeux Olympiques de la Jeunesse — Dakar 2026</span>
        <!-- Nom du site actif -->
        <span class="text-sn-green/80">·</span>
        <span class="text-sn-green font-semibold truncate max-w-[200px]">{{ siteName }}</span>
      </p>
    </div>

    <!-- Right -->
    <div class="flex items-center gap-5">
      <!-- Total personnes -->
      <div class="text-right">
        <p class="font-mono text-[10px] text-white/40 uppercase tracking-widest">Personnes</p>
        <p class="font-hud text-lg text-sn-green tabular-nums">
          {{ totalPersons.toLocaleString('fr-FR') }}
        </p>
      </div>

      <!-- Bouton config caméra -->
      <button
        @click="showConfig = true"
        class="flex items-center gap-2 px-3 py-1.5 bg-white/5 border border-white/10 text-white/60 font-mono text-xs rounded-lg hover:bg-white/10 hover:text-white/90 hover:border-sn-green/40 transition-all"
        title="Configurer la caméra"
      >
        <Icon name="heroicons:video-camera" class="w-4 h-4" />
        <span class="hidden sm:inline">Caméra</span>
      </button>

      <!-- WS dot -->
      <div class="flex items-center gap-1.5">
        <span :class="['w-2 h-2 rounded-full pulse', wsColor]" />
        <span class="font-mono text-[10px] text-white/50">{{ wsLabel }}</span>
      </div>

      <!-- Horloge -->
      <div class="font-hud text-xl text-sn-yellow tabular-nums tracking-widest">
        {{ currentTime }}
      </div>

      <!-- Langue -->
      <div class="flex gap-1">
        <button
          v-for="lang in ['fr','en']"
          :key="lang"
          @click="uiStore.setLocale(lang as 'fr'|'en')"
          :class="[
            'font-mono text-xs px-2 py-1 rounded transition-colors uppercase',
            uiStore.locale === lang
              ? 'bg-sn-green/20 text-sn-green border border-sn-green/30'
              : 'text-white/40 hover:text-white/70',
          ]"
        >
          {{ lang }}
        </button>
      </div>
    </div>
  </header>

  <!-- Modal configuration -->
  <SiteConfigModal :show="showConfig" @close="showConfig = false" @saved="onSaved" />
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import SiteConfigModal from './SiteConfigModal.vue'

const uiStore    = useUiStore()
const sitesStore = useSitesStore()

const totalPersons = computed(() => sitesStore.totalPersons)
const siteName     = computed(() => sitesStore.site.name)
const showConfig   = ref(false)

const currentTime = ref(dayjs().format('HH:mm:ss'))
useIntervalFn(() => { currentTime.value = dayjs().format('HH:mm:ss') }, 1000)

const wsStatus = computed(() => uiStore.wsStatus)
const wsColor  = computed(() => ({ connected:'bg-sn-green', connecting:'bg-sn-yellow', disconnected:'bg-sn-red' }[wsStatus.value]))
const wsLabel  = computed(() => ({ connected:'LIVE', connecting:'…', disconnected:'OFF' }[wsStatus.value]))

function onSaved(cfg: any) {
  console.log('[INFO] Config appliquée :', cfg)
}
</script>
