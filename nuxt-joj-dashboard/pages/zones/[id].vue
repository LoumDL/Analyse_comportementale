<template>
  <div v-if="zone" class="h-full flex flex-col gap-4">

    <!-- En-tête avec navigation -->
    <div class="flex items-center gap-4 shrink-0">
      <NuxtLink
        to="/"
        class="flex items-center gap-1.5 text-white/30 hover:text-white/60 font-mono text-[10px] transition-colors"
      >
        <Icon name="heroicons:chevron-left" class="w-3.5 h-3.5" />
        Tableau de bord
      </NuxtLink>
      <span class="text-white/15">/</span>
      <div class="flex items-center gap-3">
        <div
          :class="[
            'w-8 h-8 rounded-lg flex items-center justify-center font-hud text-sm font-bold',
            statusBg,
          ]"
        >{{ zoneId }}</div>
        <div>
          <h1 class="font-hud text-base text-white/85">Zone {{ zoneId }}</h1>
          <p class="font-mono text-[10px] text-white/30 mt-0.5">{{ sitesStore.site.name }} · Analyse détaillée</p>
        </div>
        <ZoneStatusBadge :status="zone.status" class="ml-2" />
      </div>
    </div>

    <!-- KPI Row -->
    <div class="grid grid-cols-4 gap-3 shrink-0">
      <div class="panel p-4 flex flex-col gap-1">
        <p class="font-mono text-[9px] text-white/30 uppercase tracking-widest">Personnes</p>
        <p :class="['font-hud text-3xl tabular-nums', statusText]">{{ zone.count }}</p>
        <p class="font-mono text-[9px] text-white/25">actives dans la zone</p>
      </div>
      <div class="panel p-4 flex flex-col gap-1">
        <p class="font-mono text-[9px] text-white/30 uppercase tracking-widest">Densité</p>
        <p :class="['font-hud text-3xl tabular-nums', statusText]">{{ zone.density.toFixed(2) }}</p>
        <p class="font-mono text-[9px] text-white/25">personnes / m²</p>
      </div>
      <div class="panel p-4 flex flex-col gap-1">
        <p class="font-mono text-[9px] text-white/30 uppercase tracking-widest">Vitesse moy.</p>
        <p class="font-hud text-3xl tabular-nums text-sn-yellow">{{ zone.avgSpeed.toFixed(2) }}</p>
        <p class="font-mono text-[9px] text-white/25">m/s déplacement</p>
      </div>
      <div class="panel p-4 flex flex-col gap-1">
        <p class="font-mono text-[9px] text-white/30 uppercase tracking-widest">Alertes actives</p>
        <p :class="['font-hud text-3xl tabular-nums', zoneAlerts.some(a => a.level === 'critical') ? 'text-sn-red' : 'text-sn-yellow']">
          {{ zoneActiveAlerts.length }}
        </p>
        <p class="font-mono text-[9px] text-white/25">non résolues</p>
      </div>
    </div>

    <!-- Corps principal -->
    <div class="flex-1 min-h-0 grid grid-cols-5 gap-4">

      <!-- Graphique densité (gauche) -->
      <div class="col-span-3 panel p-4 flex flex-col">
        <div class="flex items-center justify-between mb-4">
          <p class="font-mono text-[10px] text-white/40 uppercase tracking-widest">Densité — 10 dernières minutes</p>
          <div class="flex items-center gap-3">
            <span :class="['w-1.5 h-1.5 rounded-full', zone.status === 'normal' ? 'bg-sn-green' : zone.status === 'attention' ? 'bg-sn-yellow' : 'bg-sn-red pulse']" />
            <span class="font-mono text-[10px] text-white/40">Dernière mise à jour {{ lastUpdate }}</span>
          </div>
        </div>

        <!-- SVG chart simple -->
        <div class="flex-1 relative min-h-0" style="min-height: 160px">
          <svg :viewBox="`0 0 ${svgW} ${svgH}`" class="w-full h-full" preserveAspectRatio="none">
            <!-- Seuils -->
            <line :x1="0" :y1="yScale(4.0)" :x2="svgW" :y2="yScale(4.0)"
              stroke="rgba(227,27,35,0.3)" stroke-width="1" stroke-dasharray="4,3" />
            <text :x="svgW - 4" :y="yScale(4.0) - 4" font-family="monospace" font-size="9" fill="rgba(227,27,35,0.5)" text-anchor="end">Critique 4.0</text>

            <line :x1="0" :y1="yScale(3.0)" :x2="svgW" :y2="yScale(3.0)"
              stroke="rgba(253,239,66,0.25)" stroke-width="1" stroke-dasharray="4,3" />
            <text :x="svgW - 4" :y="yScale(3.0) - 4" font-family="monospace" font-size="9" fill="rgba(253,239,66,0.4)" text-anchor="end">Attention 3.0</text>

            <!-- Aire remplie -->
            <defs>
              <linearGradient id="densityGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" :stop-color="gradColor" stop-opacity="0.3" />
                <stop offset="100%" :stop-color="gradColor" stop-opacity="0.02" />
              </linearGradient>
            </defs>
            <path v-if="areaPath" :d="areaPath" :fill="'url(#densityGrad)'" />
            <path v-if="linePath"  :d="linePath"  fill="none" :stroke="lineColor" stroke-width="1.5" />

            <!-- Points -->
            <circle
              v-for="(pt, i) in chartPoints"
              :key="i"
              :cx="pt.x" :cy="pt.y" r="2.5"
              :fill="lineColor" fill-opacity="0.8"
            />
          </svg>
        </div>

        <!-- Légende axes -->
        <div class="flex justify-between mt-1">
          <span class="font-mono text-[9px] text-white/20">-10 min</span>
          <span class="font-mono text-[9px] text-white/20">Maintenant</span>
        </div>
      </div>

      <!-- Alertes zone (droite) -->
      <div class="col-span-2 panel p-4 flex flex-col overflow-hidden">
        <div class="flex items-center justify-between mb-3 shrink-0">
          <p class="font-mono text-[10px] text-white/40 uppercase tracking-widest">Alertes de la zone</p>
          <span class="font-mono text-[10px] text-white/25">{{ zoneAlerts.length }} total</span>
        </div>

        <div v-if="!zoneAlerts.length" class="flex-1 flex flex-col items-center justify-center text-center">
          <Icon name="heroicons:shield-check" class="w-8 h-8 text-sn-green/30 mb-2" />
          <p class="font-mono text-xs text-white/25">Aucune alerte</p>
          <p class="font-mono text-[9px] text-white/15 mt-1">La zone est sous contrôle</p>
        </div>

        <div v-else class="flex-1 overflow-y-auto space-y-2">
          <div
            v-for="alert in zoneAlerts"
            :key="alert.id"
            :class="[
              'px-3 py-2.5 rounded-lg border text-xs transition-colors',
              alert.level === 'critical' ? 'border-sn-red/25 bg-sn-red/5' :
              alert.level === 'warning'  ? 'border-sn-yellow/20 bg-sn-yellow/4' :
                                           'border-white/6 bg-white/2',
            ]"
          >
            <div class="flex items-center justify-between mb-1">
              <span :class="[
                'font-mono text-[9px] px-1.5 py-0.5 rounded border',
                alert.level === 'critical' ? 'border-sn-red/40 text-sn-red' :
                alert.level === 'warning'  ? 'border-sn-yellow/40 text-sn-yellow' :
                                              'border-white/15 text-white/40',
              ]">{{ alert.level.toUpperCase() }}</span>
              <span class="font-mono text-[9px] text-white/30">{{ formatTime(alert.timestamp) }}</span>
            </div>
            <p class="font-body text-white/65 text-[11px] leading-relaxed">{{ alert.message }}</p>
            <div class="flex items-center justify-between mt-1.5">
              <span class="font-mono text-[9px] text-white/30">{{ alert.anomalyType }}</span>
              <span :class="['font-mono text-[9px]', alert.resolved ? 'text-sn-green' : 'text-white/25']">
                {{ alert.resolved ? '✓ Résolu' : '● Actif' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Détails comportementaux -->
    <div class="panel p-4 shrink-0">
      <p class="font-mono text-[10px] text-white/40 uppercase tracking-widest mb-3">Analyse comportementale</p>
      <div class="grid grid-cols-4 gap-4">

        <div class="space-y-1">
          <p class="font-mono text-[9px] text-white/25 uppercase">Niveau de risque</p>
          <p :class="['font-mono text-sm font-semibold', statusText]">
            {{ zone.status === 'critical' ? 'CRITIQUE' : zone.status === 'attention' ? 'ATTENTION' : 'NORMAL' }}
          </p>
          <div class="h-1 bg-white/5 rounded-full overflow-hidden">
            <div
              :class="['h-full rounded-full', zone.status === 'critical' ? 'bg-sn-red' : zone.status === 'attention' ? 'bg-sn-yellow' : 'bg-sn-green']"
              :style="{ width: `${Math.min(100, (zone.density / 6) * 100)}%` }"
            />
          </div>
        </div>

        <div class="space-y-1">
          <p class="font-mono text-[9px] text-white/25 uppercase">Seuil critique</p>
          <p class="font-mono text-sm text-white/55">4.0 p/m²</p>
          <p class="font-mono text-[9px] text-white/25">
            {{ zone.density >= 4.0 ? '⚠ Dépassé' : `Marge : ${(4.0 - zone.density).toFixed(2)} p/m²` }}
          </p>
        </div>

        <div class="space-y-1">
          <p class="font-mono text-[9px] text-white/25 uppercase">Flux mouvement</p>
          <p class="font-mono text-sm text-sn-yellow">
            {{ zone.avgSpeed < 0.5 ? 'Très lent' : zone.avgSpeed < 1.0 ? 'Lent' : zone.avgSpeed < 1.5 ? 'Normal' : 'Rapide' }}
          </p>
          <p class="font-mono text-[9px] text-white/25">{{ zone.avgSpeed.toFixed(2) }} m/s moyen</p>
        </div>

        <div class="space-y-1">
          <p class="font-mono text-[9px] text-white/25 uppercase">Caméras actives</p>
          <p class="font-mono text-sm text-white/55">{{ camerasForZone.length }}</p>
          <p class="font-mono text-[9px] text-white/25">
            {{ camerasForZone.length ? camerasForZone.map(c => c.name).join(', ') : 'Aucune' }}
          </p>
        </div>

      </div>
    </div>
  </div>

  <!-- Zone inexistante -->
  <div v-else class="h-full flex flex-col items-center justify-center gap-4 text-center">
    <Icon name="heroicons:map-pin-slash" class="w-12 h-12 text-white/15" />
    <p class="font-hud text-base text-white/40">Zone introuvable</p>
    <NuxtLink to="/" class="font-mono text-xs text-sn-green hover:underline">← Retour au tableau de bord</NuxtLink>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'

const route      = useRoute()
const zoneId     = computed(() => String(route.params.id).toUpperCase())
const sitesStore = useSitesStore()
const alertsStore = useAlertsStore()
const camerasStore = useCamerasStore()

const zone = computed(() => sitesStore.site.zones[zoneId.value] ?? null)

const lastUpdate = computed(() => dayjs(sitesStore.site.lastUpdate).format('HH:mm:ss'))

const zoneAlerts = computed(() =>
  alertsStore.alerts.filter(a => a.zone === zoneId.value).slice(0, 30)
)
const zoneActiveAlerts = computed(() =>
  zoneAlerts.value.filter(a => !a.resolved)
)

const camerasForZone = computed(() =>
  camerasStore.cameras.filter(c => c.zones.includes(zoneId.value) && c.active)
)

// Computed status styles
const statusText = computed(() => ({
  critical:  'text-sn-red',
  attention: 'text-sn-yellow',
  normal:    'text-sn-green',
}[zone.value?.status ?? 'normal']))

const statusBg = computed(() => ({
  critical:  'bg-sn-red/20 text-sn-red',
  attention: 'bg-sn-yellow/20 text-sn-yellow',
  normal:    'bg-sn-green/15 text-sn-green',
}[zone.value?.status ?? 'normal']))

// --- Graphique densité simulé ---
const svgW = 400
const svgH = 160
const maxY = 6.0

function yScale(v: number): number {
  return svgH - (v / maxY) * svgH * 0.85 - svgH * 0.05
}

// Historique de 20 points (simulé + valeur actuelle)
const history = ref<number[]>([])
const MAX_HIST = 20

onMounted(() => {
  // Initialise avec des valeurs simulées autour de la densité actuelle
  const base = zone.value?.density ?? 1.5
  history.value = Array.from({ length: MAX_HIST }, (_, i) => {
    const noise = (Math.random() - 0.5) * 0.6
    return Math.max(0, base + noise - ((MAX_HIST - i) * 0.02))
  })
  camerasStore.restore()
})

// Mise à jour à chaque changement de zone
watch(() => zone.value?.density, (newDensity) => {
  if (newDensity == null) return
  history.value.push(newDensity)
  if (history.value.length > MAX_HIST) history.value.shift()
})

const chartPoints = computed(() => {
  const pts = history.value
  if (!pts.length) return []
  return pts.map((v, i) => ({
    x: (i / (MAX_HIST - 1)) * svgW,
    y: yScale(v),
  }))
})

const linePath = computed(() => {
  const pts = chartPoints.value
  if (pts.length < 2) return ''
  return pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')
})

const areaPath = computed(() => {
  const pts = chartPoints.value
  if (pts.length < 2) return ''
  const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')
  return `${line} L ${svgW} ${svgH} L 0 ${svgH} Z`
})

const lineColor  = computed(() => zone.value?.status === 'critical' ? '#E31B23' : zone.value?.status === 'attention' ? '#FDEF42' : '#00853F')
const gradColor  = computed(() => lineColor.value)

// --- Zone status badge component inline ---
const ZoneStatusBadge = defineComponent({
  props: { status: String },
  template: `
    <span :class="[
      'font-mono text-[9px] px-2 py-0.5 rounded border',
      status === 'critical'  ? 'border-sn-red/40 text-sn-red bg-sn-red/8' :
      status === 'attention' ? 'border-sn-yellow/35 text-sn-yellow bg-sn-yellow/5' :
                               'border-sn-green/25 text-sn-green bg-sn-green/5',
    ]">{{ status === 'critical' ? 'CRITIQUE' : status === 'attention' ? 'ATTENTION' : 'NORMAL' }}</span>
  `,
})

const formatTime = (ts: string) => dayjs(ts).format('HH:mm:ss')

useHead({ title: computed(() => `Zone ${zoneId.value} — JOJ Dakar 2026`) })
</script>
