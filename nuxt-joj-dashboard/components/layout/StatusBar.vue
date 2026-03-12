<template>
  <footer class="flex items-center justify-between px-6 py-1.5 border-t border-white/5 bg-[#060911]/60 text-[10px] font-mono text-white/30 shrink-0">
    <span>JOJ Dakar 2026 — Système d'Analyse Comportementale v1.0</span>
    <span>Dernière sync : {{ lastSync }}</span>
    <span :class="wsStatus === 'connected' ? 'text-sn-green' : 'text-sn-red'">
      WS {{ wsStatus.toUpperCase() }}
    </span>
  </footer>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
const uiStore  = useUiStore()
const wsStatus = computed(() => uiStore.wsStatus)
const lastSync = ref(dayjs().format('HH:mm:ss'))
useIntervalFn(() => { if (wsStatus.value === 'connected') lastSync.value = dayjs().format('HH:mm:ss') }, 5000)
</script>
