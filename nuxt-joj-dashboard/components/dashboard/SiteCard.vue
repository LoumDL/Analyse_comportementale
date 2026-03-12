<template>
  <NuxtLink
    :to="`/sites/${site.id}`"
    :class="[
      'panel p-4 block cursor-pointer transition-all duration-200 hover:border-white/20 hover:scale-[1.01]',
      site.status === 'critical' ? 'glow-red border-sn-red/30' :
      site.status === 'attention' ? 'border-sn-yellow/20' : '',
    ]"
  >
    <!-- Header -->
    <div class="flex items-start justify-between mb-3">
      <div class="flex-1 min-w-0">
        <h3 class="font-mono text-xs text-white/90 truncate">{{ site.name }}</h3>
        <p class="font-mono text-[10px] text-white/40 truncate mt-0.5">{{ site.address }}</p>
      </div>
      <ZoneIndicator :status="site.status as any" />
    </div>

    <!-- Compteur personnes -->
    <div class="mb-3">
      <LiveCounter :value="site.totalPersons" size="lg" :class="statusColor" />
      <p class="font-mono text-[10px] text-white/40 mt-0.5">personnes actives</p>
    </div>

    <!-- Zones mini-indicateurs -->
    <div class="grid grid-cols-4 gap-1 mt-3">
      <div
        v-for="(zone, key) in site.zones"
        :key="key"
        :class="['text-center py-1 rounded text-[10px] font-mono font-bold',
          zone.status === 'critical'  ? 'bg-sn-red/20 text-sn-red' :
          zone.status === 'attention' ? 'bg-sn-yellow/20 text-sn-yellow' :
                                        'bg-sn-green/10 text-sn-green'
        ]"
      >
        {{ key }}
      </div>
    </div>

    <!-- Flux -->
    <div class="flex gap-4 mt-3 pt-3 border-t border-white/5">
      <div class="flex items-center gap-1">
        <Icon name="heroicons:arrow-down-left" class="w-3 h-3 text-sn-green" />
        <span class="font-mono text-[10px] text-white/60">+{{ site.inCount.toLocaleString() }}</span>
      </div>
      <div class="flex items-center gap-1">
        <Icon name="heroicons:arrow-up-right" class="w-3 h-3 text-sn-red" />
        <span class="font-mono text-[10px] text-white/60">-{{ site.outCount.toLocaleString() }}</span>
      </div>
    </div>
  </NuxtLink>
</template>

<script setup lang="ts">
import type { Site } from '~/types'
import ZoneIndicator from './ZoneIndicator.vue'
import LiveCounter   from './LiveCounter.vue'

defineProps<{ site: Site }>()

const statusColor = computed(() => '')  // handled by ZoneIndicator
</script>
