<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/80 backdrop-blur-sm"
        @click.self="$emit('close')"
      >
        <div class="panel w-full max-w-4xl flex flex-col" style="height: 70vh;">
          <!-- Header -->
          <div class="flex items-center justify-between px-4 py-3 border-b border-white/5 shrink-0">
            <div class="flex items-center gap-2">
              <span :class="['w-2 h-2 rounded-full shrink-0', hasFrame ? 'bg-sn-red pulse' : 'bg-white/20']" />
              <span class="font-mono text-xs text-white/70">{{ sitesStore.site.name }}</span>
              <span v-if="hasFrame" class="font-hud text-[10px] text-sn-red tracking-widest ml-1">LIVE</span>
            </div>
            <button @click="$emit('close')" class="text-white/30 hover:text-white/80 transition-colors">
              <Icon name="heroicons:x-mark" class="w-5 h-5" />
            </button>
          </div>

          <!-- Flux -->
          <div class="relative flex-1 bg-black flex items-center justify-center overflow-hidden">
            <img
              v-if="hasFrame"
              :src="frameSrc"
              class="w-full h-full object-contain"
              alt="Flux caméra"
            />
            <div v-else class="absolute inset-0 flex flex-col items-center justify-center gap-3">
              <Icon name="heroicons:video-camera-slash" class="w-10 h-10 text-white/20" />
              <p class="font-mono text-xs text-white/40">En attente du flux…</p>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { io } from 'socket.io-client'
import { useSitesStore } from '~/stores/sites'

const props = defineProps<{ show: boolean }>()
defineEmits<{ close: [] }>()

const sitesStore = useSitesStore()
const config     = useRuntimeConfig()
const frameSrc   = ref('')
const hasFrame   = ref(false)

let socket: ReturnType<typeof io> | null = null

watch(() => props.show, (open) => {
  if (open) {
    socket = io(config.public.apiUrl, { path: '/ws/socket.io', transports: ['websocket'] })
    socket.on('frame', (b64: string) => {
      frameSrc.value = `data:image/jpeg;base64,${b64}`
      hasFrame.value = true
    })
  } else {
    socket?.disconnect()
    socket = null
    frameSrc.value = ''
    hasFrame.value = false
  }
})

onUnmounted(() => { socket?.disconnect() })
</script>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: opacity 0.2s; }
.modal-enter-from, .modal-leave-to       { opacity: 0; }
</style>
