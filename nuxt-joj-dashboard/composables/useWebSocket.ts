import { io, Socket } from 'socket.io-client'
import type { SiteUpdate, AlertEvent } from '~/types'

let socket: Socket | null = null

export function useWebSocket() {
  const config     = useRuntimeConfig()
  const uiStore    = useUiStore()
  const sitesStore = useSitesStore()
  const alertsStore = useAlertsStore()

  function connect() {
    if (socket?.connected) return
    uiStore.setWsStatus('connecting')

    socket = io(config.public.apiUrl, {
      path:          '/ws/socket.io',
      transports:    ['websocket'],
      reconnection:  true,
      reconnectionDelay:        1000,
      reconnectionDelayMax:     5000,
      reconnectionAttempts:     Infinity,
    })

    socket.on('connect', () => {
      uiStore.setWsStatus('connected')
      console.log('[WS] Connecté au backend')
    })

    socket.on('disconnect', () => {
      uiStore.setWsStatus('disconnected')
    })

    socket.on('connect_error', () => {
      uiStore.setWsStatus('disconnected')
    })

    socket.on('site_update', (data: SiteUpdate) => {
      sitesStore.updateSite(data.siteId, data.zones)
    })

    socket.on('alert', (data: AlertEvent) => {
      alertsStore.addAlert({
        ...data,
        siteName: sitesStore.getSiteById(data.siteId)?.name ?? data.siteId,
        resolved: false,
      })
    })
  }

  function disconnect() {
    socket?.disconnect()
    socket = null
  }

  onUnmounted(disconnect)

  return { connect, disconnect }
}
