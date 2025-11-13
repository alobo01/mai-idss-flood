# Flood Prediction Frontend Mock — React Plan & Mock Data

**Goal:** Deliver a clickable, role-based React mock that validates navigation, maps, alerts, and resource allocation for a flood-prediction system. Everything runs locally with mocked but realistic data. Dark mode by default; English-only.

---

## 1) Roles & Permissions Matrix

| Role              | Primary Goals                                                            | Can View                                                                              | Can Edit                                                                | Cannot                                                         |
| ----------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------------------- |
| **Administrator** | Register regions/zones, resources, users, thresholds & rules             | All admin screens, maps, plans                                                        | Resources (locations, counts), thresholds, zones, users/roles           | Trigger live ops actions, modify published plan contents       |
| **Planner**       | Review prediction outputs, review resources, propose edits to draft plan | Risk map, alerts, resources, scenario workbench, plan                                 | Propose plan edits, run what-if scenarios, submit draft for approval    | Edit users/resources directly (read-only view), alter live ops |
| **Coordinator**   | Execute the approved plan; monitor real-time ops; communicate with crews | Ops board, allocation map, crew locations/telemetry, alerts & comms                   | Acknowledge/resolve alerts, send predefined actions/commands, log comms | Change the plan or thresholds                                  |
| **Data Analyst**  | Inspect model outputs and impacts                                        | Analysis dashboard: risk layers, infra/human damage overlays, weighted views, exports | Export images/CSV of layers                                             | Edit resources/plan                                            |

> **Note:** All roles can view the **Risk Map** with their respective overlays and permissions. Planner sees “Propose Edit” actions; Coordinator sees “Send Action / Acknowledge”; Admin sees “Configure”.

---

## 2) Information Architecture (Routes)

```
/                     → Role chooser (for mock) / Login
/planner
  /planner/map        → Risk Map + details
  /planner/scenarios  → What‑if & plan drafting
  /planner/alerts     → Alerts timeline & details
/coordinator
  /coordinator/ops    → Live Ops Board (Kanban + comms)
  /coordinator/resources → Allocation map/table (read-only plan)
/admin
  /admin/regions      → Zones/GeoJSON manager
  /admin/thresholds   → Risk bands & alert rules
  /admin/resources    → Resource catalog (pumps, crews, sandbags)
  /admin/users        → Users & roles (mocked)
/analyst
  /analyst/overview   → Multi-layer analytical map (risk & damage)
  /analyst/exports    → Snapshots & CSV exports
```

* **Routing**: React Router v6; role guard hides disallowed tabs and disables restricted actions.
* **Dark Mode**: Tailwind `dark` class; default dark; toggle in header.

---

## 3) Key Screens (by Role)

### Planner — Risk Map

* **Controls**: time horizon (6–72h), layer toggles (risk, rivers, gauges, assets), thresholds.
* **Map**: heat layer (risk), zone polygons colored by band, critical assets (hospitals, schools), flood gauges.
* **Details Panel**: selected zone → risk score, top drivers (rainfall/gauge/saturation), recommended actions, link to scenario.
* **Actions**: “Add to Plan”, “Propose Edit”, export PNG.

### Planner — Scenarios (What‑if)

* **Inputs**: weather severity slider, resource availability (crews/equipment), threshold deltas.
* **Outputs**: ranked zones, expected coverage, notes on false‑negatives risk, draft plan diff vs baseline.
* **CTA**: “Submit Draft Plan”.

### Planner — Alerts

* **Timeline**: upcoming/current alerts with severity badges; filters by zone/severity.
* **Drawer**: rationale, impacted assets, proposed actions; option to mark as “for coordinator attention”.

### Coordinator — Live Ops Board

* **Kanban**: Tasks (Queued → In‑Progress → Done), each with zone, action, crew, ETA.
* **Comms**: per‑task and global channels; predefined quick actions (see below).
* **Map**: crews as markers; routes to assigned zones; status pulses; alert count.
* **Predefined actions** (configurable): `Start Deployment`, `Evacuate Segment`, `Block Road`, `Report Water Level`, `Request Backup`, `Stand Down`, `ETA Update`, `Safety Check`, `Battery Low`, `Send Photo`.

### Coordinator — Resource Allocation (read‑only plan)

* **Table + Map Sync**: zone → required assets & assigned crews; cannot edit plan but can **acknowledge** or **flag issues**.
* **Metrics**: coverage %, travel time, bottlenecks.

### Administrator — Configuration

