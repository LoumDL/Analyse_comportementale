<template>
  <div class="panel p-4 h-full">
    <h3 class="font-mono text-xs text-white/50 uppercase tracking-wider mb-3">Densité — 30 dernières minutes</h3>
    <v-chart class="w-full h-[280px]" :option="option" autoresize />
  </div>
</template>

<script setup lang="ts">
import { use }        from 'echarts/core'
import { LineChart }  from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, MarkLineComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import dayjs  from 'dayjs'

use([LineChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, CanvasRenderer])

const props = defineProps<{
  history: Record<string, { time: string; density: number }[]>
}>()

const ZONE_COLORS = { A:'#00853F', B:'#FDEF42', C:'#E31B23', D:'#60a5fa' }

const option = computed(() => ({
  backgroundColor: 'transparent',
  textStyle: { fontFamily:'Space Mono', color:'rgba(255,255,255,0.5)' },
  grid: { top:30, right:20, bottom:40, left:50, containLabel: true },
  tooltip: {
    trigger:'axis',
    backgroundColor:'rgba(10,14,26,0.95)',
    borderColor:'rgba(255,255,255,0.1)',
    textStyle:{ color:'#e2e8f0', fontFamily:'Space Mono', fontSize:11 },
  },
  legend: {
    data: Object.keys(props.history).map(z => `Zone ${z}`),
    textStyle: { color:'rgba(255,255,255,0.5)', fontFamily:'Space Mono', fontSize:10 },
    top: 0,
  },
  xAxis: {
    type: 'category',
    data: (props.history.A ?? []).map(p => p.time),
    axisLine: { lineStyle: { color:'rgba(255,255,255,0.1)' } },
    axisLabel: { color:'rgba(255,255,255,0.4)', fontSize:9 },
    splitLine: { show:false },
  },
  yAxis: {
    type: 'value',
    name: 'pers/m²',
    nameTextStyle: { color:'rgba(255,255,255,0.3)', fontSize:9 },
    axisLine: { lineStyle:{ color:'rgba(255,255,255,0.1)' } },
    axisLabel: { color:'rgba(255,255,255,0.4)', fontSize:9 },
    splitLine: { lineStyle:{ color:'rgba(255,255,255,0.05)' } },
  },
  series: Object.entries(props.history).map(([zone, data]) => ({
    name:  `Zone ${zone}`,
    type:  'line',
    data:  data.map(p => p.density.toFixed(2)),
    smooth: true,
    symbol: 'none',
    lineStyle: { color: ZONE_COLORS[zone as keyof typeof ZONE_COLORS], width:2 },
    areaStyle: zone === 'C' ? { color:'rgba(227,27,35,0.08)' } : undefined,
    markLine: zone === 'C' ? {
      silent: true,
      lineStyle: { color:'rgba(227,27,35,0.4)', type:'dashed' },
      data: [{ yAxis: 3.5, label: { formatter:'Seuil', color:'rgba(227,27,35,0.6)', fontSize:9 } }],
    } : undefined,
  })),
}))
</script>
