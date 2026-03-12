<template>
  <div class="w-full">
    <div class="flex justify-between items-center mb-1">
      <span class="font-mono text-[10px] text-white/50 uppercase tracking-wider">Capacité</span>
      <span class="font-hud text-sm" :class="gaugeColor">{{ pct }}%</span>
    </div>
    <div class="h-2 bg-white/5 rounded-full overflow-hidden">
      <div
        :class="['h-full rounded-full transition-all duration-700', barClass]"
        :style="{ width: `${pct}%` }"
      />
    </div>
    <div class="flex justify-between mt-1">
      <span class="font-mono text-[10px] text-white/30">{{ current.toLocaleString() }} pers</span>
      <span class="font-mono text-[10px] text-white/30">/ {{ capacity.toLocaleString() }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ current: number; capacity: number }>()
const pct   = computed(() => Math.min(100, Math.round((props.current / props.capacity) * 100)))

const gaugeColor = computed(() =>
  pct.value >= 90 ? 'text-sn-red' : pct.value >= 70 ? 'text-sn-yellow' : 'text-sn-green'
)
const barClass = computed(() =>
  pct.value >= 90
    ? 'bg-gradient-to-r from-sn-red to-red-400'
    : pct.value >= 70
    ? 'bg-gradient-to-r from-sn-yellow to-yellow-300'
    : 'bg-gradient-to-r from-sn-green to-emerald-400'
)
</script>
