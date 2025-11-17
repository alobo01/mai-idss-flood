# 🧪 Testing

Comprehensive testing strategy and implementation guide for the Flood Prediction Frontend application.

## Table of Contents

- [Overview](#overview)
- [Testing Strategy](#testing-strategy)
- [Test Structure](#test-structure)
- [End-to-End Testing](#end-to-end-testing)
- [Component Testing](#component-testing)
- [Integration Testing](#integration-testing)
- [Performance Testing](#performance-testing)
- [Accessibility Testing](#accessibility-testing)
- [Visual Regression Testing](#visual-regression-testing)
- [Test Data Management](#test-data-management)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The Flood Prediction Frontend employs a comprehensive testing strategy to ensure reliability, performance, and accessibility across all user roles and device types.

### Testing Objectives

- **Functionality**: Verify all features work as expected
- **Compatibility**: Test across browsers and devices
- **Performance**: Ensure fast load times and smooth interactions
- **Accessibility**: Validate WCAG AA compliance
- **User Experience**: Test realistic user scenarios
- **Error Handling**: Verify graceful failure handling

### Test Coverage Goals

- **E2E Tests**: 90%+ user journey coverage
- **Component Tests**: 80%+ component coverage
- **Integration Tests**: 100% API integration coverage
- **Accessibility**: 100% WCAG AA compliance
- **Performance**: Core Web Vitals thresholds met

## Testing Strategy

### Testing Pyramid

```
                    ┌─────────────────────┐
                    │   E2E Tests (10%)   │
                    │  Critical user paths│
                    └─────────────────────┘
                ┌─────────────────────────────┐
                │   Integration Tests (20%)   │
                │    API & component flows    │
                └─────────────────────────────┘
        ┌─────────────────────────────────────────────┐
        │          Unit/Component Tests (70%)         │
        │   Individual components & utility functions │
        └─────────────────────────────────────────────┘
```

### Test Categories

1. **Smoke Tests**: Quick validation of critical functionality
2. **Regression Tests**: Prevent breaking changes
3. **Compatibility Tests**: Cross-browser and device testing
4. **Performance Tests**: Load time and interaction speed
5. **Security Tests**: Input validation and XSS prevention
6. **Accessibility Tests**: Screen reader and keyboard navigation

## Test Structure

### Directory Organization

```
tests/
├── e2e/                    # End-to-end tests
│   ├── e2e.spec.ts        # Main E2E test suite
│   ├── edge-cases.spec.ts # Edge case scenarios
│   ├── accessibility.spec.ts # Accessibility tests
│   └── performance.spec.ts # Performance tests
├── integration/            # Integration tests
│   ├── api.spec.ts        # API integration tests
│   └── components.spec.ts # Component integration tests
├── unit/                  # Unit tests
│   ├── utils.spec.ts      # Utility function tests
│   └── hooks.spec.ts      # Custom hook tests
├── fixtures/              # Test data and fixtures
│   ├── mockData.ts        # API responses
│   └── testUsers.ts       # Test user configurations
└── utils/                 # Test utilities and helpers
    ├── testHelpers.ts     # Common test functions
    └── dataGenerators.ts  # Test data generators
```

### Configuration Files

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'test-results.xml' }],
    ['json', { outputFile: 'test-results.json' }],
  ],
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    // Desktop browsers
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    // Mobile browsers
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
    // Tablet
    {
      name: 'iPad',
      use: { ...devices['iPad Pro'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    port: 5173,
    reuseExistingServer: !process.env.CI,
  },
});
```

## End-to-End Testing

### Core User Journey Tests

```typescript
// tests/e2e/e2e.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Flood Prediction System - E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('Complete user journey for Planner role', async ({ page }) => {
    // Step 1: Role Selection
    await expect(page.getByText('Flood Prediction System')).toBeVisible();
    await page.click('text=Select Planner');

    // Step 2: Verify Navigation
    await expect(page.getByText('Risk Map')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Planner' })).toBeVisible();

    // Step 3: Navigate through all planner pages
    await page.click('text=Alerts');
    await expect(page.getByText('Alerts Timeline')).toBeVisible();

    await page.click('text=Scenarios');
    await expect(page.getByText('Scenario Workbench')).toBeVisible();

    // Step 4: Test role switching
    await page.click('text=Planner'); // Open role switcher
    await page.click('text=Coordinator');

    await expect(page).toHaveURL(/\\/coordinator\\//);
    await expect(page.getByText('Ops Board')).toBeVisible();
  });

  test('Dark mode functionality across all roles', async ({ page }) => {
    const roles = ['Administrator', 'Planner', 'Coordinator', 'Data Analyst'];

    for (const role of roles) {
      await page.goto('/');
      await page.click(`text=Select ${role}`);

      // Toggle dark mode
      const darkModeToggle = page.getByLabel('Toggle dark mode');
      await expect(darkModeToggle).toBeVisible();
      await darkModeToggle.click();

      // Verify dark mode is applied
      await expect(page.locator('html')).toHaveClass(/dark/);

      // Toggle back to light mode
      await darkModeToggle.click();
      await expect(page.locator('html')).not.toHaveClass(/dark/);
    }
  });

  test('Mobile responsive workflow', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');
    await page.click('text=Select Planner');

    // Test mobile menu
    const menuButton = page.getByLabel('Open menu');
    await expect(menuButton).toBeVisible();

    await menuButton.click();
    await expect(page.getByText('Risk Map')).toBeVisible();

    // Test touch interactions
    await page.click('text=Alerts');
    await expect(page.getByText('Alerts Timeline')).toBeVisible();

    // Close mobile menu
    await menuButton.click();
  });

  test('Keyboard navigation workflow', async ({ page }) => {
    await page.goto('/');

    // Test keyboard navigation through role selector
    await page.keyboard.press('Tab');
    let focused = await page.locator(':focus');
    await expect(focused).toContainText('Select Administrator');

    // Select role with keyboard
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/\\/administrator\\//);

    // Navigate through admin interface
    await page.keyboard.press('Tab');
    focused = await page.locator(':focus');

    // Test menu navigation with arrow keys
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
  });
});
```

### Edge Case Testing

```typescript
// tests/e2e/edge-cases.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Edge Cases and Error Handling', () => {
  test('Network error resilience', async ({ page }) => {
    // Simulate network failure
    await page.route('**/*', route => route.abort());

    await page.goto('/');
    await page.click('text=Select Planner');

    // Should show appropriate error handling
    await expect(page.getByText('Unable to connect')).toBeVisible();
  });

  test('Rapid role switching stress test', async ({ page }) => {
    await page.goto('/');

    const roles = ['Administrator', 'Planner', 'Coordinator', 'Data Analyst'];

    // Rapidly switch roles 10 times
    for (let i = 0; i < 10; i++) {
      for (const role of roles) {
        await page.click(`text=Select ${role}`);
        await expect(page.getByText(role)).toBeVisible();
        await page.waitForTimeout(100);
      }
    }

    // Application should remain stable
    await expect(page.getByText('Flood Prediction')).toBeVisible();
  });

  test('Very long content handling', async ({ page }) => {
    await page.click('text=Select Planner');

    // Test with very long zone names or data
    await page.evaluate(() => {
      const longText = 'A'.repeat(1000);
      document.body.innerHTML += `<div>${longText}</div>`;
    });

    // Should not crash or break layout
    await expect(page.getByText('Planner Risk Map')).toBeVisible();
  });

  test('Concurrent state updates', async ({ page }) => {
    await page.click('text=Select Planner');

    // Simulate multiple rapid state updates
    await page.evaluate(() => {
      for (let i = 0; i < 50; i++) {
        setTimeout(() => {
          window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab' }));
        }, i * 10);
      }
    });

    await page.waitForTimeout(1000);

    // Application should remain stable
    await expect(page.getByText('Planner Risk Map')).toBeVisible();
  });
});
```

## Component Testing

### React Component Tests

```typescript
// tests/unit/components/AppShell.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { AppShell } from '@/components/AppShell';
import { AppProvider } from '@/contexts/AppContext';

const renderWithProvider = (component: React.ReactElement) => {
  return render(
    <AppProvider>
      {component}
    </AppProvider>
  );
};

describe('AppShell Component', () => {
  test('renders header with application title', () => {
    renderWithProvider(
      <AppShell>
        <div>Test Content</div>
      </AppShell>
    );

    expect(screen.getByText('Flood Prediction')).toBeInTheDocument();
  });

  test('displays role badge when role is selected', () => {
    renderWithProvider(
      <AppShell>
        <div>Test Content</div>
      </AppShell>
    );

    // Mock role selection
    fireEvent.click(screen.getByText('Select Planner'));

    expect(screen.getByText('Planner')).toBeInTheDocument();
  });

  test('toggles dark mode correctly', () => {
    renderWithProvider(
      <AppShell>
        <div>Test Content</div>
      </AppShell>
    );

    const darkModeToggle = screen.getByLabelText('Toggle dark mode');
    fireEvent.click(darkModeToggle);

    expect(document.documentElement).toHaveClass('dark');
  });

  test('opens mobile menu on small screens', () => {
    // Mock mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    renderWithProvider(
      <AppShell>
        <div>Test Content</div>
      </AppShell>
    );

    const menuButton = screen.getByLabelText('Open menu');
    expect(menuButton).toBeInTheDocument();

    fireEvent.click(menuButton);
    expect(screen.getByText('Risk Map')).toBeInTheDocument();
  });
});
```

### Custom Hook Tests

```typescript
// tests/unit/hooks/useAppContext.test.tsx
import { renderHook, act } from '@testing-library/react';
import { useAppContext } from '@/contexts/AppContext';
import { AppProvider } from '@/contexts/AppContext';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AppProvider>{children}</AppProvider>
);

