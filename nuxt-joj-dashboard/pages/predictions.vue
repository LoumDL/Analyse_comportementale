<template>
  <div class="h-full flex flex-col gap-4">

    <!-- En-tête -->
    <div class="flex items-center justify-between shrink-0">
      <div>
        <h1 class="font-hud text-base text-white/85">Prédictions de Congestion</h1>
        <p class="font-mono text-[10px] text-white/30 mt-0.5">
          TimeGPT · +5 / +10 / +15 min · Confiance {{ avgConfidence }}%
        </p>
      </div>
      <button
        @click="fetchPredictions"
        :disabled="loading"
        class="flex items-center gap-1.5 px-3 py-1.5 bg-white/4 border border-white/8 text-white/50 font-mono text-[10px] rounded-lg hover:bg-white/8 hover:text-white/70 transition-colors disabled:opacity-40"
      >
        <Icon name="heroicons:arrow-path" :class="['w-3.5 h-3.5', loading ? 'animate-spin' : '']" />
        Actualiser
      </button>
    </div>

    <!-- Bandeau statut global -->
    <div
      :class="[
        'shrink-0 flex items-center gap-3 px-4 py-3 rounded-xl border',
        globalRisk === 'critical'  ? 'border-sn-red/30 bg-sn-red/8' :
        globalRisk === 'attention' ? 'border-sn-yellow/25 bg-sn-yellow/5' :
                                     'border-sn-green/20 bg-sn-green/5',
      ]"
    >
      <span :class="['w-2 h-2 rounded-full shrink-0', globalRisk === 'critical' ? 'bg-sn-red pulse' : globalRisk === 'attention' ? 'bg-sn-yellow' : 'bg-sn-green']" />
      <div class="flex-1 min-w-0">
        <p :class="['font-mono text-xs', globalRisk === 'critical' ? 'text-sn-red' : globalRisk === 'attention' ? 'text-sn-yellow' : 'text-sn-green']">
          {{ globalMessage }}
        </p>
        <p class="font-mono text-[10px] text-white/35 mt-0.5 truncate">{{ globalDetail }}</p>
      </div>
      <span :class="['font-hud text-[10px] px-2 py-0.5 rounded border shrink-0', globalRisk === 'critical' ? 'border-sn-red/40 text-sn-red' : globalRisk === 'attention' ? 'border-sn-yellow/40 text-sn-yellow' : 'border-sn-green/30 text-sn-green']">
        {{ globalRisk === 'critical' ? 'CRITIQUE' : globalRisk === 'attention' ? 'ATTENTION' : 'NORMAL' }}
      </span>
    </div>

    <!-- Zones + Chart -->
    <div class="flex-1 min-h-0 grid grid-cols-5 gap-4">

      <!-- Cartes zones (colonne gauche) -->
      <div class="col-span-2 flex flex-col gap-3 overflow-y-auto">
        <div
          v-for="pred in mainPredictions"
          :key="pred.zone"
          :class="[
            'panel p-4 flex-1 flex flex-col gap-3',
            riskAt15(pred) === 'critical'  ? 'border-sn-red/30'  :
            riskAt15(pred) === 'attention' ? 'border-sn-yellow/25' :
                                             'border-white/5',
          ]"
        >
          <!-- Zone header -->
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span :class="['w-1.5 h-1.5 rounded-full', riskAt15(pred) === 'critical' ? 'bg-sn-red' : riskAt15(pred) === 'attention' ? 'bg-sn-yellow' : 'bg-sn-green']" />
              <span class="font-hud text-sm text-white/75">Zone {{ pred.zone }}</span>
            </div>
            <div class="flex items-center gap-2">
              <span :class="['font-mono text-[9px] px-1.5 py-0.5 rounded border',
                riskAt15(pred) === 'critical'  ? 'border-sn-red/35 text-sn-red bg-sn-red/8' :
                riskAt15(pred) === 'attention' ? 'border-sn-yellow/35 text-sn-yellow bg-sn-yellow/8' :
                                                  'border-sn-green/25 text-sn-green bg-sn-green/5']">
                {{ riskAt15(pred) === 'critical' ? 'CRITIQUE' : riskAt15(pred) === 'attention' ? 'ATTENTION' : 'NORMAL' }}
              </span>
              <span :class="['text-sm font-bold leading-none', pred.trend === 'up' ? 'text-sn-red' : pred.trend === 'down' ? 'text-sn-green' : 'text-white/25']">
                {{ pred.trend === 'up' ? '↑' : pred.trend === 'down' ? '↓' : '→' }}
              </span>
            </div>
          </div>

          <!-- Horizons -->
          <div class="space-y-2">
            <div v-for="(val, label) in { '+5 min': pred.h5, '+10 min': pred.h10, '+15 min': pred.h15 }" :key="label"
              class="flex items-center gap-2"
            >
              <span class="font-mono text-[9px] text-white/30 w-12 shrink-0">{{ label }}</span>
              <div class="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                <div
                  :class="['h-full rounded-full transition-all', val >= 4.0 ? 'bg-sn-red' : val >= 3.0 ? 'bg-sn-yellow' : 'bg-sn-green']"
                  :style="{ width: `${Math.min(100, (val / 6) * 100)}%` }"
                />
              </div>
              <span :class="['font-hud text-[11px] tabular-nums w-16 text-right shrink-0', val >= 4.0 ? 'text-sn-red' : val >= 3.0 ? 'text-sn-yellow' : 'text-sn-green']">
                {{ val.toFixed(2) }} p/m²
              </span>
            </div>
          </div>

          <!-- Recommandation -->
          <p class="font-mono text-[9px] text-white/40 leading-relaxed border-t border-white/5 pt-2">
            {{ recommendation(pred) }}
          </p>
        </div>
      </div>

      <!-- Graphique (colonne droite) -->
      <div class="col-span-3">
        <PredictionChart :predictions="predictions" class="h-full" />
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import PredictionChart from '~/components/charts/PredictionChart.vue'
import type { Prediction } from '~/types'

