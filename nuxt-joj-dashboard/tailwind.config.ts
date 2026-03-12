import type { Config } from 'tailwindcss'

export default {
  content: [
    './components/**/*.{vue,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './plugins/**/*.ts',
    './app.vue',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg:      '#0A0E1A',
        surface: 'rgba(255,255,255,0.04)',
        border:  'rgba(255,255,255,0.08)',
        sn: {
          green:  '#00853F',
          yellow: '#FDEF42',
          red:    '#E31B23',
        },
      },
      fontFamily: {
        mono: ['Space Mono', 'monospace'],
        hud:  ['Orbitron', 'sans-serif'],
        body: ['DM Sans', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'flash':      'flash-update 0.6s ease-out',
      },
    },
  },
  plugins: [],
} satisfies Config
