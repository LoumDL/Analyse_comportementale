import { defineStore } from 'pinia'
import type { Alert } from '~/types'
import dayjs from 'dayjs'

export const useAlertsStore = defineStore('alerts', () => {
  const alerts    = ref<Alert[]>([])
  const selected  = ref<Alert | null>(null)
  const showModal = ref(false)

  const activeAlerts = computed(() =>
    alerts.value.filter(a => !a.resolved)
  )

  const criticalCount = computed(() =>
    activeAlerts.value.filter(a => a.level === 'critical').length
  )

  const warningCount = computed(() =>
    activeAlerts.value.filter(a => a.level === 'warning').length
  )

  function addAlert(alert: Alert) {
    alerts.value.unshift(alert)
    if (alerts.value.length > 200) alerts.value.pop()
  }

  function resolveAlert(id: string) {
    const a = alerts.value.find(a => a.id === id)
    if (a) a.resolved = true
  }

  function openAlert(alert: Alert) {
    selected.value  = alert
    showModal.value = true
  }

  function closeModal() {
    showModal.value = false
    selected.value  = null
  }

  function exportCsv(filtered: Alert[]) {
    const header = 'Heure,Niveau,Site,Zone,Anomalie,Durée,Confiance\n'
    const rows   = filtered.map(a =>
      `${dayjs(a.timestamp).format('HH:mm:ss')},${a.level},${a.siteName},${a.zone},${a.anomalyType},${a.duration ?? '-'},${(a.confidence * 100).toFixed(0)}%`
    ).join('\n')
    const blob = new Blob([header + rows], { type: 'text/csv;charset=utf-8;' })
    const url  = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href     = url
    link.download = `alertes_joj_${dayjs().format('YYYYMMDD_HHmmss')}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  async function fetchAlerts() {
    try {
      const config = useRuntimeConfig()
      const data   = await $fetch<Alert[]>(`${config.public.apiUrl}/api/alerts?limit=200`)
      alerts.value = data
    } catch {
      // conserve les données existantes si backend absent
    }
  }

  function clearAll() { alerts.value = [] }

  return {
    alerts, selected, showModal,
    activeAlerts, criticalCount, warningCount,
    addAlert, resolveAlert, openAlert, closeModal, exportCsv, fetchAlerts, clearAll,
  }
})
