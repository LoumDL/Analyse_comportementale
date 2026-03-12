<template>
  <div class="h-full flex gap-4">
    <!-- Liste -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Filtres -->
      <div class="panel p-4 mb-4 shrink-0 flex flex-wrap gap-3 items-center">
        <!-- Recherche -->
        <div class="relative flex-1 min-w-[200px]">
          <Icon name="heroicons:magnifying-glass" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
          <input
            v-model="filterState.searchQuery.value"
            placeholder="Rechercher…"
            class="w-full bg-white/5 border border-white/10 text-white/80 font-mono text-xs pl-9 pr-3 py-2 rounded-lg focus:outline-none focus:border-sn-green/50"
          />
        </div>

        <!-- Niveau -->
        <select v-model="filterState.filterLevel.value" class="bg-white/5 border border-white/10 text-white/80 font-mono text-xs px-3 py-2 rounded-lg focus:outline-none">
          <option value="all">Tous niveaux</option>
          <option value="critical">Critique</option>
          <option value="warning">Alerte</option>
          <option value="info">Info</option>
        </select>

        <!-- Site -->
        <select v-model="filterState.filterSite.value" class="bg-white/5 border border-white/10 text-white/80 font-mono text-xs px-3 py-2 rounded-lg focus:outline-none">
          <option value="all">Tous sites</option>
          <option v-for="s in sitesStore.sites" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>

        <!-- Tri -->
        <select v-model="filterState.sortBy.value" class="bg-white/5 border border-white/10 text-white/80 font-mono text-xs px-3 py-2 rounded-lg focus:outline-none">
          <option value="time">Par heure</option>
          <option value="level">Par gravité</option>
        </select>

        <!-- Export -->
        <button
          @click="filterState.exportCsv()"
          class="flex items-center gap-2 px-3 py-2 bg-sn-green/10 border border-sn-green/20 text-sn-green font-mono text-xs rounded-lg hover:bg-sn-green/20 transition-colors ml-auto"
        >
          <Icon name="heroicons:arrow-down-tray" class="w-4 h-4" />
          Export CSV
        </button>
      </div>

      <!-- Tableau -->
      <div class="panel flex-1 overflow-hidden flex flex-col">
        <div class="grid grid-cols-[auto_auto_1fr_auto_1fr_auto_auto] gap-x-4 px-4 py-2 border-b border-white/5 text-[10px] font-mono text-white/30 uppercase tracking-wider shrink-0">
          <span>Heure</span>
          <span>Niveau</span>
          <span>Site</span>
          <span>Zone</span>
          <span>Anomalie</span>
          <span>Durée</span>
          <span>Action</span>
        </div>
        <div class="flex-1 overflow-y-auto">
          <div
            v-for="alert in filterState.filtered.value"
            :key="alert.id"
            :class="[
              'grid grid-cols-[auto_auto_1fr_auto_1fr_auto_auto] gap-x-4 px-4 py-3 border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer items-center text-xs',
              selectedId === alert.id ? 'bg-white/5' : '',
            ]"
            @click="select(alert)"
          >
            <span class="font-mono text-white/60 tabular-nums">{{ formatTime(alert.timestamp) }}</span>
            <AlertBadge :level="alert.level" />
            <span class="font-body text-white/70 truncate">{{ alert.siteName }}</span>
            <span class="font-mono text-white/60">{{ alert.zone }}</span>
            <span class="font-body text-white/70 truncate">{{ alert.anomalyType }}</span>
            <span class="font-mono text-white/50">{{ alert.duration ? `${alert.duration}min` : '—' }}</span>
            <button
              @click.stop="alertsStore.openAlert(alert)"
              class="px-2 py-1 bg-white/5 border border-white/10 text-white/60 font-mono text-[10px] rounded hover:bg-white/10 transition-colors"
            >
              Voir
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Détail -->
    <div v-if="selectedAlert" class="w-80 shrink-0 panel p-4 overflow-y-auto">
      <h2 class="font-mono text-xs text-white/50 uppercase tracking-wider mb-4">Détail</h2>
      <AlertBadge :level="selectedAlert.level" class="mb-3" />
      <p class="font-body text-sm text-white/80 mb-4">{{ selectedAlert.message }}</p>
      <div class="space-y-3 text-xs">
        <DetailRow label="Site"      :value="selectedAlert.siteName" />
        <DetailRow label="Zone"      :value="`Zone ${selectedAlert.zone}`" />
        <DetailRow label="Type"      :value="selectedAlert.anomalyType" />
        <DetailRow label="Heure"     :value="formatTime(selectedAlert.timestamp)" />
        <DetailRow label="Confiance" :value="`${(selectedAlert.confidence*100).toFixed(0)}%`" />
        <DetailRow label="Statut"    :value="selectedAlert.resolved ? '✅ Résolu' : '🔴 Actif'" />
      </div>
      <button
        v-if="!selectedAlert.resolved"
        @click="alertsStore.resolveAlert(selectedAlert.id)"
        class="mt-4 w-full py-2 bg-sn-green/15 border border-sn-green/25 text-sn-green font-mono text-xs rounded-lg hover:bg-sn-green/25 transition-colors"
      >
        Marquer résolu
      </button>
    </div>
  </div>

  <AlertModal />
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import type { Alert } from '~/types'
import AlertBadge from '~/components/alerts/AlertBadge.vue'
import AlertModal from '~/components/alerts/AlertModal.vue'

const sitesStore  = useSitesStore()
const alertsStore = useAlertsStore()
const filterState = useAlerts()

const selectedId    = ref<string>('')
const selectedAlert = computed(() => alertsStore.alerts.find(a => a.id === selectedId.value) ?? null)

function select(alert: Alert) { selectedId.value = alert.id }
const formatTime = (ts: string) => dayjs(ts).format('HH:mm:ss')

const DetailRow = defineComponent({
  props: { label: String, value: String },
  template: `
    <div class="flex justify-between">
      <span class="font-mono text-white/30">{{ label }}</span>
      <span class="font-body text-white/70">{{ value }}</span>
    </div>
  `,
})

useHead({ title: 'Alertes — JOJ Dakar 2026' })
</script>
