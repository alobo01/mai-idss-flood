# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **role-based React application for flood prediction system management**. The project has a **complete architectural foundation** but requires implementation of core functionality. Think of it as a production-ready framework with placeholder content.

**Current State**: 80% architecture, 20% functionality. The scaffolding is complete but page components are mostly placeholders.

## Technology Stack

### Frontend
- **React 18** + TypeScript + Vite
- **Tailwind CSS** with dark mode (default)
- **shadcn/ui** (Radix UI) components
- **React Router v6** for role-based navigation
- **React Query** for data fetching (configured but not implemented)
- **React-Leaflet** for maps (installed but not implemented)
- **Zod** for type-safe data validation
- **Playwright** for E2E testing

### Backend (Mock)
- **Express.js** server with JSON file-based data
- **Docker Compose** for orchestration

## Development Commands

```bash
# Docker-first development (recommended)
docker compose up --build

# Local development
npm install
npm run dev

# Testing
npm run test              # Playwright E2E tests
npm run test:ui           # Interactive test runner
npm run test:report       # View test report

# Build and quality
npm run build             # Production build
npm run lint              # ESLint
```

**Application URLs**:
- Frontend: http://localhost:5173
- Mock API: http://localhost:8080

## Architecture & Project Structure

### Role-Based Design
Four distinct user roles with tailored interfaces:
- **Administrator**: System config, regions, thresholds, users
- **Planner**: Risk mapping, scenarios, alert management
- **Coordinator**: Live operations, resources, communications
- **Data Analyst**: Analytics, exports, reporting

### Key Directories
```
src/
├── components/          # Reusable UI components
│   ├── ui/             # shadcn/ui components
│   ├── AppShell.tsx    # Main layout with navigation
│   └── RoleSelector.tsx # Role switching interface
├── pages/              # Role-specific page components (mostly placeholders)
├── contexts/           # AppContext for global state
├── types/              # Zod schemas and TypeScript types
├── hooks/              # Custom React hooks
└── lib/                # Utility functions

public/mock/            # All mock data files
mock-api/              # Express server code
```

### State Management
- **AppContext**: Global state (role, zone selection, theme)
- **React Query**: Data fetching from mock API (configured but not used)
- **localStorage**: Role and theme persistence

## Data Models & API

### Mock Data Structure (Complete)
All mock data files exist in `public/mock/`:
- `zones.geojson` - 4 geographic zones with polygons
- `risk_*.json` - Time-based risk data (12h, 18h forecasts)
- `damage_index.json` - Infrastructure damage assessments
- `resources.json` - Crews, equipment, depots
- `plan_draft.json` - Response plan templates
- `alerts.json` - System alerts with severity levels
- `comms.json` - Communication logs
- `gauges.json` - River gauge readings

### API Endpoints (Mock)
Express server at `/api` provides:
- `GET /api/zones` - Geographic zones (GeoJSON)
- `GET /api/risk?at=<timestamp>` - Time-based risk data
- `GET /api/damage-index` - Damage assessments
- `GET /api/resources` - Equipment and crews
- `GET /api/plan` - Response plans
- `GET /api/alerts` - System alerts
- `GET /api/comms` - Communications
- `GET /api/gauges` - River gauges

## Current Implementation Status

### ✅ **Completed**
- Complete project setup and build pipeline
- Role-based authentication and navigation
- Responsive UI with dark mode
- AppShell layout with role-specific menus
- Type-safe data models with Zod
- Mock API with all endpoints
- Docker containerization
- Basic E2E test framework
- **Map Integration**: Interactive React-Leaflet components with real GeoJSON data
- **Data Fetching**: Full React Query integration with live API hooks
- **Interactive Components**: Dynamic map views, real-time dashboards, and interactive panels
- **Visualizations**: Risk heatmaps, zone-based coloring, and live metrics
- **Role-Specific Features**: Functional interfaces for Planner and Coordinator roles
- **Real-time Features**: Live alerts, communications, and resource tracking

### ✅ **Fully Implemented Features**

