<template>
  <aside
    :class="[
      'flex flex-col h-full transition-all duration-300 border-r border-white/5 bg-[#060911] z-40 shrink-0',
      expanded ? 'w-56' : 'w-16',
    ]"
  >
    <!-- Logo -->
    <div class="flex items-center gap-3 px-4 py-5 border-b border-white/5 min-h-[72px]">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-sn-green to-sn-yellow flex items-center justify-center shrink-0 font-hud text-black text-xs font-bold">
        JOJ
      </div>
      <transition name="fade">
        <div v-if="expanded" class="overflow-hidden">
          <p class="font-mono text-xs text-white/90 leading-tight">Dakar 2026</p>
          <p class="font-mono text-[10px] text-white/40 leading-tight">Sécu. Foules</p>
        </div>
      </transition>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 py-4 space-y-1 px-2">
      <NavItem
        v-for="item in navItems"
        :key="item.to"
        :item="item"
        :expanded="expanded"
      />
    </nav>

    <!-- Toggle & Status -->
    <div class="border-t border-white/5 px-2 py-3 space-y-2">
      <!-- WS Status -->
      <div v-if="expanded" class="flex items-center gap-2 px-2">
        <span
          :class="['w-2 h-2 rounded-full shrink-0 pulse', wsColor]"
        />
        <span class="text-[10px] font-mono text-white/50 truncate">{{ wsLabel }}</span>
      </div>
      <!-- Toggle button -->
      <button
        @click="uiStore.toggleSidebar()"
        class="w-full flex items-center justify-center h-8 rounded-lg text-white/40 hover:text-white/80 hover:bg-white/5 transition-colors"
      >
        <Icon :name="expanded ? 'heroicons:chevron-left' : 'heroicons:chevron-right'" class="w-4 h-4" />
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import NavItem from './NavItem.vue'
const uiStore  = useUiStore()
const expanded = computed(() => uiStore.sidebarExpanded)
const wsStatus = computed(() => uiStore.wsStatus)

const wsColor = computed(() => ({
  connected:    'bg-sn-green',
  connecting:   'bg-sn-yellow',
  disconnected: 'bg-sn-red',
}[wsStatus.value]))

const wsLabel = computed(() => ({
  connected:    'Connecté',
  connecting:   'Connexion…',
  disconnected: 'Hors ligne',
}[wsStatus.value]))

const navItems = [
  { to: '/',            icon: 'heroicons:squares-2x2',       label: 'Tableau de bord' },
  { to: '/predictions', icon: 'heroicons:chart-bar',          label: 'Prédictions'     },
  { to: '/alertes',     icon: 'heroicons:bell-alert',         label: 'Alertes'         },
  { to: '/cameras',     icon: 'heroicons:video-camera',       label: 'Caméras'         },
  { to: '/rapport',     icon: 'heroicons:document-chart-bar', label: 'Rapport'         },
]
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s, transform 0.2s; }
.fade-enter-from, .fade-leave-to       { opacity: 0; transform: translateX(-8px); }
</style>
