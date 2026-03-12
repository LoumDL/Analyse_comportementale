export default defineNuxtConfig({
  devtools: { enabled: true },

  nitro: {
    preset: process.env.VERCEL ? 'vercel' : undefined,
  },

  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
    '@vueuse/nuxt',
    'nuxt-icon',
  ],

  css: ['~/assets/css/main.css'],

  app: {
    head: {
      title: 'JOJ Dakar 2026 — Centre de Commandement',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'color-scheme', content: 'dark' },
      ],
      link: [
        {
          rel: 'preconnect',
          href: 'https://fonts.googleapis.com',
        },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Orbitron:wght@400;600;700;900&family=DM+Sans:wght@300;400;500;600&display=swap',
        },
        {
          rel: 'stylesheet',
          href: 'https://unpkg.com/maplibre-gl@4.1.2/dist/maplibre-gl.css',
        },
      ],
    },
  },

  runtimeConfig: {
    public: {
      wsUrl: process.env.NUXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/dashboard',
      apiUrl: process.env.NUXT_PUBLIC_API_URL || 'http://localhost:8000',
    },
  },

  typescript: {
    strict: true,
  },

  build: {
    transpile: ['vue-echarts', 'echarts', 'resize-detector'],
  },

  vite: {
    optimizeDeps: {
      include: ['echarts/core', 'echarts/charts', 'echarts/components', 'echarts/renderers'],
    },
  },
})
