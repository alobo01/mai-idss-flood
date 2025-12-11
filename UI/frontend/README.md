# Flood Prediction Frontend

A modern, responsive React TypeScript application for interactive flood risk visualization and emergency response planning. This frontend provides real-time flood predictions, interactive mapping, and comprehensive scenario planning tools for emergency operators.

## 🚀 Overview

The frontend is a critical component of the MAI IDSS (Intelligent Decision Support System) for flood prediction and response. It serves as the primary interface for emergency operators to:

- Visualize real-time flood risk assessments across multiple zones
- Monitor river gauge data and historical trends
- Plan resource allocation using rule-based algorithms
- Analyze forecast uncertainty with prediction intervals
- Access historical flood data for pattern analysis

## 🛠 Technology Stack

### Core Framework
- **React 18.2.0** - Modern functional components with hooks
- **TypeScript 5.2.2** - Type-safe development with strict mode
- **Vite 5.0.8** - Lightning-fast development and optimized builds

### UI & Styling
- **Tailwind CSS 3.3.0** - Utility-first CSS framework
- **Radix UI** - Accessible component primitives
  - `@radix-ui/react-tabs` - Tab navigation
  - `@radix-ui/react-label` - Form labels
  - `@radix-ui/react-progress` - Progress indicators
- **Lucide React** - Beautiful, consistent icon system
- **Class Variance Authority** - Component variant management

### Mapping & Geospatial
- **Leaflet 1.9.4** - Interactive maps
- **React-Leaflet 4.2.1** - React integration for Leaflet
- **PostGIS-compatible** - Works with geospatial data formats

### Build Tools
- **TypeScript Compiler** - Type checking and transpilation
- **PostCSS + Autoprefixer** - CSS processing pipeline
- **ESLint (implied)** - Code quality assurance

## 📁 Project Structure

```
frontend/
├── public/                          # Static assets
│   └── mock/                       # Mock data for development
│       ├── zones.geojson           # Flood zone geometries
│       ├── risk_*.json             # Time-series risk data
│       ├── gauges.json             # River gauge locations
│       ├── alerts.json             # Alert configurations
│       └── resources.json          # Resource allocation data
├── src/
│   ├── components/                 # Reusable UI components
│   │   ├── ui/                    # Base UI components (shadcn/ui)
│   │   │   ├── badge.tsx
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── tabs.tsx
│   │   │   ├── progress.tsx
│   │   │   ├── label.tsx
│   │   │   ├── input.tsx
│   │   │   ├── table.tsx
│   │   │   └── alert.tsx
│   │   ├── MapView.tsx            # Interactive map component
│   │   ├── StLouisFloodPanel.tsx  # River level dashboard
│   │   └── HistoricalDataPanel.tsx # Historical analysis view
│   ├── pages/                      # Route-level components
│   │   └── planner/
│   │       ├── Map.tsx            # Main planner interface
│   │       └── Resources.tsx      # Resource management
│   ├── hooks/                      # Custom React hooks
│   │   ├── useBackendData.ts      # API data fetching
│   │   ├── useRuleBased.ts        # Rule-based algorithm
│   │   ├── useSimulatedTimeline.ts # Timeline simulation
│   │   ├── useZones.ts            # Zone data management
│   │   └── use-toast.ts           # Toast notifications
│   ├── contexts/                   # React context providers
│   │   └── AppContext.tsx         # Global application state
│   ├── lib/                        # Utility libraries
│   │   ├── utils.ts               # General utilities
│   │   ├── mockData.ts            # Mock data generators
│   │   └── leaflet-config.ts      # Leaflet configuration
│   ├── types.ts                    # TypeScript type definitions
│   ├── main.tsx                    # Application entry point
│   ├── App.tsx                     # Root component
│   └── index.css                   # Global styles and Tailwind
├── package.json                    # Dependencies and scripts
├── tsconfig.json                   # TypeScript configuration
├── vite.config.ts                  # Vite build configuration
├── tailwind.config.js              # Tailwind CSS configuration
├── postcss.config.js               # PostCSS configuration
└── index.html                      # HTML template
```

## 🧩 Core Components

### MapView Component
The centerpiece of the application, providing interactive flood risk visualization:

**Features:**
- Real-time zone risk coloring with multiple data layers
- Interactive popups with detailed zone information
- Layer toggles for zones, risk assessments, and rule-based allocations
- Gauge markers for USGS river monitoring stations
- Responsive design with emergency operator UI patterns

**Props:**
```typescript
interface MapViewProps {
  zones: GeoJSONType;                    // Zone geometries
  riskData?: RiskPoint[];               // Risk assessment data
  ruleData?: PipelineRuleBasedAllocation[]; // Rule-based allocations
  selectedZone?: string | null;         // Currently selected zone
  onZoneSelect?: (zoneId: string) => void; // Zone selection handler
  timeHorizon?: string;                 // Forecast time horizon
  layers?: LayerToggles;                // Layer visibility controls
  gauges?: GaugePoint[];                // River gauge data
  className?: string;                   // Additional CSS classes
}
```

