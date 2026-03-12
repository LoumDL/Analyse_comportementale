import dayjs from 'dayjs'

export function useSiteData(siteId: Ref<string>) {
  const sitesStore = useSitesStore()
  const site       = computed(() => sitesStore.getSiteById(siteId.value))

  const densityHistory = ref<Record<string, { time: string; density: number }[]>>({
    A: [], B: [], C: [], D: [],
  })

  async function fetchHistory() {
    try {
      const config = useRuntimeConfig()
      const data   = await $fetch<Record<string, any[]>>(
        `${config.public.apiUrl}/api/sites/${siteId.value}/history`
      )
      densityHistory.value = data
    } catch {
      // backend absent — historique vide
    }
  }

  onMounted(fetchHistory)
  useIntervalFn(fetchHistory, 60_000)

  return { site, densityHistory, fetchHistory }
}
