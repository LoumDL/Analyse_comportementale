<template>
  <div class="panel p-4 h-full">
    <h3 class="font-mono text-xs text-white/50 uppercase tracking-wider mb-3">Flux Entrées / Sorties</h3>
    <v-chart class="w-full h-[220px]" :option="option" autoresize />
  </div>
</template>

<script setup lang="ts">
import { use }       from 'echarts/core'
import { BarChart }  from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import type { Site } from '~/types'

use([BarChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps<{ site: Site }>()

const zones  = computed(() => Object.keys(props.site.zones))
const option = computed(() => ({
  backgroundColor: 'transparent',
  textStyle: { fontFamily:'Space Mono', color:'rgba(255,255,255,0.5)' },
  grid: { top:30, right:10, bottom:30, left:40, containLabel:true },
  tooltip: {
    trigger:'axis', axisPointer:{ type:'shadow' },
    backgroundColor:'rgba(10,14,26,0.95)',
    borderColor:'rgba(255,255,255,0.1)',
    textStyle: { color:'#e2e8f0', fontFamily:'Space Mono', fontSize:11 },
  },
  legend: {
    data: ['Entrées', 'Sorties'],
    textStyle: { color:'rgba(255,255,255,0.5)', fontFamily:'Space Mono', fontSize:10 },
  },
  xAxis: {
    type: 'category',
    data: zones.value.map(z => `Zone ${z}`),
    axisLabel: { color:'rgba(255,255,255,0.5)', fontSize:10 },
    axisLine: { lineStyle: { color:'rgba(255,255,255,0.1)' } },
  },
  yAxis: {
    type: 'value',
    axisLabel: { color:'rgba(255,255,255,0.4)', fontSize:9 },
    splitLine: { lineStyle: { color:'rgba(255,255,255,0.05)' } },
  },
  series: [
    {
      name: 'Entrées',
      type: 'bar', barMaxWidth: 20,
      data: zones.value.map(z => props.site.zones[z].count),
      itemStyle: { color:'#00853F', borderRadius:[3,3,0,0] },
    },
    {
      name: 'Sorties',
      type: 'bar', barMaxWidth: 20,
      data: zones.value.map(z => Math.round(props.site.zones[z].count * 0.15)),
      itemStyle: { color:'#E31B23', borderRadius:[3,3,0,0] },
    },
  ],
}))
</script>