describe('useAppContext Hook', () => {
  test('provides initial state', () => {
    const { result } = renderHook(() => useAppContext(), { wrapper });

    expect(result.current.currentRole).toBeNull();
    expect(result.current.darkMode).toBe(false);
  });

  test('updates role correctly', () => {
    const { result } = renderHook(() => useAppContext(), { wrapper });

    act(() => {
      result.current.setCurrentRole('Planner');
    });

    expect(result.current.currentRole).toBe('Planner');
  });

  test('toggles dark mode', () => {
    const { result } = renderHook(() => useAppContext(), { wrapper });

    act(() => {
      result.current.setDarkMode(true);
    });

    expect(result.current.darkMode).toBe(true);
  });

  test('persists state to localStorage', () => {
    const { result } = renderHook(() => useAppContext(), { wrapper });

    act(() => {
      result.current.setCurrentRole('Administrator');
      result.current.setDarkMode(true);
    });

    expect(localStorage.getItem('flood-prediction-role')).toBe('Administrator');
    expect(localStorage.getItem('flood-prediction-dark-mode')).toBe('true');
  });
});
```

## Integration Testing

### API Integration Tests

```typescript
// tests/integration/api.spec.ts
import { test, expect } from '@playwright/test';

test.describe('API Integration Tests', () => {
  test('loads and displays zones data', async ({ page }) => {
    await page.goto('/planner/map');

    // Wait for API calls to complete
    await page.waitForLoadState('networkidle');

    // Check if zones are loaded (mock data verification)
    const zones = await page.evaluate(() => {
      return fetch('/api/zones').then(res => res.json());
    });

    expect(zones).toBeDefined();
    expect(zones.features).toBeDefined();
    expect(zones.features.length).toBeGreaterThan(0);
  });

  test('handles API errors gracefully', async ({ page }) => {
    // Simulated API failure
    await page.route('/api/zones', route => route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Internal server error' })
    }));

    await page.goto('/planner/map');

    // Should show error state
    await expect(page.getByText(/error/i)).toBeVisible();
  });

  test('caches API responses', async ({ page }) => {
    await page.goto('/planner/map');

    // First request
    const firstRequest = await page.waitForResponse('/api/zones');

    // Navigate away and back
    await page.goto('/planner/alerts');
    await page.goBack();

    // Should use cached response (no new request)
    const requests = [];
    page.on('response', response => {
      if (response.url().includes('/api/zones')) {
        requests.push(response);
      }
    });

    await page.waitForTimeout(1000);

    // Should not have made additional requests
    expect(requests.length).toBe(0);
  });
});
```

## Performance Testing

### Performance Metrics

```typescript
// tests/e2e/performance.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Performance Tests', () => {
  test('meets Core Web Vitals thresholds', async ({ page }) => {
    await page.goto('/');

    // Measure Largest Contentful Paint (LCP)
    const lcp = await page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          resolve(lastEntry.startTime);
        }).observe({ entryTypes: ['largest-contentful-paint'] });
      });
    });

    expect(lcp).toBeLessThan(2500); // LCP should be under 2.5s

    // Measure First Input Delay (FID)
    const fid = await page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const firstEntry = entries[0];
          resolve(firstEntry.processingStart - firstEntry.startTime);
        }).observe({ entryTypes: ['first-input'] });
      });
    });

    expect(fid).toBeLessThan(100); // FID should be under 100ms

    // Measure Cumulative Layout Shift (CLS)
    const cls = await page.evaluate(() => {
      return new Promise((resolve) => {
        let clsValue = 0;
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          }
          resolve(clsValue);
        }).observe({ entryTypes: ['layout-shift'] });
      });
    });

    expect(cls).toBeLessThan(0.1); // CLS should be under 0.1
  });

  test('bundle size optimization', async ({ page }) => {
    const responses: any[] = [];

    page.on('response', async (response) => {
      const url = response.url();
      if (url.endsWith('.js') || url.endsWith('.css')) {
        const headers = await response.allHeaders();
        const contentLength = headers['content-length'];
        if (contentLength) {
          responses.push({ url, size: parseInt(contentLength) });
        }
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const totalJSSize = responses
      .filter(r => r.url.endsWith('.js'))
      .reduce((sum, r) => sum + r.size, 0);

    // Main JavaScript bundle should be under 500KB gzipped
    expect(totalJSSize).toBeLessThan(500 * 1024);
  });

  test('interaction performance', async ({ page }) => {
    await page.goto('/');

    // Measure role switching performance
    const startTime = Date.now();

    await page.click('text=Select Planner');
    await page.waitForURL(/\\/planner\\//);

    const responseTime = Date.now() - startTime;

    // Role switching should be under 1 second
    expect(responseTime).toBeLessThan(1000);
  });
});
```

## Accessibility Testing

### Accessibility Tests

```typescript
// tests/e2e/accessibility.spec.ts
import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await injectAxe(page);
  });

  test('role selector page meets WCAG AA standards', async ({ page }) => {
    await checkA11y(page);
  });

  test('planner interface accessibility', async ({ page }) => {
    await page.click('text=Select Planner');
    await page.waitForURL(/\\/planner\\//);

    await checkA11y(page);
  });

  test('keyboard navigation works properly', async ({ page }) => {
    await page.goto('/');

    // Tab through all interactive elements
    const focusableElements = await page.$$('[tabindex]:not([tabindex="-1"]), button, input, select, textarea');

    for (const element of focusableElements) {
      await element.focus();
      const focusedElement = await page.locator(':focus');
      expect(await focusedElement.count()).toBe(1);
    }
  });

  test('screen reader landmarks are present', async ({ page }) => {
    await page.click('text=Select Planner');

    // Check for proper ARIA landmarks
    const main = await page.locator('main[role="main"]');
    const navigation = await page.locator('nav[role="navigation"]');
    const header = await page.locator('header[role="banner"]');

    expect(await main.count()).toBe(1);
    expect(await navigation.count()).toBe(1);
    expect(await header.count()).toBe(1);
  });

  test('color contrast meets standards', async ({ page }) => {
    await page.goto('/');

    // This would require additional color contrast testing setup
    // Using axe-playwright's color-contrast rule
    await checkA11y(page, undefined, {
      rules: {
        'color-contrast': { enabled: true }
      }
    });
  });
});
```

## Visual Regression Testing

### Visual Tests

```typescript
// tests/e2e/visual.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Visual Regression Tests', () => {
  test('role selector page visual consistency', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveScreenshot('role-selector.png');
  });

  test('planner dashboard visual consistency', async ({ page }) => {
    await page.goto('/planner/map');
    await expect(page).toHaveScreenshot('planner-dashboard.png');
  });

  test('dark mode visual consistency', async ({ page }) => {
    await page.goto('/planner/map');

    // Enable dark mode
    const darkModeToggle = page.getByLabel('Toggle dark mode');
    await darkModeToggle.click();

    await expect(page).toHaveScreenshot('planner-dashboard-dark.png');
  });

  test('mobile layout visual consistency', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    await expect(page).toHaveScreenshot('role-selector-mobile.png');
  });
});
```

## Test Data Management

### Mock Data Generation

```typescript
// tests/utils/dataGenerators.ts
export const generateMockZone = (overrides = {}) => ({
  type: 'Feature',
  properties: {
    id: `zone-${Math.random().toString(36).substr(2, 9)}`,
    name: `Test Zone ${Math.floor(Math.random() * 1000)}`,
    population: Math.floor(Math.random() * 10000),
    area: Math.random() * 100,
    ...overrides,
  },
  geometry: {
    type: 'Polygon',
    coordinates: [[
      [Math.random() * 10, Math.random() * 10],
      [Math.random() * 10, Math.random() * 10],
      [Math.random() * 10, Math.random() * 10],
      [Math.random() * 10, Math.random() * 10],
    ]],
  },
});

