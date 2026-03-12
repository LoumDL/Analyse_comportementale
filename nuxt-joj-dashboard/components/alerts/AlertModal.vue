<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="alertsStore.showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
        <div class="panel w-full max-w-2xl max-h-[80vh] overflow-y-auto">
          <!-- Header -->
          <div class="flex items-start justify-between p-6 border-b border-white/5">
            <div>
              <div class="flex items-center gap-3 mb-2">
                <AlertBadge :level="alert!.level" />
                <span class="font-mono text-xs text-white/50">{{ alert!.id }}</span>
              </div>
              <h2 class="font-mono text-sm text-white/90">{{ alert!.message }}</h2>
            </div>
            <button @click="alertsStore.closeModal()" class="text-white/30 hover:text-white/80 transition-colors ml-4">
              <Icon name="heroicons:x-mark" class="w-5 h-5" />
            </button>
          </div>

          <div class="p-6 space-y-6">
            <!-- Infos -->
            <div class="grid grid-cols-3 gap-4">
              <InfoTile label="Site"       :value="alert!.siteName" />
              <InfoTile label="Zone"       :value="`Zone ${alert!.zone}`" />
              <InfoTile label="Anomalie"   :value="alert!.anomalyType" />
              <InfoTile label="Confiance"  :value="`${(alert!.confidence * 100).toFixed(0)}%`" />
              <InfoTile label="Durée"      :value="alert!.duration ? `${alert!.duration} min` : '—'" />
              <InfoTile label="Statut"     :value="alert!.resolved ? 'Résolu' : 'Actif'" />
            </div>

            <!-- Recommandations -->
            <div>
              <h3 class="font-mono text-xs text-white/50 uppercase tracking-wider mb-3">Recommandations</h3>
              <ul class="space-y-2">
                <li v-for="rec in recommendations" :key="rec" class="flex items-start gap-2">
                  <Icon name="heroicons:chevron-right" class="w-3 h-3 text-sn-green mt-1 shrink-0" />
                  <span class="font-body text-sm text-white/70">{{ rec }}</span>
                </li>
              </ul>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex gap-3 p-6 pt-0">
            <button
              v-if="!alert!.resolved"
              @click="resolve()"
              class="px-4 py-2 bg-sn-green/20 border border-sn-green/30 text-sn-green font-mono text-xs rounded-lg hover:bg-sn-green/30 transition-colors"
            >
              Marquer résolu
            </button>
            <button
              @click="alertsStore.closeModal()"
              class="px-4 py-2 bg-white/5 border border-white/10 text-white/70 font-mono text-xs rounded-lg hover:bg-white/10 transition-colors"
            >
              Fermer
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import AlertBadge from './AlertBadge.vue'
const alertsStore = useAlertsStore()
const alert = computed(() => alertsStore.selected)

const recMap: Record<string, string[]> = {
  surcompression: ['Ouvrir les sorties de secours immédiates','Déployer agents sur le secteur','Stopper les entrées vers cette zone'],
  panic:          ['Déclencher protocole évacuation calme','Couper la musique','Activation haut-parleurs annonce calme'],
  chute:          ['Envoyer équipe médicale immédiatement','Dégager le périmètre','Contacter SAMU si nécessaire'],
  contre_flux:    ['Mettre en place barrières directionnelles','Agents aux points de convergence'],
  arret_masse:    ['Analyser cause de blocage','Fluidifier via annonces direction alternative'],
  accumulation:   ['Renforcer les sorties','Limiter temporairement les entrées'],
}

const recommendations = computed(() =>
  alert.value ? (recMap[alert.value.anomalyType] ?? ['Surveiller l\'évolution', 'Contacter le responsable de zone']) : []
)

function resolve() {
  if (alert.value) alertsStore.resolveAlert(alert.value.id)
  alertsStore.closeModal()
}
</script>

<script lang="ts">
// Helper component inline
const InfoTile = defineComponent({
  props: { label: String, value: String },
  template: `
    <div class="panel p-3">
      <p class="font-mono text-[10px] text-white/40 uppercase tracking-wider mb-1">{{ label }}</p>
      <p class="font-mono text-sm text-white/90">{{ value }}</p>
    </div>
  `,
})
</script>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s; }
.modal-enter-from, .modal-leave-to       { opacity: 0; }
</style>
