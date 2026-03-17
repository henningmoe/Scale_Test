# Cermaq Sustainability Dashboard (Frontend MVP)

Moderne frontend for bærekraftsrapportering bygget med:

- React + Vite
- Tailwind CSS
- Tremor (`@tremor/react`)

## Start lokalt

```bash
npm install
npm run dev
```

Åpne deretter URL-en Vite skriver ut (typisk `http://localhost:5173`).

## Hva som er bygget

- Enterprise dashboard-layout:
  - venstrestilt sidebar
  - toppbar med filter for lokalitet og dato
  - hovedinnhold i kort
- Tremor-komponenter:
  - `AreaChart` for utslippstrend
  - `BarChart` for slaktet volum
  - `BadgeDelta` for KPI-endring i CO2e og dødelighet
- Mock-datasett i `src/data/mockData.js` som simulerer felter fra Fishtalk/Power BI-modell.

## Neste steg

- Koble `VITE_API_BASE_URL` til API-gateway/Fishtalk-adapter
- Erstatte mockdata med ekte API-kall
- Legge på autentisering og rollebasert tilgang
