import { test, expect } from '@playwright/test';

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
      await page.click(`text=Select ${role}`);

      // Verify we're redirected to the correct role page
      await expect(page).toHaveURL(new RegExp(`/${role.toLowerCase()}/`));

      // Verify role badge is displayed
      await expect(page.locator('div').filter({ hasText: role }).first()).toBeVisible();

      // Verify app shell is loaded
      await expect(page.getByText('Flood Prediction')).toBeVisible();
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
    await page.click('text=Select Planner');

    // Open role switcher dropdown
    await page.click('text=Planner');

    // Switch to Coordinator role
    await page.click('text=Coordinator');

    // Verify role changed
    await expect(page).toHaveURL(/\/coordinator\//);
    await expect(page.getByText('Coordinator')).toBeVisible();
  });

  test('Navigation works for Planner role', async ({ page }) => {
    await page.click('text=Select Planner');

    // Test navigation to different planner pages
    await expect(page.getByText('Risk Map')).toBeVisible();

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
    await expect(page.getByText('Regions')).toBeVisible();

    await page.click('text=Thresholds');
    await expect(page.getByText('Threshold Configuration')).toBeVisible();

    await page.click('text=Resources');
    await expect(page.getByText('Resource Catalog')).toBeVisible();

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

    // Verify mobile menu toggle is visible
    const menuButton = page.getByLabel('Open menu');
    await expect(menuButton).toBeVisible();

    // Test mobile menu
    await menuButton.click();
    await expect(page.getByText('Risk Map')).toBeVisible();

    // Close menu
    await menuButton.click();
  });

  test('Logout functionality works', async ({ page }) => {
    await page.click('text=Select Planner');

    // Open role switcher
    await page.click('text=Planner');

    // Click logout
    await page.click('text=Logout');

    // Should return to role selector
    await expect(page).toHaveURL('/');
    await expect(page.getByText('Select your role to continue')).toBeVisible();
  });

  test('Direct URL navigation works', async ({ page }) => {
    // Test direct navigation to role pages
    await page.goto('/planner/map');
    await expect(page.getByText('Planner Risk Map')).toBeVisible();

    await page.goto('/coordinator/ops');
    await expect(page.getByText('Live Operations Board')).toBeVisible();

    await page.goto('/admin/regions');
    await expect(page.getByText('Regions Manager')).toBeVisible();

    await page.goto('/analyst/overview');
    await expect(page.getByText('Analytical Map')).toBeVisible();
  });

  test('Page content renders correctly', async ({ page }) => {
    // Test that placeholder content is rendered on all pages
    const testPages = [
      { url: '/planner/map', content: 'Map will be implemented here' },
      { url: '/planner/scenarios', content: 'Scenario tools will be implemented here' },
      { url: '/planner/alerts', content: 'Alerts timeline will be implemented here' },
      { url: '/coordinator/ops', content: 'Ops board will be implemented here' },
      { url: '/coordinator/resources', content: 'Resource allocation view will be implemented here' },
      { url: '/admin/regions', content: 'GeoJSON zone editor will be implemented here' },
      { url: '/admin/thresholds', content: 'Threshold configuration will be implemented here' },
      { url: '/admin/resources', content: 'Resource management will be implemented here' },
      { url: '/admin/users', content: 'User management will be implemented here' },
      { url: '/analyst/overview', content: 'Analytical layers will be implemented here' },
      { url: '/analyst/exports', content: 'Export functionality will be implemented here' },
    ];

    for (const { url, content } of testPages) {
      await page.goto(url);
      await expect(page.getByText(content)).toBeVisible();
    }
  });

  test('API integration test - verify mock API is accessible', async ({ page }) => {
    // Navigate to application
    await page.goto('/planner/map');

    // Check that the page can access mock data (no error messages)
    await expect(page.getByText('Planner Risk Map')).toBeVisible();

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

    // Continue tabbing through elements
    await page.keyboard.press('Tab');

    // Test Enter key selection
    await page.keyboard.press('Enter');

    // Should navigate to the selected role
    await expect(page).toHaveURL(/\/administrator\//);
  });

});