* **Regions/Zones**: upload/replace GeoJSON; validate properties.
* **Thresholds & Rules**: define risk bands, alert rules per band; toggle confirmations.
* **Resources**: add/edit pumps/sandbags/vehicles/depots; crew rosters with skills.
* **Users**: assign roles (mock only).

### Data Analyst — Analytical Map

* **Layers**: (1) **Risk Probability** (0–1 heatmap), (2) **Infrastructure/Human Damage** indices, (3) **Weighted Composite** (α·Risk + (1–α)·Damage, α slider 0–1).
* **Charts**: risk over time per zone; top‑N vulnerable zones by composite.
* **Exports**: PNG snapshot of map; CSV of per‑zone metrics.

---

## 4) Tech Stack & Conventions

* **React + Vite + TypeScript**
* **UI**: Tailwind CSS + shadcn/ui (Buttons, Cards, Dialog, Tabs, Toasts)
* **Routing**: React Router v6
* **State/Data**: React Query (even for mock fetchers) + Zod schemas
* **Maps**: React‑Leaflet + Leaflet.Heat + GeoJSON layers
* **Charts**: Recharts
* **Icons**: lucide-react
* **Theming**: Tailwind dark mode; prefers‑color‑scheme detection

**Free‑tier maps**: Use **OpenStreetMap** raster tiles via `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png` for demo loads. For heavier use, switch to MapTiler/Carto free tier with an API key via env variables.

---

## 5) Components (Highlights)

* `AppShell` (header with role switcher for mock, dark toggle, breadcrumbs)
* `MapView` (Leaflet map, LayerControls, Legend, GeoJSON zones)
* `ZonePanel` (KPIs, drivers, actions)
* `ScenarioWorkbench` (inputs + result cards)
* `AlertsTimeline` & `AlertDrawer`
* `OpsBoard` (Kanban) & `CommsPanel` (crew channels + quick actions)
* `AllocationTable` (read‑only for coordinator)
* `AdminForms` (Zod‑validated)
* `AnalystDashboard` (layers, weighting slider, charts, exports)
* `ExplainabilityDialog` (feature attributions, rule snippets)

---

## 6) Mock Data Contracts (realistic) & Files

Place these in `/public/mock/` and fetch with `fetch('/mock/...')`.

### 6.1 Zones (GeoJSON)

**File:** `zones.geojson`

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": "Z-ALFA",
        "name": "Riverside North",
        "population": 12450,
        "critical_assets": ["Hospital HN1", "School SN3"],
        "admin_level": 10
      },
      "geometry": { "type": "Polygon", "coordinates": [[[ -3.71,40.41],[-3.70,40.41],[-3.70,40.42],[-3.71,40.42],[-3.71,40.41 ]]] }
    }
  ]
}
```

### 6.2 Risk Snapshots

**Files:** `risk_2025-11-11T12:00:00Z.json`, `risk_2025-11-11T18:00:00Z.json`

```json
[
  {
    "zoneId": "Z-ALFA",
    "risk": 0.78,
    "drivers": [
      {"feature": "forecast_rain_mm_6h", "contribution": 0.42},
      {"feature": "river_gauge_m", "contribution": 0.29},
      {"feature": "soil_saturation", "contribution": 0.07}
    ],
    "thresholdBand": "Severe",
    "etaHours": 8
  }
]
```

### 6.3 Infrastructure & Human Damage Indices

**File:** `damage_index.json`

```json
[
  {
    "zoneId": "Z-ALFA",
    "infra_index": 0.65,
    "human_index": 0.72,
    "notes": ["Hospital HN1 in floodplain", "Substation S4 at risk"]
  }
]
```

### 6.4 Composite (can be computed client‑side)

`composite = alpha * risk + (1 - alpha) * max(infra_index, human_index)`

### 6.5 Resources Catalog

**File:** `resources.json`

```json
{
  "depots": [
    {"id":"D‑CENTRAL","name":"Central Depot","lat":40.4167,"lng":-3.7033},
    {"id":"D‑EAST","name":"East Yard","lat":40.419,"lng":-3.680}
  ],
  "equipment": [
    {"id":"P‑001","type":"Pump","capacity_lps":300,"depot":"D‑CENTRAL","status":"available"},
    {"id":"S‑010","type":"Sandbags","units":800,"depot":"D‑EAST","status":"available"}
  ],
  "crews": [
    {"id":"C‑A1","name":"Alpha Crew","skills":["pumping","evacuation"],"depot":"D‑CENTRAL","status":"ready","lat":40.4172,"lng":-3.7050},
    {"id":"C‑B3","name":"Bravo Crew","skills":["roadblock"],"depot":"D‑EAST","status":"ready","lat":40.4201,"lng":-3.6820}
  ]
}
```

### 6.6 Proposed Plan (Draft)

**File:** `plan_draft.json`

```json
{
  "version": "2025‑11‑11T10:30:00Z",
  "assignments": [
    {"zoneId":"Z-ALFA","priority":1,
     "actions":[{"type":"deploy_pump","qty":1,"from":"D‑CENTRAL"},{"type":"lay_sandbags","qty":200,"from":"D‑EAST"}]}
  ],
  "notes": "Derived from 12h horizon with severe band"
}
```

### 6.7 Alerts (Crew + System)

**File:** `alerts.json`

```json
[
  {"id":"A‑1001","zoneId":"Z-ALFA","severity":"Severe","type":"System","title":"Flood probability > 0.75","eta":"2025-11-11T20:00:00Z","status":"open"},
  {"id":"A‑1010","zoneId":"Z-ALFA","severity":"Operational","type":"Crew","crewId":"C‑A1","title":"Blocked road reported","timestamp":"2025-11-11T12:10:00Z","status":"open"}
]
```

### 6.8 Ops / Comms Events

**File:** `comms.json`

```json
[
  {"id":"M‑1","channel":"global","from":"Coordinator","text":"All crews check radios","timestamp":"2025-11-11T12:00:00Z"},
  {"id":"M‑2","channel":"task:Z-ALFA","from":"C‑A1","text":"Starting pump deployment","timestamp":"2025-11-11T12:18:00Z"}
]
```

### 6.9 Gauges & Rivers (optional)

**File:** `gauges.json`

```json
[
  {"id":"G‑RIV‑12","name":"River North Gauge","lat":40.418,"lng":-3.699,"level_m":3.2,"trend":"rising"}
]
```

---

## 7) TypeScript Models (with Zod)

```ts
export const RiskPoint = z.object({
  zoneId: z.string(),
  risk: z.number().min(0).max(1),
  drivers: z.array(z.object({ feature: z.string(), contribution: z.number() })),
  thresholdBand: z.enum(["Low","Moderate","High","Severe"]),
  etaHours: z.number().int().nonnegative()
});
export type TRiskPoint = z.infer<typeof RiskPoint>;

