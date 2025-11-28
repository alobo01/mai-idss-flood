# Flood Prediction Frontend Development Tasks

This document contains precise, testable tasks to implement the flood prediction React frontend mock described in PLAN.md.

## Phase 1: Project Setup & Infrastructure

### 1.1 Project Initialization ✅ COMPLETED
- [x] **Task**: Initialize Vite React TypeScript project
  - **Test**: Run `npm create vite@latest . --template react-ts` and verify project scaffolding
  - **Acceptance**: Project builds successfully with `npm build` ✅

- [x] **Task**: Install required dependencies
  - **Dependencies**: `react-router-dom`, `@tanstack/react-query`, `zod`, `leaflet`, `react-leaflet`, `recharts`, `lucide-react`, `@radix-ui/*`
  - **Dev Dependencies**: `tailwindcss`, `@types/leaflet`, `autoprefixer`, `postcss`, `class-variance-authority`, `clsx`, `tailwind-merge`
  - **Test**: All packages install without conflicts
  - **Acceptance**: `npm install` completes successfully ✅

- [x] **Task**: Configure Tailwind CSS with dark mode
  - **Test**: Create `tailwind.config.js` with dark mode configuration
  - **Acceptance**: CSS classes compile correctly, dark theme applies via `dark:` prefixes ✅

- [x] **Task**: Set up shadcn/ui components
  - **Components**: Button, Card, Dialog, Tabs, Badge, Dropdown Menu
  - **Test**: Components render in test pages without errors
  - **Acceptance**: All configured components are importable and functional ✅

### 1.2 Mock Data Setup ✅ COMPLETED
- [x] **Task**: Create `/public/mock/` directory structure
  - **Files**: `zones.geojson`, `risk_2025-11-11T12:00:00Z.json`, `risk_2025-11-11T18:00:00Z.json`, `damage_index.json`, `resources.json`, `plan_draft.json`, `alerts.json`, `comms.json`, `gauges.json`
  - **Test**: All JSON files are valid JSON format ✅
  - **Acceptance**: Files are accessible via `fetch('/mock/...')` ✅

- [x] **Task**: Validate GeoJSON zones data
  - **Test**: Load `zones.geojson` and verify polygon geometries
  - **Acceptance**: GeoJSON renders correctly on map with proper coordinates ✅

### 1.3 TypeScript Configuration ✅ COMPLETED
- [x] **Task**: Create Zod schemas for data models
  - **Models**: RiskPoint, Assignment, Crew, Alert, Resource, Zone, GeoJSON, etc.
  - **Test**: Schemas validate mock data without errors ✅
  - **Acceptance**: Type inference generates correct TypeScript types ✅

## Phase 2: Core Application Structure

### 2.1 Routing & Authentication ✅ COMPLETED
- [x] **Task**: Implement React Router v6 configuration
  - **Routes**: `/`, `/planner/*`, `/coordinator/*`, `/admin/*`, `/analyst/*`
  - **Test**: Navigation between routes works without page reload ✅
  - **Acceptance**: All defined routes are accessible ✅

- [x] **Task**: Create role-based authentication mock
  - **Features**: Role switcher component, route guards, permission context
  - **Test**: Role switching updates UI permissions immediately ✅
  - **Acceptance**: Unauthorized routes redirect to role chooser ✅

### 2.2 App Shell & Layout ✅ COMPLETED
- [x] **Task**: Implement AppShell component
  - **Features**: Header with role switcher, dark mode toggle, breadcrumbs, navigation
  - **Test**: Component renders responsive layout ✅
  - **Acceptance**: All navigation elements are accessible and functional ✅

- [x] **Task**: Add dark mode toggle functionality
  - **Test**: Toggle switches between light and dark themes ✅
  - **Acceptance**: Theme preference persists in localStorage ✅

## Phase 3: Map & Visualization Components

### 3.1 Base Map Component ✅ COMPLETED
- [x] **Task**: Create MapView component with React-Leaflet
  - **Features**: OpenStreetMap tiles, layer controls, zoom/pan controls
  - **Test**: Map renders with correct tile layer ✅
  - **Acceptance**: Map is interactive with smooth pan/zoom ✅

- [x] **Task**: Implement GeoJSON zones layer
  - **Features**: Zone polygons with color coding by risk band
  - **Test**: Zones render from mock GeoJSON data ✅
  - **Acceptance**: Zone colors correspond to risk levels ✅

### 3.2 Risk Visualization ✅ COMPLETED
- [x] **Task**: Add risk heatmap layer
  - **Features**: Heatmap overlay showing risk probability
  - **Test**: Heatmap displays correctly over zones ✅
  - **Acceptance**: Heat opacity and intensity are visually appropriate ✅

- [x] **Task**: Implement critical assets markers
  - **Features**: Hospital, school, infrastructure icons
  - **Test**: Asset markers display at correct coordinates ✅
  - **Acceptance**: Markers are clickable with information popup ✅

