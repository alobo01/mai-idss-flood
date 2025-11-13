# 🔧 Development

Comprehensive development setup guide and best practices for contributing to the Flood Prediction Frontend.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Debugging Guide](#debugging-guide)
- [Component Development](#component-development)
- [API Development](#api-development)
- [Testing Guidelines](#testing-guidelines)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

## Overview

This guide covers everything you need to know to develop and contribute to the Flood Prediction Frontend application. It includes setup instructions, coding standards, development workflow, and best practices.

### Development Philosophy

- **Component-First**: Build reusable, composable components
- **Type-Safe**: Leverage TypeScript for robust code
- **Mobile-First**: Design for mobile devices first
- **Test-Driven**: Write tests alongside features
- **Performance-Conscious**: Optimize for user experience
- **Accessible**: Build for all users

## Prerequisites

### System Requirements

**Minimum**:
- **Operating System**: Windows 10, macOS 10.15, or Linux (Ubuntu 18.04+)
- **Node.js**: Version 18.x or higher
- **npm**: Version 8.x or higher
- **RAM**: 8GB
- **Storage**: 10GB free space

**Recommended**:
- **Operating System**: Latest macOS, Windows 11, or Ubuntu 20.04+
- **Node.js**: Version 20.x LTS
- **npm**: Version 10.x
- **RAM**: 16GB
- **Storage**: 50GB SSD
- **Monitor**: 1920x1080 or higher resolution

### Required Tools

```bash
# Verify installations
node --version  # Should be 18.x or higher
npm --version   # Should be 8.x or higher
git --version   # Should be 2.30 or higher

# Optional but recommended tools
code --version  # VS Code
docker --version # Docker Desktop
```

### Recommended VS Code Extensions

```json
{
  "recommendations": [
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "ms-vscode.vscode-typescript-next",
    "ms-playwright.playwright",
    "ms-vscode.vscode-json",
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense",
    "ms-vscode.vscode-jest",
    "ms-vscode.live-server"
  ]
}
```

## Local Development Setup

### 1. Repository Setup

```bash
# Clone the repository
git clone <repository-url>
cd flood-prediction-frontend

# Install dependencies
npm install

# Install Playwright browsers for testing
npx playwright install

# Verify installation
npm run type-check
npm run lint
```

### 2. Environment Configuration

```bash
# Create environment file
cp .env.example .env.development

# Edit environment variables
nano .env.development
```

```env
# .env.development
VITE_API_BASE_URL=http://localhost:18080
VITE_MAP_TILES_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
VITE_WS_URL=ws://localhost:18080
VITE_ENVIRONMENT=development
VITE_LOG_LEVEL=debug
VITE_ENABLE_MOCK_API=true
```

### 3. Development Server

```bash
# Start development server (terminal 1)
npm run dev

# Start mock API server (terminal 2)
cd mock-api
npm install
npm start

# Alternative: Use Docker for complete environment
docker compose up --build
```

### 4. Verification

```bash
# Open application
# Should be available at http://localhost:5173

# Run tests to verify setup
npm run test

# Check for any issues
npm run type-check
npm run lint
```

## Project Structure

### Directory Overview

```
flood-prediction-frontend/
├── src/                          # Source code
│   ├── components/               # Reusable UI components
│   │   ├── ui/                  # Basic UI elements
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   └── index.ts         # Barrel exports
│   │   ├── layout/              # Layout components
│   │   │   ├── AppShell.tsx
│   │   │   ├── Header.tsx
│   │   │   └── Sidebar.tsx
│   │   ├── forms/               # Form components
│   │   └── charts/              # Data visualization
│   ├── pages/                   # Route-level pages
│   │   ├── RoleSelector.tsx
│   │   ├── administrator/
│   │   ├── planner/
│   │   ├── coordinator/
│   │   └── analyst/
│   ├── hooks/                   # Custom React hooks
│   │   ├── useAppContext.ts
│   │   ├── useApi.ts
│   │   └── useLocalStorage.ts
│   ├── contexts/                # React contexts
│   │   └── AppContext.tsx
│   ├── services/                # API services
│   │   ├── api.ts
│   │   ├── zones.ts
│   │   └── resources.ts
│   ├── types/                   # TypeScript definitions
│   │   ├── index.ts
│   │   ├── api.ts
│   │   └── app.ts
│   ├── utils/                   # Utility functions
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── constants.ts
│   ├── styles/                  # Global styles
│   │   └── globals.css
│   ├── App.tsx                  # Root component
│   └── main.tsx                 # Entry point
├── public/                      # Static assets
│   ├── mock/                    # Mock data files
│   └── favicon.ico
├── tests/                       # Test files
│   ├── e2e/                     # End-to-end tests
│   ├── integration/             # Integration tests
│   └── utils/                   # Test utilities
├── mock-api/                    # Mock API server
│   ├── server.js
│   ├── package.json
│   └── data/
├── docs/                        # Documentation
├── docker-compose.yml
├── Dockerfile
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── playwright.config.ts
└── README.md
```

### Component Organization

```typescript
// Component naming convention
PascalCase for components
kebab-case for files
camelCase for functions/variables

// Example structure
components/
├── ui/
│   ├── button/
│   │   ├── Button.tsx          # Main component
│   │   ├── Button.test.tsx     # Tests
│   │   ├── Button.stories.tsx  # Stories (if using Storybook)
│   │   └── index.ts            # Exports
│   └── card/
│       ├── Card.tsx
│       ├── Card.test.tsx
│       └── index.ts
```

## Development Workflow

### 1. Feature Development

```bash
# Create feature branch
git checkout -b feature/new-feature-name

# Development work
# ... write code ...

# Run tests frequently
npm run test

# Check types and linting
npm run type-check
npm run lint

# Commit changes
git add .
git commit -m "feat: add new feature description"

# Push branch
git push origin feature/new-feature-name
```

### 2. Commit Message Convention

```bash
# Format: <type>(<scope>): <description>

# Types
feat:     New feature
fix:      Bug fix
docs:     Documentation changes
style:    Code style changes (formatting, etc.)
refactor: Code refactoring
test:     Adding or updating tests
chore:    Build process or auxiliary tool changes

# Examples
feat(planner): add risk map component
fix(auth): resolve role switching issue
docs(readme): update installation instructions
test(e2e): add mobile navigation tests
```

### 3. Pull Request Process

```bash
# Create pull request
# Title should match commit message format
# Description should include:
# - What was changed
# - Why it was changed
# - How to test
# - Screenshots if UI changes

# PR Template
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
```

### 4. Code Review Guidelines

**For Reviewers**:
1. **Functionality**: Does the code work as intended?
2. **Code Quality**: Is it readable, maintainable, and follows conventions?
3. **Performance**: Are there any performance implications?
4. **Security**: Are there any security concerns?
5. **Testing**: Are tests adequate and appropriate?
6. **Documentation**: Is the code properly documented?

**For Authors**:
1. **Self-Review**: Review your own code first
2. **Test Coverage**: Ensure new code is tested
3. **Documentation**: Update relevant documentation
4. **Simplify**: Remove unnecessary complexity
5. **Consistency**: Follow existing patterns

## Coding Standards

### TypeScript Standards

```typescript
// Use explicit types
interface User {
  id: string;
  name: string;
  role: Role;
}

// Use generics for reusable components
interface Props<T> {
  data: T[];
  renderItem: (item: T) => React.ReactNode;
}

// Use utility types
type PartialUser = Partial<User>;
type UserWithoutId = Omit<User, 'id'>;

// Prefer union types over enums
type Role = 'Administrator' | 'Planner' | 'Coordinator' | 'Data Analyst';

// Use readonly for immutable data
interface ReadonlyConfig {
  readonly apiUrl: string;
  readonly timeout: number;
}
```

### React Component Standards

```typescript
// Component structure
interface Props {
  title: string;
  onSubmit: (data: FormData) => void;
  disabled?: boolean;
}

const MyComponent: React.FC<Props> = ({
  title,
  onSubmit,
  disabled = false
}) => {
  // Hooks at the top
  const [isLoading, setIsLoading] = useState(false);
  const { data, error } = useApi('/endpoint');

  // Event handlers
  const handleSubmit = useCallback((data: FormData) => {
    setIsLoading(true);
    onSubmit(data);
  }, [onSubmit]);

  // Effects
  useEffect(() => {
    // Side effects
  }, []);

  // Conditional rendering
  if (error) {
    return <ErrorMessage error={error} />;
  }

  return (
    <div className="my-component">
      <h2>{title}</h2>
      {/* Component content */}
    </div>
  );
};

export default MyComponent;
```

### CSS and Styling Standards

```typescript
// Tailwind CSS approach
<div className="flex items-center justify-between p-4 bg-white rounded-lg shadow-md border border-gray-200">
  <h3 className="text-lg font-semibold text-gray-900">
    {title}
  </h3>
  <Button variant="outline" size="sm">
    Action
  </Button>
</div>

// CSS-in-JS for dynamic styles
<div
  className={cn(
    "base-classes",
    isActive && "active-classes",
    isDisabled && "disabled-classes"
  )}
>

// Use CSS variables for theming
:root {
  --color-primary: 59 130 246;
  --color-secondary: 107 114 128;
}

.button {
  background-color: rgb(var(--color-primary));
}
```

### File Naming Conventions

```
# Components
ComponentName.tsx
ComponentName.test.tsx
ComponentName.stories.tsx

# Hooks
useHookName.ts
useHookName.test.ts

# Utilities
utilityFunction.ts
utilityFunction.test.ts

# Types
types.ts
index.ts (for barrel exports)

# Constants
constants.ts
config.ts
```

## Debugging Guide

### Browser DevTools

```typescript
// Debug components with React DevTools
// 1. Install React Developer Tools extension
// 2. Use Components tab to inspect component tree
// 3. Use Profiler tab to analyze performance

// Debug state and props
console.log('Component state:', { state, props });
console.table(dataArray);

// Debug network requests
// 1. Use Network tab in DevTools
// 2. Filter by XHR/Fetch
// 3. Check request/response details
```

### VS Code Debugging

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "node",
      "request": "launch",
      "name": "Debug React App",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "port": 9229,
      "webRoot": "${workspaceFolder}/src"
    },
    {
      "type": "node",
      "request": "launch",
      "name": "Debug Tests",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "test", "--debug"],
      "port": 9229,
      "webRoot": "${workspaceFolder}/src"
    }
  ]
}
```

### Common Debugging Techniques

```typescript
// Conditional debugging
if (process.env.NODE_ENV === 'development') {
  console.log('Debug info:', debugData);
}

