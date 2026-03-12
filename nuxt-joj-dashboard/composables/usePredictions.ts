import type { Prediction } from '~/types'

export function usePredictions(siteId: Ref<string>) {
  const predictions = ref<Prediction[]>([])
  const loading     = ref(false)

  async function fetchPredictions() {
    loading.value = true
    try {
      const config  = useRuntimeConfig()
      const data    = await $fetch<Prediction[]>(
        `${config.public.apiUrl}/api/sites/${siteId.value}/predictions`
      )
      predictions.value = data
    } catch {
      // backend absent — on conserve les données existantes
    } finally {
      loading.value = false
    }
  }

  useIntervalFn(fetchPredictions, 60_000)
  onMounted(fetchPredictions)

  return { predictions, loading, fetchPredictions }
}