### StLouisFloodPanel Component
Comprehensive dashboard for St. Louis river monitoring:

**Features:**
- Real-time river level displays
- 30-day historical trends with sparkline charts
- 1-3 day forecast predictions with uncertainty quantification
- Prediction interval visualization (80% confidence bands)
- Flood probability calculations
- Historical observation tables with forecast tails

**Key Metrics:**
- Latest river level readings
- Day-over-day level changes
- Upstream gauge signals (Hermann)
- 24-hour precipitation data

### HistoricalDataPanel Component
Advanced analytics for historical flood data:

**Features:**
- Long-term trend analysis
- Seasonal pattern detection
- Event correlation studies
- Export capabilities for analysis

## 🔧 Custom Hooks

### useBackendData Hook
Manages all API communication with the flood prediction backend:

```typescript
const {
  predictions,     // 1-3 day forecast predictions
  rawData,        // Daily hydrological observations
  latestObservation, // Most recent gauge reading
  history,        // Historical prediction accuracy
  loading,        // Loading state
  error           // Error handling
} = useBackendData();
```

### useRuleBased Hook
Implements the fuzzy logic allocation algorithm:

```typescript
const { data: rulePipeline } = useRuleBasedPipeline({
  globalPf: 0.55,           // Global performance factor
  totalUnits: 12,           // Total available resources
  mode: 'crisp',           // Allocation mode
  maxUnitsPerZone: 6       // Maximum resources per zone
});
```

### useSimulatedTimeline Hook
Provides timeline simulation for scenario planning:

```typescript
const {
  timestamp,        // Current simulation timestamp
  label,           // Human-readable timestamp
  speedLabel,      // Simulation speed indicator
  isPlaying        // Playback state
} = useSimulatedTimeline();
```

## 🎨 UI/UX Design System

### Emergency Operator Theme
The interface is specifically designed for emergency operations centers:

**High Contrast Design:**
- WCAG AA compliant color schemes
- Large, readable typography (minimum 16px base size)
- Clear visual hierarchy with emergency status colors
- Dark mode support for 24/7 operations

**Status Colors:**
- **Severe (Critical)**: Red-600 (`#dc2626`) - Immediate action required
- **High (Warning)**: Orange-600 (`#ea580c`) - Enhanced monitoring
- **Moderate (Advisory)**: Yellow-600 (`#ca8a04`) - Routine monitoring
- **Low (Normal)**: Green-600 (`#15803d`) - Normal operations

**Interactive Elements:**
- Minimum 44px touch targets for accessibility
- High contrast focus indicators
- Keyboard navigation support
- Screen reader compatibility

### Component Patterns

**Status Indicators:**
```typescript
// Consistent pattern across all components
<div className="status-indicator">
  <Icon className="h-4 w-4" aria-hidden="true" />
  <span className="font-medium">Label</span>
</div>
```

**Emergency Cards:**
```typescript
// High contrast, information-dense cards
<Card className="p-4 border-2 border-border shadow-lg bg-card">
  <div className="critical-label">Critical Information</div>
  <div className="critical-data">23.45 ft</div>
</Card>
```

## 📊 Data Management

### Mock Data System
For development and testing, the frontend uses a comprehensive mock data system:

**Risk Data Time Series:**
- Historical data from 2019 (full year coverage)
- Current scenario data from November 2025
- Hourly risk assessments for all zones
- Probability distributions and uncertainty bands

**Zone Data:**
- GeoJSON-compliant polygon geometries
- Population density calculations
- Critical infrastructure locations
- Risk threshold configurations

**Resource Data:**
- Emergency resource locations
- Allocation algorithms
- Performance metrics
- Response time calculations

### Data Flow Architecture

```
Backend API → useBackendData Hook → React Context → Components
     ↓
Mock Data → Local Development → Component Props → UI Rendering
```

**Real-time Updates:**
- Polling interval: 5 minutes for production
- WebSocket support planned for real-time updates
- Offline caching with service workers
- Data reconciliation strategies

## 🚦 Getting Started

### Prerequisites
- Node.js 18+ (recommended: LTS version)
- npm 9+ or yarn 1.22+
- Modern web browser with ES2020 support

### Development Setup

1. **Install Dependencies:**
```bash
cd frontend
npm install
```

2. **Environment Configuration:**
```bash
# Copy environment template
cp .env.example .env

# Configure API endpoints
VITE_API_BASE_URL=http://localhost:8003
VITE_MAP_TILE_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
```

3. **Start Development Server:**
```bash
npm run dev
```

4. **Access Application:**
- Frontend: http://localhost:5173
- API Documentation: http://localhost:8003/docs