export const generateMockRiskData = (zoneId: string, overrides = {}) => ({
  zoneId,
  timestamp: new Date().toISOString(),
  risk: Math.random(),
  drivers: [
    {
      factor: 'rainfall',
      value: Math.random() * 100,
      weight: 0.5,
    },
    {
      factor: 'river_level',
      value: Math.random() * 10,
      weight: 0.3,
    },
  ],
  ...overrides,
});
```

### Test Fixtures

```typescript
// tests/fixtures/mockData.ts
export const mockZones = {
  features: [
    {
      type: 'Feature',
      properties: {
        id: 'zone-1',
        name: 'Downtown',
        population: 5000,
        area: 25.5,
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]],
      },
    },
    // ... more zones
  ],
};

export const mockRiskData = {
  timestamp: '2025-01-12T12:00:00Z',
  points: [
    {
      zoneId: 'zone-1',
      risk: 0.75,
      drivers: [
        { factor: 'rainfall', value: 85, weight: 0.6 },
        { factor: 'river_level', value: 7.2, weight: 0.4 },
      ],
      thresholdBand: { name: 'High Risk', min: 0.5, max: 0.75 },
      etaHours: 6,
    },
    // ... more risk points
  ],
};
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    timeout-minutes: 60
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright Browsers
        run: npx playwright install --with-deps

      - name: Run unit tests
        run: npm run test:unit

      - name: Run integration tests
        run: npm run test:integration

      - name: Run E2E tests
        run: npm run test:e2e

      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30

      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: test-results/
          retention-days: 30
