import { test, expect } from '@playwright/test';

const ADMIN_BASE_PATH = '/administrator';
const LEGACY_ADMIN_PATH = '/admin';

test.describe('Flood Prediction System - E2E Tests', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
  });

  test('Application loads and displays role selector', async ({ page }) => {
    await expect(page.getByText('Flood Prediction System')).toBeVisible();
    await expect(page.getByText('Select your role to continue')).toBeVisible();

    // Check all four role cards are present
    await expect(page.getByRole('heading', { name: 'Administrator' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Planner' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Coordinator' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Data Analyst' })).toBeVisible();
  });

  test('Role selection works for all roles', async ({ page, context }) => {
    // Test individual role selection in sequence
    const testRoleSelection = async (role: string) => {
      // Create a new context for each role test to ensure complete isolation
      const roleContext = await context.browser().newContext({
        ignoreHTTPSErrors: true,
        viewport: { width: 1280, height: 720 }
      });
      const rolePage = await roleContext.newPage();

      try {
        // Clear any existing storage and navigate fresh
        await rolePage.goto('/', { waitUntil: 'networkidle' });

        // Wait for role selector to be fully loaded
        await expect(rolePage.getByText('Select your role to continue')).toBeVisible({ timeout: 10000 });

        // Verify role cards are visible before clicking
        await expect(rolePage.getByRole('heading', { name: role })).toBeVisible();

        // Click the role selection button and wait for navigation
        await Promise.all([
          rolePage.waitForNavigation({ waitUntil: 'networkidle', timeout: 10000 }),
          rolePage.click(`button:has-text("Select ${role}")`)
        ]);

        // Additional wait for page to fully settle
        await rolePage.waitForTimeout(1000);

        // Verify we're redirected to the correct role page
        if (role === 'Data Analyst') {
          await expect(rolePage).toHaveURL(/\/analyst\//);
        } else if (role === 'Administrator') {
          await expect(rolePage).toHaveURL(/\/(admin|administrator)\//);
        } else {
          await expect(rolePage).toHaveURL(new RegExp(`/${role.toLowerCase()}/`));
        }

        // Verify role is displayed in the UI (more robust check)
        const roleElement = rolePage.locator('div').filter({ hasText: role }).first();
        await expect(roleElement).toBeVisible({ timeout: 5000 });

        // Verify app shell is loaded with proper content
        await expect(rolePage.getByRole('heading', { name: 'Flood Prediction' })).toBeVisible();

        // Verify page-specific content is loaded
        if (role === 'Planner') {
          await expect(rolePage.getByRole('link', { name: 'Risk Map' })).toBeVisible();
        } else if (role === 'Coordinator') {
          await expect(rolePage.getByText('Ops Board')).toBeVisible();
        } else if (role === 'Administrator') {
          await expect(rolePage.getByRole('link', { name: 'Regions' })).toBeVisible();
        } else if (role === 'Data Analyst') {
          await expect(rolePage.getByText('Overview')).toBeVisible();
        }

        console.log(`✓ ${role} role selection works correctly`);
      } catch (error) {
        console.error(`✗ ${role} role selection failed:`, error);
        throw error;
      } finally {
        await roleContext.close();
      }
    };

    // Test each role with a small delay between tests
    for (const role of ['Administrator', 'Planner', 'Coordinator', 'Data Analyst']) {
      await testRoleSelection(role);
      // Small delay between role tests to prevent any race conditions
      await page.waitForTimeout(500);
    }
  });

  test('Dark mode toggle works', async ({ page }) => {
    await page.click('text=Select Planner');

    // Find and click dark mode toggle
    const darkModeToggle = page.getByLabel('Toggle dark mode');
    await expect(darkModeToggle).toBeVisible();

    // Toggle dark mode on
    await darkModeToggle.click();
    await expect(page.locator('html')).toHaveClass(/dark/);

    // Toggle dark mode off
    await darkModeToggle.click();
    await expect(page.locator('html')).not.toHaveClass(/dark/);
  });

  test('Role switcher in header works', async ({ page }) => {
    // Wait for role selector to load
    await expect(page.getByText('Select your role to continue')).toBeVisible();

    await page.click('text=Select Planner');

    // Wait for the page to load and find the role switcher dropdown
    await page.waitForSelector('[data-state="closed"]', { timeout: 10000 });

    // Open role switcher dropdown (look for the dropdown trigger button)
    const roleSwitcherButton = page.locator('button').filter({ hasText: 'Planner' }).first();
    await expect(roleSwitcherButton).toBeVisible();
    await roleSwitcherButton.click();

    // Switch to Coordinator role
    await page.waitForSelector('text=Coordinator', { timeout: 10000 });
    await page.click('text=Coordinator');

    // Verify role changed
    await expect(page).toHaveURL(/\/coordinator\//);
    await expect(page.locator('div').filter({ hasText: 'Coordinator' }).first()).toBeVisible();
  });

  test('Navigation works for Planner role', async ({ page }) => {
    await page.click('text=Select Planner');

    // Test navigation to different planner pages
    await expect(page.getByRole('link', { name: 'Risk Map' })).toBeVisible();

    await page.click('text=Alerts');
    await expect(page.getByText('Alerts Timeline')).toBeVisible();

    await page.click('text=Scenarios');
    await expect(page.getByText('Scenario Workbench')).toBeVisible();

    await page.click('text=Risk Map');
    await expect(page.getByText('Planner Risk Map')).toBeVisible();
  });

  test('Navigation works for Coordinator role', async ({ page }) => {
    await page.click('text=Select Coordinator');

    // Test coordinator navigation
    await expect(page.getByText('Ops Board')).toBeVisible();

    await page.click('text=Resources');
    await expect(page.getByText('Resource Allocation')).toBeVisible();

    await page.click('text=Ops Board');
    await expect(page.getByText('Live Operations Board')).toBeVisible();
  });

  test('Navigation works for Administrator role', async ({ page }) => {
    await page.click('text=Select Administrator');

    // Test administrator navigation
    await expect(page.getByRole('link', { name: 'Regions' })).toBeVisible();

    await page.click('text=Thresholds');
    await expect(page.getByRole('heading', { name: 'Threshold Configuration' })).toBeVisible();

    await page.click('text=Resources');
    // Wait for page to load and check for either heading or text content
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    // Check for Resource Management content - try multiple selectors
    const resourceManagementVisible = await Promise.race([
      page.getByRole('heading', { name: 'Resource Management' }).isVisible().catch(() => false),
      page.getByText('Resource Management').isVisible().catch(() => false),
      page.locator('h1:has-text("Resource Management")').isVisible().catch(() => false),
    ]);
    expect(resourceManagementVisible).toBe(true);

    await page.click('text=Users');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    // Check for User Management content - try multiple selectors
    const userManagementVisible = await Promise.race([
      page.getByRole('heading', { name: 'User Management' }).isVisible().catch(() => false),
      page.getByText('User Management').isVisible().catch(() => false),
      page.locator('h1:has-text("User Management")').isVisible().catch(() => false),
    ]);
    expect(userManagementVisible).toBe(true);

    await page.click('text=Regions');
    await expect(page.getByRole('heading', { name: 'Regions Manager' })).toBeVisible();
  });

  test('Navigation works for Data Analyst role', async ({ page }) => {
    await page.click('text=Select Data Analyst');

    // Test analyst navigation
    await expect(page.getByText('Overview')).toBeVisible();

    await page.click('text=Exports');
    await expect(page.getByText('Export Tools')).toBeVisible();

    await page.click('text=Overview');
    await expect(page.getByText('Analytical Map')).toBeVisible();
  });

  test('Mobile responsiveness works', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');

    // Verify mobile layout
    await expect(page.getByText('Flood Prediction System')).toBeVisible();

    // Select a role
    await page.click('text=Select Planner');
    await page.waitForLoadState('networkidle');

    // Verify mobile menu toggle is visible (use more specific selector)
    const menuButton = page.locator('button.md\\:hidden').first();
    await expect(menuButton).toBeVisible();

    // Test mobile menu - wait for menu to be fully open before interacting
    await menuButton.click();
    await page.waitForTimeout(300); // Wait for menu animation

    // Verify menu content is visible
    await expect(page.getByRole('link', { name: 'Risk Map' })).toBeVisible();

    // Try to click on a menu item to test it's not blocked
    const riskMapLink = page.getByRole('link', { name: 'Risk Map' });
    await riskMapLink.click();
    await page.waitForLoadState('networkidle');

    // Verify we navigated successfully and the page content loaded
    await expect(page.getByText('Planner Risk Map')).toBeVisible();

    // For the menu close test, click outside the menu area instead of the button
    // to avoid the overlay blocking issue
    const pageContent = page.locator('main').first();
    await pageContent.click();
    await page.waitForTimeout(300);

    // Verify menu can be opened again
    await menuButton.click();
    await page.waitForTimeout(300);

    // Verify menu is open by checking content is visible again
    await expect(page.getByRole('link', { name: 'Risk Map' })).toBeVisible();
  });

  test('Logout functionality works', async ({ page }) => {
    // Wait for role selector to load
    await expect(page.getByText('Select your role to continue')).toBeVisible();

    await page.click('text=Select Planner');

    // Wait for the page to load
    await page.waitForSelector('text=Planner', { timeout: 10000 });

    // Open role switcher dropdown
    const roleSwitcherButton = page.locator('button').filter({ hasText: 'Planner' }).first();
    await expect(roleSwitcherButton).toBeVisible();
    await roleSwitcherButton.click();

    // Click logout
    await page.waitForSelector('text=Logout', { timeout: 10000 });
    await page.click('text=Logout');

    // Should return to role selector
    await expect(page).toHaveURL('/');
    await expect(page.getByText('Select your role to continue')).toBeVisible();
  });

  test('Direct URL navigation works', async ({ page }) => {
    // Test direct navigation to role pages - need to select role first
    await page.goto('/');
    await expect(page.getByText('Select your role to continue')).toBeVisible({ timeout: 10000 });

    // Select Planner role first
    await page.click('text=Select Planner');
    await page.waitForLoadState('networkidle');

    // Now navigate to planner pages
    await page.goto('/planner/map');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Planner Risk Map' })).toBeVisible({ timeout: 10000 });

    // Select Coordinator role
    const roleSwitcherButton = page.locator('button').filter({ hasText: 'Planner' }).first();
    await roleSwitcherButton.click();
    await page.waitForSelector('text=Coordinator', { timeout: 10000 });
    await page.click('text=Coordinator');
    await page.waitForLoadState('networkidle');

    // Navigate to coordinator pages
    await page.goto('/coordinator/ops');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Live Operations Board')).toBeVisible({ timeout: 10000 });

    // Select Administrator role
    const roleSwitcherButton2 = page.locator('button').filter({ hasText: 'Coordinator' }).first();
    await roleSwitcherButton2.click();
    await page.waitForSelector('text=Administrator', { timeout: 10000 });
    await page.click('text=Administrator');
    await page.waitForLoadState('networkidle');

    // Navigate to admin pages
    await page.goto(`${ADMIN_BASE_PATH}/regions`);
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Regions Manager' })).toBeVisible({ timeout: 10000 });

    // Select Data Analyst role
    const roleSwitcherButton3 = page.locator('button').filter({ hasText: 'Administrator' }).first();
    await roleSwitcherButton3.click();
    await page.waitForSelector('text=Data Analyst', { timeout: 10000 });
    await page.click('text=Data Analyst');
    await page.waitForLoadState('networkidle');

    // Navigate to analyst pages
    await page.goto('/analyst/overview');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Analytical Map')).toBeVisible({ timeout: 10000 });
  });

  test('Legacy admin URLs work (admin paths are supported)', async ({ page }) => {
    // Set administrator role in localStorage to bypass role selector
    await page.addInitScript(() => {
      localStorage.setItem('flood-prediction-role', 'Administrator');
    });

    // Both /admin and /administrator paths should work
    await page.goto(`${LEGACY_ADMIN_PATH}/regions`);
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Regions Manager' })).toBeVisible({ timeout: 10000 });

    await page.goto(`${LEGACY_ADMIN_PATH}/thresholds`);
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Threshold Configuration' })).toBeVisible({ timeout: 10000 });
  });

  test('Page content renders correctly', async ({ page }) => {
    // Test that actual content is rendered on all pages

    // Test Planner pages
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.setItem('flood-prediction-role', 'Planner');
    });
    await page.goto('/');

    const plannerPages = [
      { url: '/planner/map', content: 'Planner Risk Map' },
      { url: '/planner/scenarios', content: 'Scenario Workbench' },
      { url: '/planner/alerts', content: 'Alerts Timeline' },
    ];

    for (const { url, content } of plannerPages) {
      await page.goto(url);
      await page.waitForLoadState('networkidle');
      await expect(page.getByRole('heading', { name: content })).toBeVisible({ timeout: 10000 });
    }

    // Test Coordinator pages
    await page.evaluate(() => {
      localStorage.setItem('flood-prediction-role', 'Coordinator');
    });
    await page.goto('/');

    const coordinatorPages = [
      { url: '/coordinator/ops', content: 'Live Operations Board' },
      { url: '/coordinator/resources', content: 'Resource Allocation' },
    ];

    for (const { url, content } of coordinatorPages) {
      await page.goto(url);
      await page.waitForLoadState('networkidle');
      await expect(page.getByRole('heading', { name: content })).toBeVisible({ timeout: 10000 });
    }

    // Test Administrator pages
    await page.evaluate(() => {
      localStorage.setItem('flood-prediction-role', 'Administrator');
    });
    await page.goto('/');

    const adminPages = [
      { url: `${ADMIN_BASE_PATH}/regions`, content: 'Regions Manager' },
      { url: `${ADMIN_BASE_PATH}/thresholds`, content: 'Threshold Configuration' },
      { url: `${ADMIN_BASE_PATH}/resources`, content: 'Resource Management' },
      { url: `${ADMIN_BASE_PATH}/users`, content: 'User Management' },
    ];

    for (const { url, content } of adminPages) {
      await page.goto(url);
      await page.waitForLoadState('networkidle');
      await expect(page.getByRole('heading', { name: content })).toBeVisible({ timeout: 10000 });
    }

    // Test Data Analyst pages
    await page.evaluate(() => {
      localStorage.setItem('flood-prediction-role', 'Data Analyst');
    });
    await page.goto('/');

    const analystPages = [
      { url: '/analyst/overview', content: 'Analytical Map' },
      { url: '/analyst/exports', content: 'Export Tools' },
    ];

    for (const { url, content } of analystPages) {
      await page.goto(url);
      await page.waitForLoadState('networkidle');
      await expect(page.getByRole('heading', { name: content })).toBeVisible({ timeout: 10000 });
    }
  });

  test('API integration test - verify mock API is accessible', async ({ page }) => {
    // Set planner role in localStorage to bypass role selector
    await page.addInitScript(() => {
      localStorage.setItem('flood-prediction-role', 'Planner');
    });

    // Navigate to application
    await page.goto('/planner/map');
    await page.waitForLoadState('networkidle');

    // Check that the page can access mock data (no error messages)
    await expect(page.getByRole('heading', { name: 'Planner Risk Map' })).toBeVisible({ timeout: 10000 });

    // Verify the page loads without API errors
    const consoleLogs = [];
    page.on('console', msg => {
      if (msg.type() === 'error') consoleLogs.push(msg.text());
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify no critical API errors
    const apiErrors = consoleLogs.filter(log => log.includes('404') || log.includes('fetch error'));
    expect(apiErrors).toHaveLength(0);
  });

  test('Keyboard navigation works', async ({ page }) => {
    await page.goto('/');

    // Test keyboard navigation through role selector
    await page.keyboard.press('Tab');

    // Should focus on first role card button
    const firstRoleButton = page.locator('button').filter({ hasText: 'Select Administrator' }).first();
    await expect(firstRoleButton).toBeFocused();

    // Test Enter key selection directly (without extra tab)
    await page.keyboard.press('Enter');

    // Should navigate to an administrator path (either /admin or /administrator)
    await expect(page).toHaveURL(/\/(admin|administrator)\//);
  });

});
