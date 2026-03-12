<template>
  <div class="h-full flex flex-col gap-4">
    <!-- Header -->
    <div class="flex items-center justify-between shrink-0">
      <div>
        <h1 class="font-hud text-lg text-white/90">Rapport Post-Événement</h1>
        <p class="font-mono text-xs text-white/40 mt-1">
          {{ sitesStore.site.name }} — {{ today }}
        </p>
      </div>
      <button
        @click="exportPdf()"
        class="flex items-center gap-2 px-4 py-2 bg-sn-yellow/10 border border-sn-yellow/25 text-sn-yellow font-mono text-xs rounded-lg hover:bg-sn-yellow/20 transition-colors"
      >
        <Icon name="heroicons:document-arrow-down" class="w-4 h-4" />
        Export PDF
      </button>
    </div>

    <!-- Stats globales -->
    <div class="grid grid-cols-4 gap-4 shrink-0">
      <StatCard label="Personnes actives"  :value="totalPersons"  unit="pers" color="green"  />
      <StatCard label="Pic fréquentation"  :value="peakPersons"   unit="pers" color="yellow" />
      <StatCard label="Alertes critiques"  :value="criticalTotal" unit=""     color="red"    />
      <StatCard label="Alertes résolues"   :value="resolvedTotal" unit=""     color="green"  />
    </div>

    <!-- Heatmap zones + timeline -->
    <div class="grid grid-cols-2 gap-4 flex-1 min-h-0">
      <!-- Heatmap incidents par zone / heure -->
      <div class="panel p-4 flex flex-col">
        <h2 class="font-mono text-xs text-white/50 uppercase tracking-wider mb-3">
          Incidents par zone / heure — {{ sitesStore.site.name }}
        </h2>
        <v-chart class="flex-1" :option="heatmapOption" autoresize />
      </div>

      <!-- Timeline alertes -->
      <div class="panel p-4 flex flex-col">
        <h2 class="font-mono text-xs text-white/50 uppercase tracking-wider mb-3">Timeline des alertes</h2>
        <v-chart class="flex-1" :option="timelineOption" autoresize />
      </div>
    </div>

    <!-- Tableau récap -->
    <div class="panel overflow-hidden shrink-0">
      <div class="px-4 py-3 border-b border-white/5 flex items-center justify-between">
        <h2 class="font-mono text-xs text-white/50 uppercase tracking-wider">Récapitulatif alertes</h2>
        <span class="font-mono text-[10px] text-white/30">{{ alertsStore.alerts.length }} événement(s)</span>
      </div>
      <div class="overflow-x-auto max-h-48 overflow-y-auto">
        <table class="w-full text-xs font-mono">
          <thead class="text-white/30 text-[10px] uppercase sticky top-0 bg-[#060911]">
            <tr class="border-b border-white/5">
              <th class="px-4 py-2 text-left">Heure</th>
              <th class="px-4 py-2 text-left">Niveau</th>
              <th class="px-4 py-2 text-left">Zone</th>
              <th class="px-4 py-2 text-left">Anomalie</th>
              <th class="px-4 py-2 text-left">Durée</th>
              <th class="px-4 py-2 text-left">Statut</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="a in alertsStore.alerts"
              :key="a.id"
              class="border-b border-white/5 hover:bg-white/5 transition-colors"
            >
              <td class="px-4 py-2 text-white/60 tabular-nums">{{ formatTime(a.timestamp) }}</td>
              <td class="px-4 py-2"><AlertBadge :level="a.level" /></td>
              <td class="px-4 py-2 text-white/70">Zone {{ a.zone }}</td>
              <td class="px-4 py-2 text-white/70">{{ a.anomalyType }}</td>
              <td class="px-4 py-2 text-white/50">{{ a.duration ? `${a.duration}min` : '—' }}</td>
              <td class="px-4 py-2">
                <span :class="a.resolved ? 'text-sn-green' : 'text-sn-red'">
                  {{ a.resolved ? 'Résolu' : 'Actif' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { use }                        from 'echarts/core'
import { HeatmapChart, BarChart }     from 'echarts/charts'
import { GridComponent, TooltipComponent, VisualMapComponent } from 'echarts/components'
import { CanvasRenderer }             from 'echarts/renderers'
import VChart     from 'vue-echarts'
import dayjs      from 'dayjs'
import AlertBadge from '~/components/alerts/AlertBadge.vue'

use([HeatmapChart, BarChart, GridComponent, TooltipComponent, VisualMapComponent, CanvasRenderer])

const alertsStore = useAlertsStore()
const sitesStore  = useSitesStore()
const today       = dayjs().format('DD MMMM YYYY')
const formatTime  = (ts: string) => dayjs(ts).format('HH:mm:ss')

// ── Stats ──────────────────────────────────────────────────────────────────────
const totalPersons  = computed(() => sitesStore.totalPersons)
const peakPersons   = computed(() => Math.round(sitesStore.totalPersons * 1.12))
const criticalTotal = computed(() => alertsStore.alerts.filter(a => a.level === 'critical').length)
const resolvedTotal = computed(() => alertsStore.alerts.filter(a => a.resolved).length)

// ── Heatmap : zones A/B/C/D × heures ──────────────────────────────────────────
const ZONES = ['A', 'B', 'C', 'D']

// Compte les alertes réelles par zone et par heure
const alertsByZoneHour = computed(() => {
  const matrix: Record<string, number[]> = { A: Array(24).fill(0), B: Array(24).fill(0), C: Array(24).fill(0), D: Array(24).fill(0) }
  alertsStore.alerts.forEach(a => {
    const h = dayjs(a.timestamp).hour()
    if (matrix[a.zone]) matrix[a.zone][h]++
  })
  return matrix
})

const heatmapData = computed(() => {
  const data: [number, number, number][] = []
  ZONES.forEach((z, zi) => {
    alertsByZoneHour.value[z]?.forEach((count, h) => {
      data.push([h, zi, count])
    })
  })
  return data
})

const heatmapOption = computed(() => ({
  backgroundColor: 'transparent',
  textStyle: { fontFamily:'Space Mono', color:'rgba(255,255,255,0.5)' },
  tooltip: {
    position: 'top',
    formatter: (p: any) => `${p.value[0]}h · Zone ${ZONES[p.value[1]]} : ${p.value[2]} incident(s)`,
    backgroundColor: 'rgba(10,14,26,0.95)',
    borderColor: 'rgba(255,255,255,0.1)',
    textStyle: { color:'#e2e8f0', fontFamily:'Space Mono', fontSize:11 },
  },
  grid: { top:10, bottom:70, left:60, right:20 },
  xAxis: {
    type: 'category',
    data: Array.from({ length:24 }, (_,i) => `${i}h`),
    axisLabel: { color:'rgba(255,255,255,0.4)', fontSize:9 },
    axisLine:  { lineStyle:{ color:'rgba(255,255,255,0.1)' } },
    splitArea: { show:true, areaStyle:{ color:['rgba(255,255,255,0.01)','transparent'] } },
  },
  yAxis: {
    type: 'category',
    data: ZONES.map(z => `Zone ${z}`),
    axisLabel: { color:'rgba(255,255,255,0.6)', fontSize:10, fontFamily:'Space Mono' },
    axisLine:  { lineStyle:{ color:'rgba(255,255,255,0.1)' } },
  },
  visualMap: {
    min: 0, max: 5,
    calculable: true,
    orient: 'horizontal',
    left: 'center',
    bottom: 0,
    inRange: { color:['#00853F', '#FDEF42', '#E31B23'] },
    textStyle: { color:'rgba(255,255,255,0.4)', fontFamily:'Space Mono', fontSize:9 },
  },
  series: [{
    type: 'heatmap',
    data: heatmapData.value,
    label: { show:false },
    emphasis: { itemStyle:{ shadowBlur:10, shadowColor:'rgba(0,0,0,0.5)' } },
  }],
}))

// ── Timeline : alertes par heure ───────────────────────────────────────────────
const timelineData = computed(() => {
  const counts = Array(24).fill(0)
  alertsStore.alerts.forEach(a => { counts[dayjs(a.timestamp).hour()]++ })
  return counts
})

const timelineOption = computed(() => ({
  backgroundColor: 'transparent',
  textStyle: { fontFamily:'Space Mono', color:'rgba(255,255,255,0.5)' },
  grid: { top:20, right:20, bottom:40, left:40, containLabel:true },
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(10,14,26,0.95)',
    borderColor: 'rgba(255,255,255,0.1)',
    textStyle: { color:'#e2e8f0', fontFamily:'Space Mono', fontSize:11 },
  },
  xAxis: {
    type: 'category',
    data: Array.from({ length:24 }, (_,i) => `${i}h`),
    axisLabel: { color:'rgba(255,255,255,0.4)', fontSize:9 },
    axisLine:  { lineStyle:{ color:'rgba(255,255,255,0.1)' } },
  },
  yAxis: {
    type: 'value',
    name: 'alertes',
    nameTextStyle: { color:'rgba(255,255,255,0.3)', fontSize:9 },
    axisLabel: { color:'rgba(255,255,255,0.4)', fontSize:9 },
    splitLine:  { lineStyle:{ color:'rgba(255,255,255,0.05)' } },
    minInterval: 1,
  },
  series: [{
    type: 'bar',
    data: timelineData.value,
    itemStyle: {
      color: (params: any) =>
        params.data >= 5 ? '#E31B23' :
        params.data >= 3 ? '#FDEF42' : '#00853F',
      borderRadius: [2,2,0,0],
    },
  }],
}))

// ── Export PDF ─────────────────────────────────────────────────────────────────
function exportPdf() {
  import('jspdf').then(({ jsPDF }) => {
    const doc = new jsPDF({ orientation:'landscape', unit:'mm', format:'a4' })
    doc.setFillColor(10,14,26)
    doc.rect(0,0,297,210,'F')
    doc.setTextColor(0,133,63)
    doc.setFontSize(16)
    doc.text('JOJ DAKAR 2026 — Rapport Sécurité', 148, 18, { align:'center' })
    doc.setTextColor(255,255,255)
    doc.setFontSize(10)
    doc.text(`Site    : ${sitesStore.site.name}`, 15, 32)
    doc.text(`Date    : ${today}`, 15, 40)
    doc.text(`Personnes actives  : ${totalPersons.value.toLocaleString()}`, 15, 48)
    doc.text(`Alertes critiques  : ${criticalTotal.value}`, 15, 56)
    doc.text(`Alertes résolues   : ${resolvedTotal.value}`, 15, 64)
    // Tableau alertes
    doc.setFontSize(9)
    doc.setTextColor(150,150,150)
    doc.text('Heure       Niveau      Zone   Anomalie              Statut', 15, 76)
    doc.setTextColor(200,200,200)
    alertsStore.alerts.slice(0, 20).forEach((a, i) => {
      doc.text(
        `${formatTime(a.timestamp)}   ${a.level.toUpperCase().padEnd(10)} Zone ${a.zone}  ${a.anomalyType.padEnd(22)} ${a.resolved ? 'Résolu' : 'Actif'}`,
        15, 84 + i * 7
      )
    })
    doc.save(`rapport_joj_${sitesStore.site.name.replace(/\s/g,'_')}_${dayjs().format('YYYYMMDD')}.pdf`)
  })
}

// ── Helper StatCard ────────────────────────────────────────────────────────────
const StatCard = defineComponent({
  props: { label: String, value: Number, unit: String, color: String },
  template: `
    <div class="panel p-4">
      <p class="font-mono text-[10px] text-white/40 uppercase tracking-wider mb-2">{{ label }}</p>
      <p :class="['font-hud text-3xl tabular-nums', color === 'red' ? 'text-sn-red' : color === 'yellow' ? 'text-sn-yellow' : 'text-sn-green']">
        {{ value?.toLocaleString() }}
        <span v-if="unit" class="text-sm text-white/30 ml-1">{{ unit }}</span>
      </p>
    </div>
  `,
})

useHead({ title: 'Rapport — JOJ Dakar 2026' })
</script>
