# 🏗️ Architecture

System design, technical decisions, and architectural patterns for the Flood Prediction Frontend.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Frontend Architecture](#frontend-architecture)
- [Backend Architecture](#backend-architecture)
- [Data Flow](#data-flow)
- [Component Architecture](#component-architecture)
- [State Management](#state-management)
- [Security Architecture](#security-architecture)
- [Performance Architecture](#performance-architecture)
- [Scalability Considerations](#scalability-considerations)

## Overview

The Flood Prediction Frontend is a modern web application designed for real-time flood prediction management. It follows a microservices architecture with a clear separation between frontend and backend concerns.

### Key Architectural Principles

- **Component-Based**: Modular, reusable React components
- **Role-Based Access**: Separate interfaces for different user types
- **Mobile-First**: Responsive design prioritizing mobile experience
- **Type-Safe**: Comprehensive TypeScript implementation
- **Test-Driven**: Extensive automated testing coverage
- **Container-Native**: Docker-based deployment and development

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Browser                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   React App     │  │   React Router  │  │  React Query │ │
│  │   (TypeScript)  │  │   (Navigation)  │  │ (Data Layer) │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   CORS Config   │  │  Rate Limiting  │  │  Auth Proxy  │ │
│  │                 │  │                 │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Services Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Mock API      │  │  Real-Time WS   │  │   File Store │ │
│  │  (Express.js)   │  │   Simulation    │  │   (JSON)     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Container Architecture

```yaml
Services:
  - web:
      image: flood-frontend:latest
      ports: ["5173:80"]
      technology: React + nginx

  - api:
      image: flood-api:latest
      ports: ["8080:8080"]
      technology: Node.js + Express

  - database: (Future)
      image: postgres:latest
      ports: ["5432:5432"]
      technology: PostgreSQL + PostGIS

Networks:
  - flood-network:
      driver: bridge
      isolated: true
```

## Frontend Architecture

### Application Structure

```
src/
├── components/          # Reusable UI components
│   ├── ui/             # Basic UI elements (Button, Card, etc.)
│   ├── layout/         # Layout components (AppShell, Header)
│   ├── forms/          # Form components
│   └── charts/         # Data visualization components
├── pages/              # Route-level page components
│   ├── administrator/  # Administrator-specific pages
│   ├── planner/        # Planner-specific pages
│   ├── coordinator/    # Coordinator-specific pages
│   └── analyst/        # Data Analyst pages
├── hooks/              # Custom React hooks
├── contexts/           # React context providers
├── services/           # API service layer
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
└── styles/             # Global styles and themes
```

### Component Hierarchy

```
App
├── BrowserRouter
├── QueryClientProvider
├── AppProvider
└── Routes
    ├── RoleSelector
    └── AppShell
        ├── Header
        │   ├── DarkModeToggle
        │   └── RoleSwitcher
        ├── Sidebar
        │   └── Navigation
        └── Main
            └── [Page Components]
```

### Routing Architecture

**Route Definitions**:
```typescript
const routes = [
  { path: '/', element: <RoleSelector /> },
  {
    path: '/administrator/*',
    element: <AppShell role="Administrator">
      <AdministratorRoutes />
    </AppShell>
  },
  {
    path: '/planner/*',
    element: <AppShell role="Planner">
      <PlannerRoutes />
    </AppShell>
  },
  // ... other roles
];
```

**Route Guards**:
- Authentication check via AppContext
- Role-based access control
- Redirect fallbacks for invalid routes

## Backend Architecture

### Mock API Structure

```
mock-api/
├── server.js           # Express server setup
├── routes/             # API route definitions
│   ├── zones.js        # Geographic zones
│   ├── risk.js         # Risk data
│   ├── resources.js    # Resource management
│   └── alerts.js       # Alert system
├── middleware/         # Express middleware
│   ├── cors.js         # CORS configuration
│   ├── auth.js         # Authentication (mock)
│   └── validation.js   # Request validation
├── data/               # Mock data files
└── utils/              # API utilities
```

### API Endpoints Architecture

```typescript
// RESTful API Design
GET    /api/zones              // List all zones
GET    /api/zones/:id          // Get specific zone
POST   /api/zones              // Create new zone
PUT    /api/zones/:id          // Update zone
DELETE /api/zones/:id          // Delete zone

GET    /api/risk               // Get risk data
GET    /api/risk?at=timestamp  // Get time-specific risk

GET    /api/resources          // List resources
POST   /api/resources          // Allocate resources

GET    /api/alerts             // Get alerts
POST   /api/alerts             // Create alert
PUT    /api/alerts/:id/ack     // Acknowledge alert
```

### Data Layer Architecture

```typescript
// Service Layer Pattern
class ZoneService {
  async getZones(): Promise<Zone[]> {
    return api.get('/zones');
  }

  async getZoneRisk(zoneId: string, timestamp: string): Promise<RiskData> {
    return api.get(`/risk?zone=${zoneId}&at=${timestamp}`);
  }
}

// Repository Pattern (Future for database)
class ZoneRepository {
  async findById(id: string): Promise<Zone | null> {
    return db.zones.findUnique({ where: { id } });
  }

  async create(zone: CreateZoneDto): Promise<Zone> {
    return db.zones.create({ data: zone });
  }
}
```

## Data Flow

### Application Data Flow

```
User Interaction
       │
       ▼
React Component
       │
       ▼
Custom Hook (useQuery/useMutation)
       │
       ▼
React Query Cache
       │
       ▼
API Service Layer
       │
       ▼
HTTP Request
       │
       ▼
Express API
       │
       ▼
Mock Data Store
```

### State Management Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Local State    │    │  Context State  │    │  Server State   │
│  (useState)     │    │  (AppContext)   │    │  (React Query)  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ Form inputs     │    │ User role       │    │ Zones data      │
│ UI toggles      │    │ Dark mode       │    │ Risk data       │
│ Component state │    │ Selected zone   │    │ Resources       │
│                 │    │ Navigation      │    │ Alerts          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Caching Strategy

```typescript
// React Query Configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,     // 5 minutes
      cacheTime: 10 * 60 * 1000,    // 10 minutes
      refetchOnWindowFocus: false,
      retry: 3,
    },
  },
});

// Selective Cache Invalidation
const useCreateAlert = () => {
  return useMutation({
    mutationFn: createAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
};
```

## Component Architecture

### Component Patterns

#### 1. Compound Components

```typescript
// Map View Compound Component
<MapView>
  <MapContainer center={center} zoom={zoom}>
    <TileLayer url={tileUrl} />
    <ZonesLayer />
    <RiskLayer />
    <MarkersLayer />
  </MapContainer>
  <MapControls>
    <LayerToggle />
    <TimeSlider />
    <ZoomControls />
  </MapControls>
</MapView>
```

#### 2. Render Props Pattern

```typescript
// DataTable with Render Props
<DataTable
  data={resources}
  columns={columns}
  renderRow={(resource, index) => (
    <ResourceRow
      key={resource.id}
      resource={resource}
      onUpdate={handleUpdate}
    />
  )}
  renderEmpty={() => <EmptyState message="No resources found" />}
/>
```

#### 3. Higher-Order Components

```typescript
// withRole HOC
export const withRole = <P extends object>(RequiredRole: Role) =>
  (Component: React.ComponentType<P>) => {
    return (props: P) => {
      const { currentRole } = useAppContext();

      if (currentRole !== RequiredRole) {
        return <AccessDenied />;
      }

      return <Component {...props} />;
    };
  };

// Usage
const AdminOnlyUsers = withRole('Administrator')(UsersPage);
```

### Component Architecture Principles

1. **Single Responsibility**: Each component has one clear purpose
2. **Composition over Inheritance**: Build complex UIs from simple components
3. **Props Interface**: Clear, typed props contracts
4. **Controlled Components**: Predictable state management
5. **Error Boundaries**: Graceful error handling

## State Management

### Local State Management

```typescript
// Component State Pattern
const ResourceCard: React.FC<ResourceCardProps> = ({ resource }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleExpand = useCallback(() => {
    setIsExpanded(prev => !prev);
  }, []);

  return (
    <Card>
      <CardHeader onClick={handleExpand}>
        {resource.name}
      </CardHeader>
      {isExpanded && (
        <CardContent>
          {/* Expanded content */}
        </CardContent>
      )}
    </Card>
  );
};
```

### Global State Management

```typescript
// Context API Pattern
interface AppContextType {
  currentRole: Role | null;
  setCurrentRole: (role: Role | null) => void;
  darkMode: boolean;
  setDarkMode: (enabled: boolean) => void;
  selectedZone: string | null;
  setSelectedZone: (zoneId: string | null) => void;
}

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Memoize context value to prevent unnecessary re-renders
  const contextValue = useMemo(() => ({
    ...state,
    dispatch
  }), [state]);

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};
```

### Server State Management

```typescript
// React Query Pattern
const useZones = () => {
  return useQuery({
    queryKey: ['zones'],
    queryFn: () => zoneService.getZones(),
    staleTime: 10 * 60 * 1000, // 10 minutes
    select: (data) => data.sort((a, b) => a.name.localeCompare(b.name)),
  });
};

const useUpdateZone = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: zoneService.updateZone,
    onSuccess: (updatedZone) => {
      queryClient.setQueryData(['zones'], (old: Zone[] | undefined) =>
        old?.map(zone => zone.id === updatedZone.id ? updatedZone : zone)
      );
    },
  });
};
```

## Security Architecture

### Authentication Architecture

```typescript
// JWT Token Management (Future Implementation)
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  permissions: Permission[];
}

const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    token: localStorage.getItem('authToken'),
    isAuthenticated: false,
    permissions: [],
  });

  const login = useCallback(async (credentials: LoginCredentials) => {
    try {
      const response = await authService.login(credentials);
      const { user, token, permissions } = response.data;

      localStorage.setItem('authToken', token);
      setAuthState({ user, token, isAuthenticated: true, permissions });
    } catch (error) {
      throw new AuthenticationError('Invalid credentials');
    }
  }, []);

  return { ...authState, login, logout };
};
```

### Role-Based Access Control (RBAC)

```typescript
// Permission System
interface Permission {
  resource: string;
  action: 'read' | 'write' | 'delete' | 'admin';
}

const rolePermissions: Record<Role, Permission[]> = {
  Administrator: [
    { resource: 'zones', action: 'admin' },
    { resource: 'users', action: 'admin' },
    { resource: 'resources', action: 'admin' },
    { resource: 'thresholds', action: 'admin' },
  ],
  Planner: [
    { resource: 'zones', action: 'read' },
    { resource: 'risk', action: 'read' },
    { resource: 'scenarios', action: 'write' },
    { resource: 'alerts', action: 'read' },
  ],
  // ... other roles
};

// Permission Hook
const usePermissions = () => {
  const { currentRole } = useAppContext();

  const hasPermission = useCallback((resource: string, action: string) => {
    const permissions = rolePermissions[currentRole!] || [];
    return permissions.some(p => p.resource === resource && p.action === action);
  }, [currentRole]);

  return { hasPermission };
};
```

### Data Validation Architecture

```typescript
// Zod Schema Validation
const CreateZoneSchema = z.object({
  name: z.string().min(1).max(100),
  geometry: z.object({
    type: z.literal('Polygon'),
    coordinates: z.array(z.array(z.tuple([z.number(), z.number()]))),
  }),
  population: z.number().int().nonnegative(),
  criticalAssets: z.array(z.string()).optional(),
});

// API Validation Middleware
const validateRequest = (schema: z.ZodSchema) => {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      schema.parse(req.body);
      next();
    } catch (error) {
      res.status(400).json({ error: 'Invalid request data', details: error });
    }
  };
};
```

## Performance Architecture

### Bundle Optimization

```typescript
// Code Splitting Configuration
const PlannerRoutes = lazy(() => import('./pages/planner/PlannerRoutes'));
const CoordinatorRoutes = lazy(() => import('./pages/coordinator/CoordinatorRoutes'));

// Dynamic Imports for Heavy Components
const MapView = lazy(() => import('./components/MapView'));
const ChartComponent = lazy(() => import('./components/ChartComponent'));

// Route-based Code Splitting
const router = createBrowserRouter([
  {
    path: '/',
    element: <RoleSelector />,
  },
  {
    path: '/planner/*',
    element: <Suspense fallback={<Loading />}><PlannerRoutes /></Suspense>,
  },
  // ... other routes
]);
```

### Performance Monitoring

```typescript
// Performance Metrics Hook
const usePerformanceMetrics = () => {
  const [metrics, setMetrics] = useState({
    renderTime: 0,
    apiResponseTime: 0,
    memoryUsage: 0,
  });

  useEffect(() => {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      entries.forEach((entry) => {
        if (entry.entryType === 'measure') {
          setMetrics(prev => ({
            ...prev,
            [entry.name]: entry.duration,
          }));
        }
      });
    });

    observer.observe({ entryTypes: ['measure'] });

    return () => observer.disconnect();
  }, []);

  return metrics;
};
```

### Caching Strategy

```typescript
// Service Worker for Offline Caching
const registerServiceWorker = async () => {
  if ('serviceWorker' in navigator) {
    const registration = await navigator.serviceWorker.register('/sw.js');

    // Cache essential API responses
    registration.addEventListener('message', (event) => {
      if (event.data.type === 'CACHE_UPDATED') {
        queryClient.invalidateQueries(event.data.queryKey);
      }
    });
  }
};
```

## Scalability Considerations

### Horizontal Scaling

```typescript
// Load Balancing Configuration
// Future: Multiple frontend instances behind load balancer
const loadBalancerConfig = {
  strategy: 'round-robin',
  healthCheck: '/health',
  instances: ['web-1', 'web-2', 'web-3'],
};

// Stateless Design for Scaling
const StatelessComponent: React.FC<Props> = ({ data, onUpdate }) => {
  // No internal state that requires server affinity
  // All state passed via props or context
  return <div>{/* Component implementation */}</div>;
};
```

### Database Scaling (Future)

```typescript
// Read Replicas for Query Performance
const readReplicaConfig = {
  primary: 'postgres-primary:5432',
  replicas: [
    'postgres-replica-1:5432',
    'postgres-replica-2:5432',
  ],
  readPreference: 'secondaryPreferred',
};

// Connection Pooling
const poolConfig = {
  min: 5,
  max: 20,
  acquireTimeoutMillis: 30000,
  idleTimeoutMillis: 30000,
};
```

### Microservices Migration Path

```typescript
// Service Boundary Definitions
const serviceBoundaries = {
  authService: {
    endpoints: ['/auth/login', '/auth/logout', '/auth/refresh'],
    database: 'users',
  },
  zoneService: {
    endpoints: ['/api/zones/*'],
    database: 'zones',
  },
  riskService: {
    endpoints: ['/api/risk/*'],
    database: 'risk_data',
    caching: 'redis',
  },
  alertService: {
    endpoints: ['/api/alerts/*'],
    database: 'alerts',
    websocket: true,
  },
};
```

This architecture provides a solid foundation for the flood prediction system while maintaining flexibility for future growth and enhancements. The modular design allows for independent development, testing, and deployment of different system components.