// Debug component renders
useEffect(() => {
  console.log('Component mounted/updated:', { props, state });
});

// Debug API calls
const debugApiCall = async (url: string) => {
  console.log('API Call:', url);
  try {
    const response = await fetch(url);
    console.log('API Response:', response);
    return response;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

// Debug form data
const handleSubmit = (data: FormData) => {
  console.log('Form submitted:', data);
  // ... handle submission
};
```

### Performance Debugging

```typescript
// Measure render performance
const measureRender = (componentName: string) => {
  const startTime = performance.now();
  return () => {
    const endTime = performance.now();
    console.log(`${componentName} render time:`, endTime - startTime);
  };
};

// Use React Profiler
<Profiler id="MyComponent" onRender={(id, phase, actualTime) => {
  console.log(`${id} ${phase} took ${actualTime}ms`);
}}>
  <MyComponent />
</Profiler>

// Debug bundle size
npm run build:analyze
```

## Component Development

### Component Template

```typescript
// Component template
import React, { useState, useEffect, useCallback } from 'react';
import { cn } from '@/utils/cn';

interface Props {
  // Define props with proper typing
  title: string;
  variant?: 'default' | 'secondary';
  onSubmit?: (data: any) => void;
  children?: React.ReactNode;
  className?: string;
}

const ComponentName: React.FC<Props> = ({
  title,
  variant = 'default',
  onSubmit,
  children,
  className,
}) => {
  // State management
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Side effects
  useEffect(() => {
    // Component mount/update logic
  }, []);

  // Event handlers
  const handleSubmit = useCallback((data: any) => {
    setIsLoading(true);
    setError(null);

    try {
      onSubmit?.(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [onSubmit]);

  // Derived state
  const isDisabled = isLoading || !onSubmit;

  // Render
  return (
    <div className={cn(
      "base-component-classes",
      variant === 'secondary' && "variant-classes",
      className
    )}>
      <h2 className="component-title">{title}</h2>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {children}

      <button
        onClick={handleSubmit}
        disabled={isDisabled}
        className="submit-button"
      >
        {isLoading ? 'Loading...' : 'Submit'}
      </button>
    </div>
  );
};

export default ComponentName;
```

### Custom Hooks

```typescript
// Custom hook template
import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface UseApiOptions<T> {
  immediate?: boolean;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

export const useApi = <T>(
  url: string,
  options: UseApiOptions<T> = {}
) => {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    immediate = true,
    onSuccess,
    onError,
  } = options;

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
      onSuccess?.(result);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      onError?.(error);
    } finally {
      setIsLoading(false);
    }
  }, [url, onSuccess, onError]);

  useEffect(() => {
    if (immediate) {
      fetchData();
    }
  }, [immediate, fetchData]);

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, error, isLoading, refetch };
};
```

### Form Development

```typescript
// Form with validation
import { useForm, zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const formSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email address'),
  role: z.enum(['Administrator', 'Planner', 'Coordinator', 'Data Analyst']),
});

