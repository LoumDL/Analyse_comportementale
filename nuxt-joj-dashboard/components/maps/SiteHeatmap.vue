<template>
  <div class="panel overflow-hidden h-full" style="min-height:400px">
    <div ref="mapContainer" class="w-full h-full" />
  </div>
</template>

<script setup lang="ts">
import type { Site } from '~/types'

const props = defineProps<{ sites: Site[] }>()
const mapContainer = ref<HTMLDivElement>()
let map: any = null

const statusColor: Record<string, string> = {
  normal:    '#00853F',
  attention: '#FDEF42',
  critical:  '#E31B23',
  offline:   '#6b7280',
}

onMounted(async () => {
  if (!mapContainer.value) return
  const maplibre = await import('maplibre-gl')
  const { Map, Marker, Popup, NavigationControl } = maplibre.default ?? maplibre

  map = new Map({
    container: mapContainer.value,
    style: {
      version: 8,
      sources: {
        'osm': {
          type: 'raster',
          tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
          tileSize: 256,
          attribution: '© OpenStreetMap contributors',
        },
      },
      layers: [{ id:'osm', type:'raster', source:'osm' }],
    },
    center:  [-17.38, 14.71],
    zoom:    11,
    attributionControl: false,
  })

  map.addControl(new NavigationControl(), 'top-right')

  // Filtre CSS dark pour la carte
  const canvas = mapContainer.value.querySelector('canvas')
  if (canvas) {
    canvas.style.filter = 'brightness(0.4) contrast(1.2) saturate(0.7)'
  }

  map.on('load', () => {
    props.sites.forEach(site => {
      const color = statusColor[site.status] ?? '#6b7280'
      const el = document.createElement('div')
      el.innerHTML = `
        <div style="
          width:36px; height:36px; border-radius:50%;
          background:${color}22; border:2px solid ${color};
          display:flex; align-items:center; justify-content:center;
          font-family:Space Mono; font-size:9px; color:${color};
          cursor:pointer; box-shadow: 0 0 12px ${color}66;
        ">
          <span style="font-weight:bold">${site.totalPersons > 999 ? (site.totalPersons/1000).toFixed(1)+'k' : site.totalPersons}</span>
        </div>
      `
      const popup = new Popup({ offset:20, className:'map-popup' })
        .setHTML(`
          <div style="font-family:Space Mono; font-size:11px; color:#e2e8f0; padding:4px;">
            <strong>${site.name}</strong><br/>
            ${site.totalPersons.toLocaleString()} personnes<br/>
            <span style="color:${color}">${site.status.toUpperCase()}</span>
          </div>
        `)
      new Marker({ element: el })
        .setLngLat([site.lng, site.lat])
        .setPopup(popup)
        .addTo(map)
    })
  })
})

onUnmounted(() => map?.remove())
</script>

<style>
.maplibregl-popup-content {
  background: rgba(10,14,26,0.95) !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
  border-radius: 8px !important;
  padding: 8px 12px !important;
}
.maplibregl-popup-tip { display: none !important; }
.maplibregl-ctrl-group { background: rgba(10,14,26,0.9) !important; border: 1px solid rgba(255,255,255,0.1) !important; }
.maplibregl-ctrl-group button { color: rgba(255,255,255,0.7) !important; }
</style>
