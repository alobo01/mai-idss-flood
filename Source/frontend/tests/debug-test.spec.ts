import { test, expect } from '@playwright/test';

test.describe('Debug Test', () => {
  test('Check if pages are loading at all', async ({ page }) => {
    // Set up console error listener
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('Console error:', msg.text());
      }
    });

    // Go to root first
    await page.goto('/');
    await page.waitForTimeout(3000);

    // Check if we can see the role selector
    const roleSelector = await page.locator('body').textContent();
    console.log('Root page contains "role":', roleSelector?.toLowerCase().includes('role'));

    // Take a screenshot of root page
    await page.screenshot({ path: 'debug-root.png' });

    // Now try to go to planner map
    await page.goto('/planner/map');
    await page.waitForTimeout(5000);

    // Take a screenshot of planner map
    await page.screenshot({ path: 'debug-planner-map.png' });

    // Check page title
    const title = await page.title();
    console.log('Page title:', title);

    // Check for any text content
    const bodyText = await page.locator('body').textContent();
    console.log('Body text length:', bodyText?.length);
    console.log('Body contains "Flood":', bodyText?.includes('Flood'));
  });
});