const sitesStore     = useSitesStore()
const selectedSiteId = ref(sitesStore.sites[0]?.id ?? '')
const { predictions, loading, fetchPredictions } = usePredictions(selectedSiteId)

const mainPredictions = computed(() => predictions.value.filter(p => p.zone !== 'G'))

const avgConfidence = computed(() => {
  const p = mainPredictions.value
  if (!p.length) return 85
  return Math.round(p.reduce((s, x) => s + x.confidence, 0) / p.length * 100)
})

function riskAt15(pred: Prediction): 'critical' | 'attention' | 'normal' {
  return pred.h15 >= 4.0 ? 'critical' : pred.h15 >= 3.0 ? 'attention' : 'normal'
}

const globalRisk = computed<'critical' | 'attention' | 'normal'>(() => {
  if (mainPredictions.value.some(p => riskAt15(p) === 'critical'))  return 'critical'
  if (mainPredictions.value.some(p => riskAt15(p) === 'attention')) return 'attention'
  return 'normal'
})

const globalMessage = computed(() => ({
  critical:  'Congestion critique prévue — intervention immédiate requise',
  attention: 'Densité élevée prévue — surveillance renforcée conseillée',
  normal:    'Situation stable sur les 15 prochaines minutes',
}[globalRisk.value]))

const globalDetail = computed(() => {
  const crit = mainPredictions.value.filter(p => riskAt15(p) === 'critical').map(p => `Zone ${p.zone}`)
  const att  = mainPredictions.value.filter(p => riskAt15(p) === 'attention').map(p => `Zone ${p.zone}`)
  if (crit.length) return `Zones critiques : ${crit.join(', ')}${att.length ? ' · À surveiller : ' + att.join(', ') : ''}`
  if (att.length)  return `Zones à surveiller : ${att.join(', ')}`
  return 'Toutes les zones restent sous le seuil d\'attention (3.0 p/m²)'
})

function recommendation(pred: Prediction): string {
  if (pred.h15 >= 4.0)  return `Évacuation partielle — ${pred.h15.toFixed(1)} p/m² attendu dans 15 min.`
  if (pred.h10 >= 4.0)  return `Seuil critique dans 10 min (${pred.h10.toFixed(1)} p/m²). Préparer évacuation.`
  if (pred.h15 >= 3.0)  return `Densité en hausse vers ${pred.h15.toFixed(1)} p/m². Surveiller.`
  if (pred.trend === 'up')   return 'Tendance haussière modérée. Surveillance standard.'
  if (pred.trend === 'down') return 'Zone en désengorgement progressif.'
  return 'Aucune action requise.'
}

useHead({ title: 'Prédictions — JOJ Dakar 2026' })
</script>