### 3.3 Map Controls ✅ COMPLETED
- [x] **Task**: Create LayerControls component
  - **Features**: Toggle layers (risk, rivers, gauges, assets)
  - **Test**: Layer toggles show/hide corresponding map elements ✅
  - **Acceptance**: Layer state persists during session ✅

- [x] **Task**: Implement time horizon selector
  - **Features**: 6h, 12h, 24h, 48h, 72h time windows
  - **Test**: Time selection updates risk data display ✅
  - **Acceptance**: Risk data changes based on selected timeframe ✅

## Phase 4: Role-Specific Features

### 4.1 Planner Interface ✅ PARTIALLY COMPLETED
- [x] **Task**: Implement Planner Risk Map view
  - **Route**: `/planner/map`
  - **Features**: Zone details panel, recommended actions, "Add to Plan" button
  - **Test**: Clicking zone shows details panel ✅
  - **Acceptance**: Panel displays risk score, drivers, and actions ✅

- [ ] **Task**: Create Scenario Workbench
  - **Route**: `/planner/scenarios`
  - **Features**: Weather severity slider, resource inputs, what-if analysis
  - **Test**: Sliders update scenario results in real-time
  - **Acceptance**: Ranked zones display based on scenario parameters

- [x] **Task**: Implement Alerts Timeline
  - **Route**: `/planner/alerts`
  - **Features**: Chronological alert list, severity filters, zone filtering
  - **Test**: Timeline displays alerts in chronological order ✅
  - **Acceptance**: Filters correctly narrow alert display ✅

### 4.2 Coordinator Interface ✅ COMPLETED
- [x] **Task**: Create Live Ops Board
  - **Route**: `/coordinator/ops`
  - **Features**: Real-time dashboard with metrics, alerts, and resource status
  - **Test**: Dashboard displays live data and updates ✅
  - **Acceptance**: Critical alerts and resource status show correctly ✅

- [x] **Task**: Implement Communications Panel
  - **Features**: Multi-channel communication hub, message history, filtering
  - **Test**: Messages display chronologically with proper filtering ✅
  - **Acceptance**: Communication channels work correctly ✅

- [x] **Task**: Create Resource Allocation view
  - **Route**: `/coordinator/resources`
  - **Features**: Interactive resource management, crew deployment, equipment tracking
  - **Test**: Resources display with correct status and deployment options ✅
  - **Acceptance**: Resource allocation metrics calculate correctly ✅

### 4.3 Administrator Interface
- [ ] **Task**: Implement Regions Manager
  - **Route**: `/admin/regions`
  - **Features**: GeoJSON upload/edit, zone validation, property editing
  - **Test**: GeoJSON files upload and parse correctly
  - **Acceptance**: Invalid GeoJSON shows appropriate error messages

- [ ] **Task**: Create Threshold Configuration
  - **Route**: `/admin/thresholds`
  - **Features**: Risk band definitions, alert rules, confirmation toggles
  - **Test**: Threshold changes update map color bands immediately
  - **Acceptance**: Form validation prevents invalid values

- [ ] **Task**: Implement Resource Catalog
  - **Route**: `/admin/resources`
  - **Features**: Add/edit depots, equipment, crews with skills
  - **Test**: Forms save and display new resources correctly
  - **Acceptance**: Resource list updates after form submission

### 4.4 Data Analyst Interface
- [ ] **Task**: Create Analytical Map
  - **Route**: `/analyst/overview`
  - **Features**: Risk probability layer, damage indices, composite weighted view
  - **Test**: Alpha weighting slider updates composite layer
  - **Acceptance**: Composite calculation uses correct formula

- [ ] **Task**: Implement Export functionality
  - **Route**: `/analyst/exports`
  - **Features**: PNG map snapshots, CSV data export
  - **Test**: PNG exports save readable map images
  - **Acceptance**: CSV exports contain proper per-zone metrics

## Phase 5: Data Management & State ✅ COMPLETED

### 5.1 Data Fetching ✅ COMPLETED
- [x] **Task**: Set up React Query for API calls
  - **Features**: Query hooks for all data types, error handling, loading states
  - **Test**: Data loads from mock files without errors ✅
  - **Acceptance**: Loading states display during data fetch ✅

- [x] **Task**: Create API service
  - **Features**: Express server serving static JSON files, CORS support
  - **Test**: API endpoints return correct JSON data ✅
  - **Acceptance**: All endpoints are accessible ✅

### 5.2 State Management ✅ COMPLETED
- [x] **Task**: Implement application state context
  - **Features**: Current role, selected zone, active filters, UI preferences
  - **Test**: State updates propagate to all consuming components ✅
  - **Acceptance**: State persists across route changes ✅

## Phase 6: User Experience & Polish

### 6.1 Responsive Design ✅ COMPLETED
- [x] **Task**: Ensure mobile responsiveness
  - **Test**: Application works on 320px width devices ✅
  - **Acceptance**: All features remain functional on mobile ✅

- [x] **Task**: Implement keyboard navigation
  - **Test**: All interactive elements accessible via keyboard ✅
  - **Acceptance**: Tab order follows logical visual flow ✅