type FormData = z.infer<typeof formSchema>;

const UserForm: React.FC = () => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
  });

  const onSubmit = async (data: FormData) => {
    try {
      await createUser(data);
      reset();
    } catch (error) {
      console.error('Failed to create user:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="name">Name</label>
        <input
          id="name"
          {...register('name')}
          className="form-input"
        />
        {errors.name && (
          <p className="error-text">{errors.name.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          {...register('email')}
          className="form-input"
        />
        {errors.email && (
          <p className="error-text">{errors.email.message}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="submit-button"
      >
        {isSubmitting ? 'Creating...' : 'Create User'}
      </button>
    </form>
  );
};
```

## API Development

### Service Layer Pattern

```typescript
// services/api.ts
class ApiService {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseUrl: string = import.meta.env.VITE_API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const config: RequestInit = {
      headers: { ...this.defaultHeaders, ...options.headers },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const apiService = new ApiService();
```

### Specific API Services

```typescript
// services/zones.ts
import { apiService } from './api';
import { Zone, CreateZoneRequest, UpdateZoneRequest } from '@/types';

export const zonesService = {
  async getZones(): Promise<Zone[]> {
    return apiService.get<Zone[]>('/zones');
  },

  async getZone(id: string): Promise<Zone> {
    return apiService.get<Zone>(`/zones/${id}`);
  },

  async createZone(data: CreateZoneRequest): Promise<Zone> {
    return apiService.post<Zone>('/zones', data);
  },

  async updateZone(id: string, data: UpdateZoneRequest): Promise<Zone> {
    return apiService.put<Zone>(`/zones/${id}`, data);
  },

  async deleteZone(id: string): Promise<void> {
    return apiService.delete<void>(`/zones/${id}`);
  },
};
```

### React Query Integration

```typescript
// hooks/useZones.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { zonesService } from '@/services/zones';
import { Zone, CreateZoneRequest } from '@/types';

export const useZones = () => {
  return useQuery({
    queryKey: ['zones'],
    queryFn: () => zonesService.getZones(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useZone = (id: string) => {
  return useQuery({
    queryKey: ['zones', id],
    queryFn: () => zonesService.getZone(id),
    enabled: !!id,
  });
};

export const useCreateZone = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateZoneRequest) => zonesService.createZone(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['zones'] });
    },
  });
};

export const useUpdateZone = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateZoneRequest }) =>
      zonesService.updateZone(id, data),
    onSuccess: (updatedZone) => {
      queryClient.setQueryData(['zones', updatedZone.id], updatedZone);
      queryClient.invalidateQueries({ queryKey: ['zones'] });
    },
  });
};
```

## Testing Guidelines

### Unit Testing

```typescript
// Example unit test
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppProvider } from '@/contexts/AppContext';
import MyComponent from './MyComponent';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const renderWithProviders = (component: React.ReactElement) => {
  const testQueryClient = createTestQueryClient();

  return render(
    <QueryClientProvider client={testQueryClient}>
      <AppProvider>
        {component}
      </AppProvider>
    </QueryClientProvider>
  );
};

