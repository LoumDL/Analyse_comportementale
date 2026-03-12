<template>
  <div class="panel h-full flex flex-col overflow-hidden">
    <div class="flex items-center justify-between px-4 py-3 border-b border-white/5 shrink-0">
      <h2 class="font-mono text-xs text-white/70 uppercase tracking-widest">Flux d'alertes</h2>
      <span class="font-hud text-xs text-sn-red">{{ alertsStore.criticalCount }} critiques</span>
    </div>
    <div class="flex-1 overflow-y-auto space-y-1 p-2">
      <TransitionGroup name="alert-slide">
        <div
          v-for="alert in recentAlerts"
          :key="alert.id"
          @click="alertsStore.openAlert(alert)"
          :class="[
            'flex items-start gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors hover:bg-white/5',
            alert.level === 'critical' ? 'border-l-2 border-sn-red' :
            alert.level === 'warning'  ? 'border-l-2 border-sn-yellow' :
                                         'border-l-2 border-blue-400',
          ]"
        >
          <div class="shrink-0 mt-0.5">
            <AlertBadge :level="alert.level" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="font-mono text-[11px] text-white/80 truncate">{{ alert.message }}</p>
            <p class="font-mono text-[10px] text-white/40 mt-0.5">
              {{ alert.siteName }} · Zone {{ alert.zone }} · {{ formatTime(alert.timestamp) }}
            </p>
          </div>
          <span v-if="!alert.resolved" class="w-1.5 h-1.5 rounded-full bg-sn-red pulse shrink-0 mt-1.5" />
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs'
import AlertBadge from './AlertBadge.vue'
const alertsStore = useAlertsStore()
const recentAlerts = computed(() => alertsStore.alerts.slice(0, 30))
const formatTime   = (ts: string) => dayjs(ts).format('HH:mm:ss')
</script>

<style scoped>
.alert-slide-enter-active { transition: opacity 0.2s ease; }
.alert-slide-enter-from   { opacity: 0; }
.alert-slide-move         { transition: none; }
</style>