export const Assignment = z.object({
  zoneId: z.string(),
  priority: z.number().int().positive(),
  actions: z.array(z.object({ type: z.string(), qty: z.number(), from: z.string().optional() }))
});

export const Crew = z.object({
  id: z.string(), name: z.string(), skills: z.array(z.string()),
  depot: z.string(), status: z.enum(["ready","enroute","working","rest"]),
  lat: z.number(), lng: z.number()
});
```

---

## 8) API Contracts (Future Backend)

**REST (suggested):**

* `GET /api/zones` → GeoJSON
* `GET /api/risk?at=ISO8601` → `TRiskPoint[]`
* `GET /api/damage-index` → per‑zone damage indices
* `GET /api/resources` → depots/equipment/crews
* `GET /api/plan` → current approved plan (Coordinator read‑only)
* `POST /api/plan/draft` (Planner only, propose changes)
* `GET /api/alerts` → open + recent alerts
* `POST /api/alerts/{id}/ack` (Coordinator)
* `GET /api/comms?channel=...` | `POST /api/comms` (Coordinator + crews)

**WebSocket channels:**

* `/ws/alerts` — system + crew alerts stream
* `/ws/telemetry` — crew locations/status
* `/ws/comms` — messages

**Auth & RBAC (later):** JWT (role in claims); FE route guards mirror but never replace server enforcement.

**Env (frontend):**

* `VITE_API_BASE_URL` (default `http://localhost:8080` or `http://api:8080` in Compose)
* `VITE_MAP_TILES_URL` (defaults to OSM)

---

## 9) Docker‑friendly Setup

### 9.1 Frontend Dockerfile

```Dockerfile
# ./frontend/Dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY ./nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx","-g","daemon off;"]
```

### 9.2 Mock API (Express, static JSON)

**server.js**