describe('MyComponent', () => {
  test('renders correctly with default props', () => {
    renderWithProviders(<MyComponent title="Test" />);

    expect(screen.getByText('Test')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  test('calls onSubmit when form is submitted', async () => {
    const onSubmit = jest.fn();

    renderWithProviders(
      <MyComponent title="Test" onSubmit={onSubmit} />
    );

    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledTimes(1);
    });
  });

  test('displays error message when submission fails', async () => {
    const onSubmit = jest.fn().mockRejectedValue(new Error('Test error'));

    renderWithProviders(
      <MyComponent title="Test" onSubmit={onSubmit} />
    );

    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText('Test error')).toBeInTheDocument();
    });
  });
});
```

### Integration Testing

```typescript
// Example integration test
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from '../App';

const renderApp = () => {
  return render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
};

describe('Application Integration', () => {
  test('navigates from role selector to planner dashboard', async () => {
    renderApp();

    // Should start on role selector
    expect(screen.getByText('Flood Prediction System')).toBeInTheDocument();

    // Click on planner role
    fireEvent.click(screen.getByText('Select Planner'));

    // Should navigate to planner dashboard
    await waitFor(() => {
      expect(screen.getByText('Risk Map')).toBeInTheDocument();
    });
  });

  test('dark mode toggle works across navigation', async () => {
    renderApp();

    // Enable dark mode
    fireEvent.click(screen.getByLabelText('Toggle dark mode'));
    expect(document.documentElement).toHaveClass('dark');

    // Navigate to different role
    fireEvent.click(screen.getByText('Select Coordinator'));

    // Dark mode should persist
    await waitFor(() => {
      expect(document.documentElement).toHaveClass('dark');
    });
  });
});
```

## Performance Optimization

### Code Splitting

```typescript
// Route-based code splitting
import { lazy, Suspense } from 'react';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

