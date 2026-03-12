<template>
  <NuxtLink
    :to="item.to"
    :class="[
      'flex items-center gap-3 px-2 py-2.5 rounded-lg transition-all duration-150 group',
      isActive
        ? 'bg-sn-green/15 text-sn-green border border-sn-green/20'
        : 'text-white/50 hover:text-white/90 hover:bg-white/5',
    ]"
  >
    <Icon :name="item.icon" class="w-5 h-5 shrink-0" />
    <transition name="fade">
      <span v-if="expanded" class="text-sm font-mono truncate">{{ item.label }}</span>
    </transition>
    <!-- Badge alertes -->
    <transition name="fade">
      <span
        v-if="expanded && item.to === '/alertes' && criticalCount > 0"
        class="ml-auto bg-sn-red text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full"
      >
        {{ criticalCount }}
      </span>
    </transition>
  </NuxtLink>
</template>

<script setup lang="ts">
const props  = defineProps<{ item: { to: string; icon: string; label: string }; expanded: boolean }>()
const route  = useRoute()
const alertsStore = useAlertsStore()
const isActive    = computed(() => route.path === props.item.to || (props.item.to !== '/' && route.path.startsWith(props.item.to)))
const criticalCount = computed(() => alertsStore.criticalCount)
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s; }
.fade-enter-from, .fade-leave-to       { opacity: 0; }
</style>