```

### Test Scripts

```json
// package.json
{
  "scripts": {
    "test": "playwright test",
    "test:unit": "vitest run",
    "test:integration": "playwright test tests/integration/",
    "test:e2e": "playwright test tests/e2e/",
    "test:accessibility": "playwright test tests/e2e/accessibility.spec.ts",
    "test:performance": "playwright test tests/e2e/performance.spec.ts",
    "test:visual": "playwright test tests/e2e/visual.spec.ts",
    "test:headed": "playwright test --headed",
    "test:debug": "playwright test --debug",
    "test:ui": "playwright test --ui",
    "test:report": "playwright show-report"
  }
}
```

## Best Practices

### Test Writing Guidelines

1. **Use Descriptive Test Names**: Tests should clearly describe what they're testing
2. **Test User Behavior**: Focus on user actions and outcomes, not implementation details
3. **Use Page Object Model**: Organize selectors and actions by page/component
4. **Avoid brittleness**: Use stable selectors and avoid reliance on timing
5. **Test in isolation**: Tests should not depend on each other

### Page Object Model

```typescript
// tests/pageObjects/RoleSelector.ts
export class RoleSelector {
  constructor(private page: Page) {}

  get administratorCard() {
    return this.page.getByRole('heading', { name: 'Administrator' });
  }

