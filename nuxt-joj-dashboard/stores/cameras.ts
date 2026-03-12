import { defineStore } from 'pinia'

export interface Camera {
  id:     string
  name:   string
  source: string
  zones:  string[]
  active: boolean
  status: 'online' | 'offline' | 'unknown'
}

const DEFAULTS: Camera[] = [
  { id: 'cam-1', name: 'Caméra principale', source: 'http://localhost:8000/api/stream', zones: ['A', 'B'], active: true,  status: 'unknown' },
  { id: 'cam-2', name: 'Entrée nord',        source: '',                                 zones: ['C'],       active: false, status: 'offline' },
  { id: 'cam-3', name: 'Sortie sud',         source: '',                                 zones: ['D'],       active: false, status: 'offline' },
]

export const useCamerasStore = defineStore('cameras', () => {
  const cameras = ref<Camera[]>(DEFAULTS.map(c => ({ ...c })))

  function addCamera(cam: Omit<Camera, 'id' | 'status'>) {
    cameras.value.push({ ...cam, id: `cam-${Date.now()}`, status: 'unknown' })
    _persist()
  }

  function updateCamera(id: string, updates: Partial<Omit<Camera, 'id'>>) {
    const idx = cameras.value.findIndex(c => c.id === id)
    if (idx >= 0) { cameras.value[idx] = { ...cameras.value[idx], ...updates }; _persist() }
  }

  function removeCamera(id: string) {
    cameras.value = cameras.value.filter(c => c.id !== id)
    _persist()
  }

  function setStatus(id: string, status: Camera['status']) {
    const cam = cameras.value.find(c => c.id === id)
    if (cam) cam.status = status
  }

  function _persist() {
    if (import.meta.client) localStorage.setItem('joj_cameras', JSON.stringify(cameras.value))
  }

  function restore() {
    if (!import.meta.client) return
    try {
      const saved = localStorage.getItem('joj_cameras')
      if (saved) cameras.value = JSON.parse(saved)
    } catch { /* ignore */ }
  }

  return { cameras, addCamera, updateCamera, removeCamera, setStatus, restore }
})
