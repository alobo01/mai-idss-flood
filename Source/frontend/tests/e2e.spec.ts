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

  test('Role selection works for all roles', async ({ page }) => {
    const roles = ['Administrator', 'Planner', 'Coordinator', 'Data Analyst'];

    for (const role of roles) {
      await page.goto('/');

      // Wait for role selector to load
      await expect(page.getByText('Select your role to continue')).toBeVisible({ timeout: 10000 });

      // Wait for and click the role selection button
      await page.waitForSelector(`text=Select ${role}`, { timeout: 10000 });
      await page.click(`text=Select ${role}`);

      // Wait for navigation to complete and page to load
      await page.waitForLoadState('networkidle');

      // Verify we're redirected to the correct role page (handle Data Analyst special case)
      if (role === 'Data Analyst') {
        await expect(page).toHaveURL(/\/analyst\//);
      } else if (role === 'Administrator') {
        await expect(page).toHaveURL(/\/(admin|administrator)\//);
      } else {
        await expect(page).toHaveURL(new RegExp(`/${role.toLowerCase()}/`));
      }

      // Verify role badge is displayed
      await expect(page.locator('div').filter({ hasText: role }).first()).toBeVisible();

      // Verify app shell is loaded
      await expect(page.getByRole('heading', { name: 'Flood Prediction' })).toBeVisible();
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
    await expect(page.getByText('Resource Management')).toBeVisible();

    await page.click('text=Users');
    await expect(page.getByText('User Management')).toBeVisible();

    await page.click('text=Regions');
    await expect(page.getByText('Regions Manager')).toBeVisible();
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

    // Verify mobile menu toggle is visible (use the button with Menu icon)
    const menuButton = page.locator('button').filter({ has: page.locator('svg') }).first();
    await expect(menuButton).toBeVisible();

    // Test mobile menu
    await menuButton.click();
    await expect(page.getByRole('link', { name: 'Risk Map' })).toBeVisible();

    // Close menu
    await menuButton.click();
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
    // Test direct navigation to role pages
    await page.goto('/planner/map');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Planner Risk Map' })).toBeVisible({ timeout: 10000 });

    await page.goto('/coordinator/ops');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Live Operations Board')).toBeVisible({ timeout: 10000 });

    await page.goto(`${ADMIN_BASE_PATH}/regions`);
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('heading', { name: 'Regions Manager' })).toBeVisible({ timeout: 10000 });

    await page.goto('/analyst/overview');
    await page.waitForLoadState('networkidle');
    await expect(page.getByText('Analytical Map')).toBeVisible({ timeout: 10000 });
  });

  test('Legacy admin URLs work (admin paths are supported)', async ({ page }) => {
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
    const testPages = [
      { url: '/planner/map', content: 'Planner Risk Map' },
      { url: '/planner/scenarios', content: 'Scenario planning tools will be implemented here' },
      { url: '/planner/alerts', content: 'Alerts Timeline' },
      { url: '/coordinator/ops', content: 'Live Operations Board' },
      { url: '/coordinator/resources', content: 'Resource Allocation' },
      { url: `${ADMIN_BASE_PATH}/regions`, content: 'Regions Manager' },
      { url: `${ADMIN_BASE_PATH}/thresholds`, content: 'Threshold Configuration' },
      { url: `${ADMIN_BASE_PATH}/resources`, content: 'Resource Management' },
      { url: `${ADMIN_BASE_PATH}/users`, content: 'User Management' },
      { url: '/analyst/overview', content: 'Analytical Map' },
      { url: '/analyst/exports', content: 'Export Tools' },
    ];

    for (const { url, content } of testPages) {
      await page.goto(url);
      await page.waitForLoadState('networkidle');
      await expect(page.getByRole('heading', { name: content })).toBeVisible({ timeout: 10000 });
    }
  });

  test('API integration test - verify mock API is accessible', async ({ page }) => {
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