### Production Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Build output directory: dist/
```

## 🔧 Configuration

### Vite Configuration
Key features in `vite.config.ts`:
- React plugin with fast refresh
- API proxy for backend communication
- Path aliases for clean imports
- Optimized chunk splitting

### TypeScript Configuration
Strict TypeScript setup in `tsconfig.json`:
- Strict type checking enabled
- Path mapping for clean imports
- Modern ES2020 target
- JSX transform for React 18

### Tailwind CSS Configuration
Custom design system in `tailwind.config.js`:
- Emergency operator color palette
- Custom animation utilities
- Responsive breakpoints
- Dark mode support

## 🌐 Accessibility Features

### WCAG 2.1 AA Compliance
- **Keyboard Navigation:** Full keyboard access to all interactive elements
- **Screen Reader Support:** Semantic HTML with ARIA labels
- **High Contrast:** Emergency operator optimized color schemes
- **Focus Management:** Clear focus indicators and logical tab order
- **Text Scaling:** Support for 200% text zoom

### Emergency Operator Features
- **Large Touch Targets:** Minimum 44px for all interactive elements
- **Clear Status Indicators:** Color + icon redundancy
- **Consistent Layout:** Predictable interface patterns
- **Error Prevention:** Confirmation dialogs for critical actions
- **Time-Sensitive Information:** Prominent display of urgent data

## 🔍 Testing Strategy

### Component Testing
- Unit tests with React Testing Library
- Integration tests for data flow
- Mock service worker for API testing
- Visual regression testing

### End-to-End Testing
- Critical user journey automation
- Cross-browser compatibility testing
- Performance monitoring
- Accessibility compliance verification

## 📱 Responsive Design

### Breakpoints
- **Mobile:** 320px - 768px
- **Tablet:** 768px - 1024px
- **Desktop:** 1024px - 1280px
- **Large Desktop:** 1280px+

### Mobile Adaptations
- Collapsible navigation
- Touch-optimized map controls
- Simplified data tables
- Progressive disclosure of information

## 🚀 Performance Optimizations

### Code Splitting
- Route-based chunk splitting
- Lazy loading of map libraries
- Component-level code splitting
- Dynamic imports for heavy dependencies

### Bundle Optimization
- Tree shaking for unused code
- Minification and compression
- Image optimization and WebP support
- CDN delivery for static assets

### Runtime Performance
- React.memo for expensive components
- Virtual scrolling for large datasets
- Debounced map interactions
- Efficient state management patterns

## 🔒 Security Considerations

### Content Security Policy
- Strict CSP headers in production
- XSS prevention with React's built-in protections
- Secure API communication with HTTPS
- Input sanitization for user data

### Data Privacy
- No persistent personal data storage
- Secure token handling for API authentication
- Rate limiting for API requests
- Audit logging for data access

## 🛠 Maintenance

### Dependencies
- Regular security updates via npm audit
- Automated dependency updates
- Peer dependency compatibility checks
- Legacy code migration planning

### Code Quality
- ESLint configuration for consistent style
- Prettier for code formatting
- TypeScript strict mode enforcement
- Pre-commit hooks for quality assurance

## 📚 API Integration

### Backend Endpoints
The frontend integrates with several key backend endpoints:

```typescript
// Main prediction endpoint
GET /predict?horizon={1|2|3}
Response: {
  timestamp: string;
  predictions: BackendPrediction[];
}

// Zone management
GET /zones                 // Zone metadata
GET /zones-geo            // GeoJSON geometries

// Rule-based allocation
GET /rule-based/dispatch?pf={value}&total={units}
Response: PipelineRuleBasedAllocation[];

// Health check
GET /health               // Database connectivity
```

### Error Handling
Comprehensive error handling strategy:
- Network error recovery
- Graceful degradation for missing data
- User-friendly error messages
- Automatic retry mechanisms
- Fallback to cached data

## 🎯 Future Enhancements

### Planned Features
- **Real-time WebSocket Integration:** Live data updates
- **Advanced Scenario Planning:** "What-if" analysis tools
- **Mobile Application:** React Native emergency responder app
- **Offline Capabilities:** Service worker for offline operation
- **Multi-language Support:** Internationalization (i18n)
- **Advanced Analytics:** Machine learning insights

### Technical Improvements
- **Micro-frontend Architecture:** Module splitting
- **Progressive Web App:** PWA capabilities
- **WebAssembly Integration:** Heavy computation optimizations
- **3D Visualization:** Three.js for advanced mapping
- **Voice Interface:** Speech recognition for hands-free operation

## 📞 Support and Contributing

### Getting Help
- **Documentation:** Check this README and inline code comments
- **Issue Tracking:** Use GitHub issues for bug reports
- **Development Guide:** See CONTRIBUTING.md for development setup
- **Code Review:** All changes require peer review approval

### Development Workflow
1. Feature branch development
2. TypeScript strict compliance
3. Automated testing requirements
4. Accessibility audit compliance
5. Performance impact assessment
6. Security review for sensitive changes

---

**Built with ❤️ for Emergency Operations Centers**
**MAI IDSS - Flood Prediction System**