const PlannerRoutes = lazy(() => import('@/pages/planner/PlannerRoutes'));
const CoordinatorRoutes = lazy(() => import('@/pages/coordinator/CoordinatorRoutes'));

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<RoleSelector />} />
        <Route
          path="/planner/*"
          element={
            <Suspense fallback={<LoadingSpinner />}>
              <PlannerRoutes />
            </Suspense>
          }
        />
        <Route
          path="/coordinator/*"
          element={
            <Suspense fallback={<LoadingSpinner />}>
              <CoordinatorRoutes />
            </Suspense>
          }
        />
      </Routes>
    </Router>
  );
};
```

### Bundle Analysis

```bash
# Analyze bundle size
npm run build:analyze

# Check bundle composition
npm run build
npx vite-bundle-analyzer dist/static/js/*.js

# Find large dependencies
npx webpack-bundle-analyzer dist/static/js/*.js
```

### React Optimization

```typescript
// Use React.memo for expensive components
const ExpensiveComponent = React.memo(({ data }) => {
  return <div>{/* Complex rendering logic */}</div>;
});

// Use useMemo for expensive calculations
const ExpensiveList: React.FC<{ items: Item[] }> = ({ items }) => {
  const processedItems = useMemo(() => {
    return items.map(item => ({
      ...item,
      computed: expensiveCalculation(item),
    }));
  }, [items]);

  return <div>{/* Render processedItems */}</div>;
};

// Use useCallback for stable function references
const Parent: React.FC = () => {
  const [count, setCount] = useState(0);

  const handleClick = useCallback(() => {
    setCount(c => c + 1);
  }, []);

  return <Child onClick={handleClick} />;
};
```

## Troubleshooting

### Common Development Issues

**TypeScript Errors**:
```bash
# Clear TypeScript cache
rm -rf node_modules/.cache
npm run type-check

