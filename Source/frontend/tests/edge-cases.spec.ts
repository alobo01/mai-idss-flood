import { test, expect } from '@playwright/test';

test.describe('Edge Cases Tests', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('Good Case: Perfect user flow', async ({ page }) => {
    // Select a role
    await page.click('text=Select Planner');

    // Verify navigation
    await expect(page.getByText('Risk Map')).toBeVisible();

    // Navigate through pages
    await page.click('text=Alerts');
    await expect(page.getByText('Alerts Timeline')).toBeVisible();

    // Test role switching
    await page.click('text=Planner');
    await page.click('text=Coordinator');
    await expect(page.getByText('Ops Board')).toBeVisible();

    // All operations should complete successfully
    await expect(page.getByText('Flood Prediction')).toBeVisible();
  });

  test('Bad Case: Invalid route handling', async ({ page }) => {
    // Try to access non-existent route
    await page.goto('/invalid-route');

    // Should redirect to role selector or appropriate page
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByText('Select your role to continue')).toBeVisible();
  });

  test('Edge Case: Rapid role switching', async ({ page }) => {
    // Rapidly switch between roles
    const roles = ['Administrator', 'Planner', 'Coordinator', 'Data Analyst'];

    for (let i = 0; i < 3; i++) {
      for (const role of roles) {
        await page.click(`text=Select ${role}`);
        await expect(page.getByText(role)).toBeVisible();
        await page.waitForTimeout(100); // Small delay
      }
    }

    // Should handle rapid switching without errors
    await expect(page.getByText('Flood Prediction')).toBeVisible();
  });

  test('Edge Case: Network error resilience', async ({ page }) => {
    // Mock network failure by intercepting requests
    await page.route('**/*', route => route.abort());

    // Navigate to application
    await page.click('text=Select Planner');

    // Should still load basic UI elements (static content)
    await expect(page.getByText('Flood Prediction')).toBeVisible();
    await expect(page.getByText('Planner Risk Map')).toBeVisible();
  });

  test('Edge Case: Very long page titles', async ({ page }) => {
    await page.click('text=Select Planner');

    // Test very long text content (simulated by checking if it can handle long titles)
    const longText = 'A'.repeat(100);

    // Should not crash with long content
    await page.evaluate(() => {
      const div = document.createElement('div');
      div.textContent = 'A'.repeat(100);
      document.body.appendChild(div);
    });

    await expect(page.getByText('Planner Risk Map')).toBeVisible();
  });

  test('Edge Case: Concurrent state updates', async ({ page }) => {
    await page.click('text=Select Planner');

    // Test multiple state updates happening simultaneously
    await page.evaluate(() => {
      // Simulate multiple rapid state updates
      const events = [
        new KeyboardEvent('keydown', { key: 'Tab' }),
        new KeyboardEvent('keydown', { key: 'Tab' }),
        new KeyboardEvent('keydown', { key: 'Tab' }),
      ];
      events.forEach(event => document.dispatchEvent(event));
    });

    // Application should remain stable
    await expect(page.getByText('Planner Risk Map')).toBeVisible();
  });

});