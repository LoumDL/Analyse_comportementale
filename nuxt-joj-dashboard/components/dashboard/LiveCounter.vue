<template>
  <span class="font-hud tabular-nums" :class="sizeClass">{{ displayValue.toLocaleString('fr-FR') }}</span>
</template>

<script setup lang="ts">
const props = defineProps<{ value: number; size?: 'sm' | 'md' | 'lg' | 'xl' }>()
const displayValue = ref(props.value)

watch(() => props.value, (newVal, oldVal) => {
  const diff  = newVal - oldVal
  const steps = 20
  const delta = diff / steps
  let current = oldVal
  const timer = setInterval(() => {
    current += delta
    displayValue.value = Math.round(current)
    if ((delta > 0 && current >= newVal) || (delta < 0 && current <= newVal)) {
      displayValue.value = newVal
      clearInterval(timer)
    }
  }, 30)
})

const sizeClass = computed(() => ({
  sm: 'text-sm',
  md: 'text-xl',
  lg: 'text-3xl',
  xl: 'text-5xl',
}[props.size ?? 'md']))
</script>
