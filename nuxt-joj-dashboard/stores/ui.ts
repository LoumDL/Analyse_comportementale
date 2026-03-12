import { defineStore } from 'pinia'

export const useUiStore = defineStore('ui', () => {
  const sidebarExpanded = ref(true)
  const locale          = ref<'fr' | 'en'>('fr')
  const wsStatus        = ref<'connected' | 'connecting' | 'disconnected'>('disconnected')

  function toggleSidebar()       { sidebarExpanded.value = !sidebarExpanded.value }
  function setLocale(l: 'fr'|'en') { locale.value = l }
  function setWsStatus(s: 'connected'|'connecting'|'disconnected') { wsStatus.value = s }

  return { sidebarExpanded, locale, wsStatus, toggleSidebar, setLocale, setWsStatus }
})
