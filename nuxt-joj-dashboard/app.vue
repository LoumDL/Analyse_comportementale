<template>
  <div class="flex h-screen overflow-hidden bg-bg grid-bg font-body">
    <AppSidebar />
    <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
      <AppHeader />
      <main class="flex-1 overflow-auto p-4">
        <NuxtPage />
      </main>
      <StatusBar />
    </div>
  </div>
</template>

<script setup lang="ts">
import AppSidebar from '~/components/layout/AppSidebar.vue'
import AppHeader  from '~/components/layout/AppHeader.vue'
import StatusBar  from '~/components/layout/StatusBar.vue'

useHead({ htmlAttrs: { class: 'dark' } })
</script>