  get plannerCard() {
    return this.page.getByRole('heading', { name: 'Planner' });
  }

  async selectRole(role: string) {
    await this.page.click(`text=Select ${role}`);
  }

  async waitForNavigationToRole(role: string) {
    await this.page.waitForURL(new RegExp(`/${role.toLowerCase()}/`));
  }
}

// tests/pageObjects/AppShell.ts
export class AppShell {
  constructor(private page: Page) {}

  get darkModeToggle() {
    return this.page.getByLabel('Toggle dark mode');
  }

  get roleSwitcher() {
    return this.page.getByText('Planner').first(); // Current role badge
  }

  async toggleDarkMode() {
    await this.darkModeToggle.click();
  }

  async switchRole(role: string) {
    await this.roleSwitcher.click();
    await this.page.click(`text=${role}`);
  }
}
```

### Test Organization

```typescript
// tests/utils/testHelpers.ts
export const loginAsRole = async (page: Page, role: string) => {
  await page.goto('/');
  await page.click(`text=Select ${role}`);
  await page.waitForURL(new RegExp(`/${role.toLowerCase()}/`));
};

export const expectRoleLoaded = async (page: Page, role: string) => {
  await expect(page.getByText(role)).toBeVisible();
  await expect(page.getByText('Flood Prediction')).toBeVisible();
};

