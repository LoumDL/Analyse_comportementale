<template>
  <div v-if="site" class="h-full flex flex-col gap-4">
    <!-- Header site -->
    <div class="flex items-center gap-4 shrink-0">
      <NuxtLink to="/" class="text-white/40 hover:text-white/80 transition-colors">
        <Icon name="heroicons:arrow-left" class="w-5 h-5" />
      </NuxtLink>
      <div>
        <h1 class="font-hud text-lg text-white/90">{{ site.name }}</h1>
        <p class="font-mono text-xs text-white/40">{{ site.address }}</p>
      </div>
      <ZoneIndicator :status="site.status as any" class="ml-auto" />
    </div>

    <!-- Zones panel + density chart -->
    <div class="grid grid-cols-3 gap-4 flex-1 min-h-0">
      <!-- Zones métriques -->
      <div class="panel p-4 space-y-3">
        <h2 class="font-mono text-xs text-white/50 uppercase tracking-wider mb-4">Zones en temps réel</h2>
        <div v-for="(zone, key) in site.zones" :key="key" class="space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="font-mono text-xs text-white/70">Zone {{ key }}</span>
            <ZoneIndicator :status="zone.status as any" />
          </div>
          <div class="flex items-center gap-3">
            <div class="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
              <div
                :class="['h-full rounded-full transition-all duration-500',
                  zone.status === 'critical' ? 'bg-sn-red' : zone.status === 'attention' ? 'bg-sn-yellow' : 'bg-sn-green'
                ]"
                :style="{ width: `${Math.min(100, (zone.density / 6) * 100)}%` }"
              />
            </div>
            <span class="font-hud text-xs text-white/70 tabular-nums w-16 text-right">
              {{ zone.count }} pers
            </span>
          </div>
          <p class="font-mono text-[10px] text-white/30">
            {{ zone.density.toFixed(1) }} p/m² · v̄={{ zone.avgSpeed.toFixed(1) }} m/s
          </p>
        </div>

      </div>

      <!-- Density Timeline -->
      <div class="col-span-2">
        <DensityTimeline :history="densityHistory" class="h-full" />
      </div>
    </div>

    <!-- Flow chart -->
    <div class="grid grid-cols-2 gap-4 shrink-0">
      <FlowBarChart :site="site" />
      <PredictionChart :predictions="predictions" />
    </div>
  </div>

  <div v-else class="flex items-center justify-center h-full">
    <p class="font-mono text-white/40">Site introuvable : {{ $route.params.id }}</p>
  </div>
</template>

<script setup lang="ts">
import ZoneIndicator  from '~/components/dashboard/ZoneIndicator.vue'
import DensityTimeline from '~/components/charts/DensityTimeline.vue'
import FlowBarChart   from '~/components/charts/FlowBarChart.vue'
import PredictionChart from '~/components/charts/PredictionChart.vue'

const route   = useRoute()
const siteId  = computed(() => route.params.id as string)
const { site, densityHistory } = useSiteData(siteId)
const { predictions }          = usePredictions(siteId)

useHead({ title: computed(() => `${site.value?.name ?? '—'} — JOJ 2026`) })
</script>
