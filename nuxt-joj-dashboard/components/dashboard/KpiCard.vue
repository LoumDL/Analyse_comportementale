<template>
  <div :class="['panel p-5 flex items-center gap-4', critical ? 'glow-red' : '']">
    <div :class="['w-12 h-12 rounded-xl flex items-center justify-center shrink-0', iconBg]">
      <Icon :name="icon" :class="['w-6 h-6', iconColor]" />
    </div>
    <div class="flex-1 min-w-0">
      <p class="font-mono text-[10px] text-white/40 uppercase tracking-widest truncate">{{ label }}</p>
      <div class="flex items-end gap-2 mt-1">
        <LiveCounter :value="value" size="xl" :class="valueColor" />
        <span v-if="total" class="font-hud text-xl text-white/30 mb-1">/ {{ total }}</span>
      </div>
      <div v-if="trend !== undefined" class="flex items-center gap-1 mt-1">
        <Icon
          :name="trend >= 0 ? 'heroicons:arrow-trending-up' : 'heroicons:arrow-trending-down'"
          :class="['w-3 h-3', trend >= 0 ? 'text-sn-red' : 'text-sn-green']"
        />
        <span class="font-mono text-[10px] text-white/40">{{ trend >= 0 ? '+' : '' }}{{ trend }} / 5min</span>
      </div>
      <div v-if="critical !== undefined && critical > 0" class="mt-1">
        <span class="font-mono text-[10px] text-sn-red">{{ critical }} critique(s)</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import LiveCounter from './LiveCounter.vue'

const props = defineProps<{
  label:     string
  value:     number
  total?:    number
  icon:      string
  color:     'green' | 'yellow' | 'red'
  trend?:    number
  critical?: number
}>()

const colorMap = {
  green:  { bg:'bg-sn-green/10',  icon:'text-sn-green',  value:'text-sn-green'  },
  yellow: { bg:'bg-sn-yellow/10', icon:'text-sn-yellow', value:'text-sn-yellow' },
  red:    { bg:'bg-sn-red/10',    icon:'text-sn-red',    value:'text-sn-red'    },
}

const iconBg    = computed(() => colorMap[props.color].bg)
const iconColor = computed(() => colorMap[props.color].icon)
const valueColor = computed(() => colorMap[props.color].value)
</script>
