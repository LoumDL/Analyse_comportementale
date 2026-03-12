import { defineStore } from 'pinia'
import type { Site } from '~/types'

const EMPTY_SITE: Site = {
  id:           'site-principal',
  name:         'Mon site',
  address:      '',
  lat:          14.7247,
  lng:          -17.4591,
  capacity:     0,
  totalPersons: 0,
  inCount:      0,
  outCount:     0,
  status:       'normal',
  lastUpdate:   new Date().toISOString(),
  zones:        {},
}

export const useSitesStore = defineStore('sites', () => {
  const site    = ref<Site>({ ...EMPTY_SITE })
  const loading = ref(false)

  const sites        = computed(() => [site.value])
  const totalPersons = computed(() => site.value.totalPersons)
  const sitesOk      = computed(() => site.value.status === 'normal' ? 1 : 0)

  function getSiteById(_id: string) { return site.value }

  function updateSite(_siteId: string, zones: Record<string, { count: number; density: number; avgSpeed: number }>) {
    let total = 0
    for (const [zoneId, data] of Object.entries(zones)) {
      if (!site.value.zones[zoneId]) {
        site.value.zones[zoneId] = { id: zoneId, count: 0, density: 0, avgSpeed: 0, status: 'normal' }
      }
      site.value.zones[zoneId].count    = data.count
      site.value.zones[zoneId].density  = data.density
      site.value.zones[zoneId].avgSpeed = data.avgSpeed
      site.value.zones[zoneId].status   =
        data.density >= 4.0 ? 'critical' :
        data.density >= 3.0 ? 'attention' : 'normal'
      total += data.count
    }
    site.value.totalPersons = total
    site.value.lastUpdate   = new Date().toISOString()
    site.value.status =
      Object.values(site.value.zones).some(z => z.status === 'critical')  ? 'critical' :
      Object.values(site.value.zones).some(z => z.status === 'attention') ? 'attention' : 'normal'
  }

  function applyConfig(cfg: { name: string }) {
    site.value.name = cfg.name
  }

  async function fetchSite() {
    loading.value = true
    try {
      const config = useRuntimeConfig()
      const data   = await $fetch<Site>(`${config.public.apiUrl}/api/site`)
      site.value   = data
    } catch {
      // backend absent — on garde l'état actuel
    } finally {
      loading.value = false
    }
  }

  function resetZones() {
    site.value.zones        = {}
    site.value.totalPersons = 0
    site.value.status       = 'normal'
  }

  return {
    site, sites, loading,
    totalPersons, sitesOk,
    getSiteById, updateSite, applyConfig, fetchSite, resetZones,
  }
})
