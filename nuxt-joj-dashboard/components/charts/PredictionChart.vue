<template>
  <div class="panel p-4 h-full flex flex-col">
    <h3 class="font-mono text-xs text-white/50 uppercase tracking-wider mb-3 shrink-0">
      Évolution densité prédite — +5 / +10 / +15 min
    </h3>
    <v-chart class="flex-1 min-h-0" :option="option" autoresize />
  </div>
</template>

<script setup lang="ts">
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  GridComponent, TooltipComponent, LegendComponent,
  MarkLineComponent, MarkAreaComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import type { Prediction } from '~/types'

use([LineChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, MarkAreaComponent, CanvasRenderer])

const props = defineProps<{ predictions: Prediction[] }>()

const COLORS: Record<string, string> = { A: '#00853F', B: '#FDEF42', C: '#E31B23', D: '#60a5fa' }
const ZONE_LABELS = ['A', 'B', 'C', 'D']

const option = computed(() => ({
  backgroundColor: 'transparent',
  textStyle: { fontFamily: 'Space Mono', color: 'rgba(255,255,255,0.5)' },
  grid: { top: 40, right: 30, bottom: 50, left: 55, containLabel: true },
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(10,14,26,0.97)',
    borderColor: 'rgba(255,255,255,0.1)',
    padding: 12,
    textStyle: { color: '#e2e8f0', fontFamily: 'Space Mono', fontSize: 11 },
    formatter: (params: any[]) => {
      const horizon = params[0]?.axisValue
      let html = `<div style="margin-bottom:6px;font-weight:bold;color:rgba(255,255,255,0.7)">${horizon}</div>`
      params.forEach(p => {
        const v = p.value as number
        const risk = v >= 4.0 ? '⚠ CRITIQUE' : v >= 3.0 ? '⚡ ATTENTION' : '✓ Normal'
        const col  = v >= 4.0 ? '#E31B23' : v >= 3.0 ? '#FDEF42' : '#00853F'
        html += `<div style="display:flex;justify-content:space-between;gap:16px;margin:3px 0">
          <span>${p.marker} ${p.seriesName}</span>
          <span style="color:${col};font-weight:bold">${v.toFixed(2)} p/m² &nbsp;${risk}</span>
        </div>`
      })
      return html
    },
  },
  legend: {
    data: ZONE_LABELS.map(z => `Zone ${z}`),
    bottom: 0,
    textStyle: { color: 'rgba(255,255,255,0.5)', fontFamily: 'Space Mono', fontSize: 10 },
  },
  xAxis: {
    type: 'category',
    data: ['+5 min', '+10 min', '+15 min'],
    axisLabel: { color: 'rgba(255,255,255,0.6)', fontFamily: 'Space Mono', fontSize: 11 },
    axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
    axisTick: { show: false },
  },
  yAxis: {
    type: 'value',
    name: 'pers/m²',
    nameTextStyle: { color: 'rgba(255,255,255,0.3)', fontSize: 9 },
    axisLabel: { color: 'rgba(255,255,255,0.4)', fontSize: 10 },
    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
    min: 0,
  },
  series: [
    // Zones de risque en arrière-plan
    {
      type: 'line',
      data: [],
      markArea: {
        silent: true,
        data: [
          [
            { yAxis: 3.0, itemStyle: { color: 'rgba(253,239,66,0.06)' } },
            { yAxis: 4.0 },
          ],
          [
            { yAxis: 4.0, itemStyle: { color: 'rgba(227,27,35,0.08)' } },
            { yAxis: 9999 },
          ],
        ],
      },
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { type: 'dashed' },
        label: { fontFamily: 'Space Mono', fontSize: 9 },
        data: [
          {
            yAxis: 3.0,
            lineStyle: { color: 'rgba(253,239,66,0.5)' },
            label: { formatter: 'Seuil attention', color: 'rgba(253,239,66,0.6)', position: 'end' },
          },
          {
            yAxis: 4.0,
            lineStyle: { color: 'rgba(227,27,35,0.6)' },
            label: { formatter: 'Seuil critique', color: 'rgba(227,27,35,0.7)', position: 'end' },
          },
        ],
      },
    },
    // Séries par zone
    ...ZONE_LABELS.map(z => {
      const pred = props.predictions.find(p => p.zone === z)
      return {
        name: `Zone ${z}`,
        type: 'line',
        data: pred ? [pred.h5, pred.h10, pred.h15] : [0, 0, 0],
        smooth: false,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { color: COLORS[z], width: 2 },
        itemStyle: { color: COLORS[z], borderWidth: 2, borderColor: '#0a0e1a' },
        label: {
          show: true,
          position: 'top',
          formatter: (p: any) => `${(p.value as number).toFixed(1)}`,
          color: COLORS[z],
          fontFamily: 'Space Mono',
          fontSize: 10,
        },
        areaStyle: { opacity: 0.06, color: COLORS[z] },
      }
    }),
  ],
}))
</script>
