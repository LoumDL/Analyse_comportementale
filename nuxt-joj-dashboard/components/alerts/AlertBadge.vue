<template>
  <span :class="['inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-mono font-bold border', classes]">
    {{ icon }} {{ label }}
  </span>
</template>

<script setup lang="ts">
const props = defineProps<{ level: 'info' | 'warning' | 'critical' }>()
const map = {
  critical: { label:'CRITIQUE', icon:'🔴', classes:'bg-sn-red/15 text-sn-red border-sn-red/30' },
  warning:  { label:'ALERTE',   icon:'⚠️', classes:'bg-sn-yellow/15 text-sn-yellow border-sn-yellow/30' },
  info:     { label:'INFO',     icon:'🔵', classes:'bg-blue-500/15 text-blue-400 border-blue-400/30' },
}
const { label, icon, classes } = map[props.level]
</script>