#### Map & Visualization
- **MapView Component**: Interactive maps with React-Leaflet integration
- **GeoJSON Zones Layer**: Real flood zone data with polygon boundaries
- **Risk Heatmaps**: Dynamic risk coloring based on prediction data
- **Critical Assets Markers**: Visual indicators for hospitals, schools, infrastructure
- **Layer Controls**: Toggle between zones, risk, assets, and gauges
- **Time Horizon Selector**: 6h, 12h, 24h, 48h, 72h forecast periods
- **Interactive Zone Selection**: Click zones for detailed risk information

#### Planner Interface
- **Risk Assessment Map**: Interactive flood risk visualization with detailed analysis
- **Alert Management**: Centralized alert monitoring and response system
- **Zone Details Panel**: Comprehensive zone information with population and assets
- **Risk Analysis Dashboard**: Metrics, drivers, and high-risk zone prioritization

#### Coordinator Interface
- **Live Operations Board**: Real-time coordination dashboard with metrics
- **Alerts Timeline**: Real-time alert management with filtering and acknowledgment
- **Communications Panel**: Multi-channel communication hub with message history
- **Resource Allocation**: Interactive crew and equipment deployment system
- **Gauge Monitoring**: Real-time river gauge tracking with alert thresholds

### ❌ **Needs Implementation**
- **Scenario Workbench**: Advanced "what-if" analysis for Planner role
- **Administrator Interfaces**: System configuration and management tools
- **Data Analyst Interfaces**: Analytics, exports, and reporting functionality
- **Performance Optimizations**: Caching, virtual scrolling, and debouncing
- **Enhanced Testing**: More comprehensive E2E test coverage
- **Advanced Real-time**: WebSocket integration for live updates

## Development Guidelines

### When Implementing New Features

1. **Use Existing Patterns**: Follow the established component structure in `src/components/`
2. **Type Safety**: Leverage existing Zod schemas in `src/types/`
3. **Mock Data**: Use mock API endpoints via React Query hooks
4. **Responsive Design**: Maintain mobile-first approach with Tailwind breakpoints
5. **Dark Mode**: All components must support both themes
6. **Role-Based Access**: Use AppContext for role-specific UI rendering

### Map Implementation Priority
The most critical missing piece is the React-Leaflet integration. When implementing maps:

1. Start with basic MapView component in `src/components/MapView.tsx`
2. Use zones.geojson data for base layer
3. Implement risk overlays using risk_*.json data
4. Add interactive zone selection and details panel

### Testing Approach
- E2E tests with Playwright are configured
- Focus on testing user flows across different roles
- Test responsive design at mobile/tablet/desktop viewports
- Verify dark mode functionality

## Docker & Deployment

### Development Environment
```bash
docker compose up --build
```

### Container Architecture
- **Frontend Container**: nginx serving built React app
- **API Container**: Express serving mock JSON data
- **Health Checks**: API must be healthy before frontend starts
- **Volume Mounts**: Mock data shared between containers

### Production Considerations
- Frontend is stateless and can scale horizontally
- Mock API would be replaced with real backend services
- Environment variables control API URLs and tile servers

## Next Implementation Steps

Based on TASKS.md, the priority implementation order is:

1. **MapView Component** - Interactive maps with GeoJSON zones
2. **Data Integration** - Connect UI components to mock API
3. **Planner Interface** - Risk mapping and scenario tools
4. **Coordinator Interface** - Live operations board
5. **Resource Allocation** - Interactive assignment tools
6. **Admin Interface** - Zone editing and threshold config
7. **Export/Reporting** - Data export functionality

## Common Issues & Solutions

### Map Integration
- React-Leaflet requires CSS imports: `import 'leaflet/dist/leaflet.css'`
- Default markers need custom icon configuration
- OpenStreetMap tiles need proper attribution

### API Integration
- Mock API runs on port 8080 in development
- Use React Query error boundaries for graceful fallbacks
- Implement loading states for better UX

### Docker Development
- Use volume mounts for hot reloading during development
- API health checks prevent frontend race conditions
- Clear browser cache when updating mock data

This codebase provides excellent foundation for building a sophisticated flood prediction management system. The architecture is solid, types are comprehensive, and the design system is professional. The main work needed is implementing the interactive features, particularly map visualization and role-specific functionality.