export const checkAccessibility = async (page: Page) => {
  await injectAxe(page);
  await checkA11y(page);
};
```

## Troubleshooting

### Common Test Issues

**Flaky Tests**:
```bash
# Increase timeout for slow operations
await expect(element).toBeVisible({ timeout: 10000 });

# Use waitForSelector instead of immediate assertions
await page.waitForSelector('.critical-element');

# Add explicit waits for API calls
await page.waitForResponse(response => response.url().includes('/api/zones'));
```

**Selector Issues**:
```typescript
// Use stable selectors
page.locator('[data-testid="role-selector"]') // Good
page.locator('div > span > button') // Bad

// Use accessible selectors
page.getByRole('button', { name: 'Select Planner' }) // Good
page.locator('button.select-planner') // Medium
page.locator('button:nth-child(2)') // Bad
```

**Browser Compatibility**:
```typescript
// Handle browser-specific differences
if (browserName === 'webkit') {
  // Safari-specific logic
}

// Use browser-agnostic APIs
await page.locator('input[type="date"]').fill('2025-01-12'); // Good
await page.evaluate(() => document.querySelector('input').value = 'date'); // Bad
```

### Debug Tools

```bash
# Run tests in headed mode for debugging
npm run test:headed

# Run single test
npx playwright test tests/e2e/e2e.spec.ts --grep "specific test name"

# Run with debugging
npx playwright test --debug

# Generate test report
npm run test:report
```

### Performance Debugging

```typescript
// Enable tracing for performance analysis
test.beforeEach(async ({ page }) => {
  await page.tracing.start({ screenshots: true, snapshots: true });
});

test.afterEach(async ({ page }) => {
  await page.tracing.stop({ path: `trace-${Date.now()}.zip` });
});
```

This comprehensive testing strategy ensures the Flood Prediction Frontend application is reliable, performant, and accessible across all supported browsers and devices. Regular execution of these tests helps maintain code quality and prevents regressions as the application evolves.
