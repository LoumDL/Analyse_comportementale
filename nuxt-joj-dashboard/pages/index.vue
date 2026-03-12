<template>
  <div class="h-full flex flex-col gap-4">

    <!-- KPI Row -->
    <div class="grid grid-cols-3 gap-4 shrink-0">
      <KpiCard
        label="Personnes actives"
        :value="sitesStore.totalPersons"
        icon="heroicons:users"
        color="green"
      />
      <KpiCard
        label="Alertes actives"
        :value="alertsStore.activeAlerts.length"
        icon="heroicons:bell-alert"
        :color="alertsStore.criticalCount > 0 ? 'red' : 'yellow'"
        :critical="alertsStore.criticalCount"
      />
      <KpiCard
        label="Statut site"
        :value="sitesStore.sitesOk"
        :total="1"
        icon="heroicons:building-storefront"
        :color="sitesStore.site.status === 'critical' ? 'red' : sitesStore.site.status === 'attention' ? 'yellow' : 'green'"
      />
    </div>

    <!-- Détail zones -->
    <div class="panel p-4 flex-1">
      <div class="flex items-center justify-between mb-4">
        <h2 class="font-mono text-xs text-white/50 uppercase tracking-widest">
          {{ sitesStore.site.name }} — Zones en temps réel
        </h2>
        <div class="flex items-center gap-3">
          <ZoneIndicator :status="sitesStore.site.status as any" />
          <button
            @click="refresh"
            :disabled="refreshing"
            class="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 border border-white/10 text-white/60 font-mono text-[10px] rounded-lg hover:bg-white/10 hover:text-white/80 transition-colors disabled:opacity-50"
          >
            <Icon name="heroicons:arrow-path" :class="['w-3.5 h-3.5', refreshing ? 'animate-spin' : '']" />
            Actualiser
          </button>
        </div>
      </div>

      <!-- Aucune zone reçue -->
      <div v-if="!Object.keys(sitesStore.site.zones).length" class="flex flex-col items-center justify-center gap-3 py-16 text-center">
        <Icon name="heroicons:signal-slash" class="w-10 h-10 text-white/10" />
        <p class="font-mono text-xs text-white/25">En attente des données du backend…</p>
        <p class="font-mono text-[10px] text-white/15">Les zones apparaîtront dès que l'analyse sera lancée</p>
      </div>

      <div v-else class="grid grid-cols-4 gap-4">
        <NuxtLink
          v-for="(zone, key) in sitesStore.site.zones"
          :key="key"
          :to="`/zones/${key}`"
          :class="[
            'p-4 rounded-xl border transition-all duration-300 block group',
            zone.status === 'critical'  ? 'border-sn-red/40 bg-sn-red/5 glow-red hover:border-sn-red/60' :
            zone.status === 'attention' ? 'border-sn-yellow/30 bg-sn-yellow/5 hover:border-sn-yellow/50' :
                                          'border-white/8 bg-white/2 hover:border-white/15'
          ]"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="font-hud text-lg text-white/60 group-hover:text-white/80 transition-colors">Zone {{ key }}</span>
            <ZoneIndicator :status="zone.status as any" />
          </div>
          <p class="font-hud text-3xl tabular-nums" :class="
            zone.status === 'critical' ? 'text-sn-red' :
            zone.status === 'attention' ? 'text-sn-yellow' : 'text-sn-green'
          ">
            {{ zone.count }}
          </p>
          <p class="font-mono text-[10px] text-white/40 mt-1">personnes</p>
          <div class="mt-3 h-1.5 bg-white/5 rounded-full overflow-hidden">
            <div
              :class="['h-full rounded-full transition-all duration-500',
                zone.status === 'critical' ? 'bg-sn-red' :
                zone.status === 'attention' ? 'bg-sn-yellow' : 'bg-sn-green'
              ]"
              :style="{ width: `${Math.min(100, (zone.density / 6) * 100)}%` }"
            />
          </div>
          <p class="font-mono text-[10px] text-white/30 mt-1.5">
            {{ zone.density.toFixed(1) }} p/m² · {{ zone.avgSpeed.toFixed(1) }} m/s
          </p>
          <p class="font-mono text-[9px] text-white/15 mt-2 group-hover:text-white/25 transition-colors">Voir le détail →</p>
        </NuxtLink>
      </div>
    </div>

    <AlertModal />
  </div>
</template>

<script setup lang="ts">
import KpiCard       from '~/components/dashboard/KpiCard.vue'
import ZoneIndicator from '~/components/dashboard/ZoneIndicator.vue'
import AlertModal    from '~/components/alerts/AlertModal.vue'

const sitesStore  = useSitesStore()
const alertsStore = useAlertsStore()
const refreshing  = ref(false)

// Réinitialise tout à 0 au chargement de la page
onMounted(() => {
  alertsStore.clearAll()
  sitesStore.resetZones()
})

async function refresh() {
  refreshing.value = true
  await sitesStore.fetchSite()
  refreshing.value = false
}

useHead({ title: 'Dashboard — JOJ Dakar 2026' })
</script>
