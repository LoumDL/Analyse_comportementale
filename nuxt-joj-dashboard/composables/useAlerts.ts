import type { Alert } from '~/types'

export function useAlerts() {
  const alertsStore = useAlertsStore()

  const filterLevel  = ref<string>('all')
  const filterSite   = ref<string>('all')
  const filterType   = ref<string>('all')
  const searchQuery  = ref('')
  const sortBy       = ref<'time' | 'level'>('time')

  const levelWeight = { critical: 3, warning: 2, info: 1 }

  const filtered = computed(() => {
    let result = alertsStore.alerts

    if (filterLevel.value !== 'all')
      result = result.filter(a => a.level === filterLevel.value)

    if (filterSite.value !== 'all')
      result = result.filter(a => a.siteId === filterSite.value)

    if (filterType.value !== 'all')
      result = result.filter(a => a.anomalyType === filterType.value)

    if (searchQuery.value)
      result = result.filter(a =>
        a.message.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        a.siteName.toLowerCase().includes(searchQuery.value.toLowerCase())
      )

    if (sortBy.value === 'level')
      result = [...result].sort((a, b) => levelWeight[b.level] - levelWeight[a.level])

    return result
  })

  return {
    filtered, filterLevel, filterSite, filterType, searchQuery, sortBy,
    exportCsv: () => alertsStore.exportCsv(filtered.value),
  }
}
