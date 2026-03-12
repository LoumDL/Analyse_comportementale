<template>
  <div class="flex items-center gap-2">
    <span
      :class="['inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-mono font-semibold border', statusClass]"
    >
      <span :class="['w-1.5 h-1.5 rounded-full', dotClass]" />
      {{ label }}
    </span>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ status: 'normal' | 'attention' | 'critical' }>()

const labels = { normal:'NORMALE', attention:'ATTENTION', critical:'CRITIQUE' }
const label  = computed(() => labels[props.status])

const statusClass = computed(() => ({
  normal:    'border-sn-green/30 text-sn-green bg-sn-green/10',
  attention: 'border-sn-yellow/30 text-sn-yellow bg-sn-yellow/10',
  critical:  'border-sn-red/30 text-sn-red bg-sn-red/10 glow-red',
}[props.status]))

const dotClass = computed(() => ({
  normal:    'bg-sn-green',
  attention: 'bg-sn-yellow',
  critical:  'bg-sn-red pulse',
}[props.status]))
</script>