### 6.2 Error Handling ✅ COMPLETED
- [x] **Task**: Add error boundaries
  - **Features**: Graceful error display, recovery options
  - **Test**: Component errors don't crash entire application ✅
  - **Acceptance**: Error boundaries show helpful error messages ✅

- [x] **Task**: Implement loading states
  - **Features**: Skeleton loaders, progress indicators
  - **Test**: Loading displays during data fetching ✅
  - **Acceptance**: No layout shifts during loading ✅

### 6.3 Performance Optimization
- [ ] **Task**: Implement virtual scrolling for large lists
  - **Test**: Large alert lists maintain 60fps scroll performance
  - **Acceptance**: Memory usage remains stable with large datasets

- [ ] **Task**: Add map interaction debouncing
  - **Test**: Rapid map interactions don't cause performance issues
  - **Acceptance**: Map remains responsive during heavy use

## Phase 7: Integration & Testing

### 7.1 End-to-End Testing
- [ ] **Task**: Create Cypress test suite
  - **Scenarios**: Role switching, map interaction, plan creation, alert handling
  - **Test**: All major user flows complete successfully
  - **Acceptance**: Tests pass in headless mode

### 7.2 Docker Integration ✅ COMPLETED
- [x] **Task**: Create frontend Dockerfile
  - **Test**: Image builds successfully with production assets ✅
  - **Acceptance**: Container serves application correctly ✅

- [x] **Task**: Set up docker-compose
  - **Test**: Both frontend and API start together ✅
  - **Acceptance**: Application accessible at http://localhost:5173 ✅

## Phase 8: Documentation & Deployment

### 8.1 Documentation
- [ ] **Task**: Create component documentation
  - **Test**: All components have JSDoc comments
  - **Acceptance**: Storybook builds successfully

### 8.2 Demo Preparation
- [ ] **Task**: Implement demo script flows
  - **Flows**: Planner map → scenarios → coordinator ops → analyst export → admin config
  - **Test**: Demo runs smoothly without errors
  - **Acceptance**: All demo features are visually impressive

## Phase 9: API Completion (PostgreSQL)

### 9.1 Service Hardening
- [ ] **Task**: Run the Node/Express API against the Postgres service in both local dev and Docker Compose
  - **Test**: `/health`, `/api/zones`, `/api/alerts`, and `/api/resources` respond successfully when `DB_HOST=postgres`
  - **Acceptance**: Backend container starts cleanly after PostgreSQL initialization

- [ ] **Task**: Provide automated migrations + seed data tied to the new SQL scripts
  - **Test**: `npm run db:migrate && npm run db:seed` completes on a clean database without manual edits
  - **Acceptance**: Database contains sample zones, assets, gauges, alerts, and response plans

### 9.2 Endpoint Parity
- [ ] **Task**: Implement database-backed routes for risk assessments, assets, communications, gauges, deployments, and admin CRUD
  - **Test**: Requests return rows from PostgreSQL instead of JSON files (`api/server.js` parity)
  - **Acceptance**: All endpoints documented under `docs/api` exist in `backend/server.js`

- [ ] **Task**: Add integration tests that hit the API against a seeded Postgres instance
  - **Test**: CI job brings up Postgres, runs backend tests, and validates sample responses
  - **Acceptance**: Tests fail if database schema or seed data no longer matches API contracts

## Acceptance Criteria Summary

### Core Functionality
- [ ] All 4 roles (Planner, Coordinator, Admin, Analyst) have functional interfaces
- [ ] Map displays zones, risk layers, and assets correctly
- [ ] Role-based permissions restrict access appropriately
- [ ] Mock data loads and displays without errors
- [ ] Navigation between all routes works seamlessly

### Quality Standards
- [ ] Application builds without warnings or errors
- [ ] Dark mode theme is consistently applied
- [ ] Responsive design works on all screen sizes
- [ ] Keyboard navigation is fully functional
- [ ] Loading states provide good user feedback

### Performance Requirements
- [ ] Initial page load completes within 3 seconds
- [ ] Map interactions remain responsive (< 100ms latency)
- [ ] Large datasets (1000+ alerts) scroll smoothly
- [ ] Memory usage remains stable during extended use

### Integration Success
- [ ] Docker compose builds and runs successfully
- [ ] API serves all required endpoints
- [ ] Frontend connects to API without CORS errors
- [ ] Demo script showcases all planned features

## Testing Checklist

### Manual Testing
- [ ] Role switching works correctly
- [ ] Map loads with all layers
- [ ] Zone selection shows proper details
- [ ] Form submissions validate correctly
- [ ] Export functions generate proper files
- [ ] Responsive layout adapts to screen size

### Automated Testing
- [ ] Unit tests for data models pass
- [ ] Component integration tests pass
- [ ] E2E Cypress tests complete
- [ ] Build process completes without errors
- [ ] Docker images build and run correctly

### Performance Testing
- [ ] Lighthouse score > 90
- [ ] Bundle size < 2MB (gzipped)
- [ ] Time to interactive < 3 seconds
- [ ] Map render time < 1 second