# Check TypeScript configuration
npx tsc --noEmit

# Update types
npm update @types/*
```

**Build Issues**:
```bash
# Clear build cache
rm -rf dist
npm run build

# Check for circular dependencies
npx madge --circular src/

# Analyze bundle
npm run build:analyze
```

**Dependency Issues**:
```bash
# Clear and reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check for vulnerabilities
npm audit

# Fix vulnerabilities
npm audit fix
```

**DevTools Issues**:
```bash
# Reset development environment
docker compose down -v
docker compose up --build

# Check port conflicts
lsof -ti:5173
lsof -ti:18080
```

### Performance Issues

**Slow Initial Load**:
```typescript
// Use dynamic imports for heavy components
const HeavyChart = lazy(() => import('./HeavyChart'));

// Implement loading states
<Suspense fallback={<LoadingSkeleton />}>
  <HeavyChart />
</Suspense>

// Optimize images and assets
// Use next-gen formats (WebP, AVIF)
// Implement lazy loading
```

**Slow Re-renders**:
```typescript
// Profile components with React DevTools
// Use React.memo to prevent unnecessary re-renders
// Optimize context value to prevent cascading updates

// Bad: Creates new object on every render
const contextValue = { state, dispatch };

// Good: Memoized context value
const contextValue = useMemo(() => ({ state, dispatch }), [state, dispatch]);
```

This development guide provides comprehensive information for setting up a productive development environment and following best practices for contributing to the Flood Prediction Frontend application.

## 🚀 Administrator Portal Development

The Administrator portal is now fully functional with complete database management capabilities. Here are key development considerations:

### Key Features Implemented

1. **Complete Administrator Interface**
   - User Management with role-based access control
   - Threshold Configuration (risk, gauge, alert rules)
   - Resource Management (depots, equipment, crews)
   - Interactive Region Management with ZoneEditor

2. **Reusable Components**
   - **DataTable**: Full-featured data table with search, sort, pagination
   - **FormDialog**: Modal forms with comprehensive validation
   - **UI Components**: Complete shadcn/ui component library

3. **Mock API Server**
   - Express.js server with 30+ administrator endpoints
   - Complete CRUD operations for all resources
   - Data validation and business logic enforcement
   - Export functionality for data backup

### Development Scripts

```bash
# Start complete development environment
npm run dev:full

# Individual services
npm run dev          # Frontend only
npm run api           # Mock API server
npm run api:dev       # API with hot reload

# Testing and building
npm run test          # E2E tests
npm run build         # Production build
```

### Administrator Portal Access

1. **Start the development server**
   ```bash
   npm run dev:full
   ```

2. **Access the application**
   - URL: http://localhost:5173
   - Role: Select "Administrator"

3. **Explore Administrator Features**
   - User Management (`/admin/users`)
   - Threshold Configuration (`/admin/thresholds`)
   - Resource Management (`/admin/resources`)
   - Region Management (`/admin/regions`)

### Mock API Endpoints

The mock API server provides complete administrator functionality:

- **User Management**: `/api/admin/users/*`
- **Threshold Management**: `/api/admin/thresholds/*`
- **Resource Management**: `/api/admin/resources/*`
- **Zone Management**: `/api/admin/zones`
- **Export**: `/api/admin/export/:type`

Complete API documentation: [Admin API Reference](api/admin-endpoints.md)

### Administrator Documentation

Comprehensive documentation has been created:

- **[Administrator Guide](../ADMIN_README.md)**: Complete portal overview
- **[Setup Guide](administrator/setup.md)**: Initial configuration
- **[User Management](administrator/user-management.md)**: User account administration
- **[Security Guide](administrator/security.md)**: Security best practices
- **[API Reference](api/admin-endpoints.md)**: Complete API documentation

### Testing the Administrator Portal

```bash
# Run all tests
npm run test

# Run specific administrator tests
npx playwright test admin-user-management.spec.ts
npx playwright test admin-thresholds.spec.ts
npx playwright test admin-resources.spec.ts
```

The Administrator portal is production-ready with comprehensive functionality for non-technical users to manage all aspects of the flood prediction system database.