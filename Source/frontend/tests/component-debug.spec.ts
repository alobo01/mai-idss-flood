import { test, expect } from '@playwright/test';

const PLANNER_ONLY = process.env.PLANNER_ONLY === 'true';
if (PLANNER_ONLY) {
  test.skip();
}

test.describe('Component Import Debug Tests', () => {
  test('Check if AdminResources component can be imported', async ({ page }) => {
    // Set admin role
    await page.addInitScript(() => {
      localStorage.setItem('flood-prediction-role', 'Administrator');

      // Add console.log to capture component rendering
      window.addEventListener('load', () => {
        console.log('Page loaded');
      });
    });

    // Navigate to resources page
    await page.goto('/administrator/resources');

    // Listen for console messages
    const consoleMessages = [];
    page.on('console', msg => {
      consoleMessages.push(msg.type() + ': ' + msg.text());
    });

    // Listen for unhandled errors
    const errors = [];
    page.on('pageerror', error => {
      errors.push(error.message);
    });

    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000); // Extra time for React to render

    console.log('=== Console Messages ===');
    consoleMessages.forEach(msg => console.log(msg));

    console.log('=== JavaScript Errors ===');
    errors.forEach(error => console.log(error));

    // Check if the page contains ANY React content
    const reactContent = await page.locator('#root').textContent();
    console.log('Root content length:', reactContent?.length);
    console.log('Root content preview:', reactContent?.substring(0, 200));

    // Check for specific React error messages
    const hasReactError = consoleMessages.some(msg =>
      msg.includes('error') || msg.includes('Error') || msg.includes('failed')
    );

    if (hasReactError) {
      console.log('❌ React errors detected');
    }

    // Look for any loading indicators
    const loadingElements = await page.locator('text=Loading').all();
    console.log('Loading elements found:', loadingElements.length);
  });
});