```js
import express from 'express';
import cors from 'cors';
import fs from 'fs';
const app = express();
app.use(cors());
app.get('/api/zones', (_,res)=>res.sendFile('/data/zones.geojson'));
app.get('/api/risk', (req,res)=>{
  const at = (req.query.at || '2025-11-11T12:00:00Z').toString().replace(/:/g,'-');
  const p = `/data/risk_${at}.json`; // pre-render a few timestamps
  if (fs.existsSync(p)) res.sendFile(p); else res.sendFile('/data/risk_2025-11-11T12-00-00Z.json');
});
app.get('/api/damage-index', (_,res)=>res.sendFile('/data/damage_index.json'));
app.get('/api/resources', (_,res)=>res.sendFile('/data/resources.json'));
app.get('/api/plan', (_,res)=>res.sendFile('/data/plan_draft.json'));
app.get('/api/alerts', (_,res)=>res.sendFile('/data/alerts.json'));
app.get('/api/comms', (_,res)=>res.sendFile('/data/comms.json'));
app.listen(8080, ()=>console.log('Mock API on :8080'));
```

**Dockerfile**

```Dockerfile
# ./mock-api/Dockerfile
FROM node:20-alpine
WORKDIR /srv
COPY package.json package-lock.json ./
RUN npm ci
COPY server.js ./
COPY public/mock /data
EXPOSE 8080
CMD ["node","server.js"]
```

**package.json (api)**

```json
{ "name":"mock-api","type":"module","dependencies": {"express":"^4.19.2","cors":"^2.8.5"} }
```

### 9.3 docker-compose

```yaml
version: "3.9"
services:
  api:
    build: ./mock-api
    ports: ["8080:8080"]
  web:
    build: ./frontend
    environment:
      - VITE_API_BASE_URL=http://api:8080
      - VITE_MAP_TILES_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
    ports: ["5173:80"]
    depends_on: [api]
```

> **Note:** Postgres/PostGIS can be added later as another service; the FE reads from the API only. Keep FE stateless.

---

## 10) Quick Start (Concise)

1. **Scaffold FE**: `pnpm create vite frontend --template react-ts`
2. Add **Tailwind + shadcn/ui**; add **React Router**, **React Query**, **Zod**, **React‑Leaflet**, **Recharts**.
3. Create `/public/mock` and copy the JSON files above.
4. Implement routes, `AppShell`, `MapView`, and panels using mocked fetchers.
5. Build **mock‑api** service with the Express server serving files from `/public/mock`.
6. `docker compose up --build` → FE on `http://localhost:5173`.
7. Use the role switcher to demo Planner → Coordinator → Admin → Analyst flows.

---

## 11) Demo Script (2–3 minutes)

1. **Planner/Map**: open hot zone → show drivers & recommendation → “Add to Plan”.
2. **Scenarios**: tweak severity/resources → observe ranked zones → submit draft.
3. **Coordinator/Resources**: see read‑only plan → open Ops Board → send `Start Deployment` to `C‑A1` → acknowledge road block alert.
4. **Analyst**: set α = 0.6 → show composite layer; export PNG.
5. **Admin**: raise “Severe” threshold → map recolors bands.

---

## 12) Implementation Notes

* **Access Control (Mock)**: a simple `useSession()` with `role` in context; guards per route; disable/ghost buttons where disallowed.
* **Explainability**: show top 3 feature contributions per zone; tooltip on layers for rationale.
* **Performance**: virtualized lists for alerts; debounced map interactions.
* **Exports**: canvas or `html2canvas` for PNG, simple CSV stringify for tables.
* **Testing**: minimal unit tests for data mappers; Cypress happy‑path smoke test.

---

## 13) Predefined Actions (Coordinator)

* **Crew control**: Start/Stop task, ETA update, Request backup, Safety check.
* **Environment**: Report water level (enum: rising/steady/falling + numeric), Block/Unblock road, Evacuate segment.
* **Logistics**: Request supplies, Low battery alert, Send photo.

> Each action posts to `/api/comms` (mock) and appends to the task channel.

---

## 14) Future Backend & DB Integration (Ready Hooks)

* **DB**: Postgres + PostGIS for zones, gauges, assets. The API aggregates per‑zone risk and damage views.
* **ETL**: Ingest model outputs into `risk_snapshots` with `zone_id`, `timestamp`, `risk`, and `drivers (JSONB)`.
* **Indices**: GiST on zone geometries; time index on risk snapshots; materialized view for latest snapshot.
* **API Gateways**: Prefix `/api` and enable CORS for FE origin; pagination for large lists; gzip.
* **Security**: JWT with roles; CSRF not needed on pure API + token.

---

## 15) Visuals & UX

* **Dark‑first palette**, high contrast, severity badges (Low/Moderate/High/Severe), clear legends.
* **Map Legend**: 5 bands; tooltip explains thresholds; click selects zone.
* **Empty States**: informative messages with CTAs.
* **Accessibility**: WCAG AA; keyboard navigation; ARIA on dialogs/tabs.
