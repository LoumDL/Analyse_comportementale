# JOJ Dakar 2026 — Dashboard de Surveillance des Foules

Centre de commandement sécurité pour les Jeux Olympiques de la Jeunesse Dakar 2026.

## Stack
- **Nuxt 3** + Vue 3 + TypeScript
- **ECharts** / vue-echarts — graphiques temps réel
- **MapLibre GL** — carte interactive Dakar
- **Pinia** — state management
- **Socket.io** — WebSocket temps réel
- **TailwindCSS** — dark theme "Command Center Africain"

## Installation

```bash
npm install
npm run dev
```

Ouvre http://localhost:3000

## Configuration

Copie `.env.example` en `.env` :
```
NUXT_PUBLIC_WS_URL=ws://localhost:8000/ws/dashboard
NUXT_PUBLIC_API_URL=http://localhost:8000
```

Sans backend actif, les **mocks** (`data/mocks.ts`) sont utilisés automatiquement.

## Pages

| Route | Description |
|---|---|
| `/` | Dashboard principal — KPI + carte + sites + alertes |
| `/sites/:id` | Vue détaillée d'un site — zones + graphiques |
| `/predictions` | Prédictions TimeGPT +5/+10/+15 min |
| `/alertes` | Centre d'alertes filtrable + export CSV |
| `/rapport` | Bilan post-événement + export PDF |

## Backend (Python)

Le dashboard se connecte au backend FastAPI :
- WebSocket : `ws://localhost:8000/ws/dashboard`
- REST : `GET /api/sites`, `GET /api/alerts`, etc.
