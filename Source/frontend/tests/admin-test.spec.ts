import { test, expect } from '@playwright/test';

const PLANNER_ONLY = process.env.PLANNER_ONLY === 'true';
if (PLANNER_ONLY) {
  test.skip();
}

test.describe('Admin Debug Test', () => {
  test('Check admin threshold page', async ({ page }) => {
    // Set admin role and navigate to threshold page
    await page.addInitScript(() => {
      localStorage.setItem('flood-prediction-role', 'Administrator');
    });

    // Navigate to admin thresholds page
    await page.goto('/administrator/thresholds');
    await page.waitForLoadState('networkidle');

    // Take screenshot
    await page.screenshot({ path: 'debug-admin-thresholds.png' });

    // Check what's actually on the page
    const bodyText = await page.locator('body').textContent();
    console.log('Page text length:', bodyText?.length);
    console.log('Page contains "Threshold":', bodyText?.includes('Threshold'));
    console.log('Page contains "Configuration":', bodyText?.includes('Configuration'));
    console.log('Page contains "Risk":', bodyText?.includes('Risk'));

    // Check for any h1-h3 elements
    const headings = await page.locator('h1, h2, h3').all();
    console.log('Found heading elements:', headings.length);
    for (let i = 0; i < Math.min(headings.length, 5); i++) {
      const text = await headings[i].textContent();
      console.log(`Heading ${i}:`, text);
    }

    // Check for error messages
    const hasError = bodyText?.includes('error') || bodyText?.includes('Error');
    console.log('Page contains error:', hasError);

    // Check for any tab or button elements
    const buttons = await page.locator('button, [role="tab"]').all();
    console.log('Found interactive elements:', buttons.length);
  });

  test('Check admin resources page', async ({ page }) => {
    // Set admin role and navigate to resources page
    await page.addInitScript(() => {
      localStorage.setItem('flood-prediction-role', 'Administrator');
    });

    await page.goto('/administrator/resources');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').textContent();
    console.log('Resources page text length:', bodyText?.length);
    console.log('Resources page contains "Resource":', bodyText?.includes('Resource'));
    console.log('Resources page contains "Management":', bodyText?.includes('Management'));
    console.log('Resources page contains "Depots":', bodyText?.includes('Depots'));
    console.log('Resources page contains "Equipment":', bodyText?.includes('Equipment'));
    console.log('Resources page contains "error":', bodyText?.includes('error'));

    const h1s = await page.locator('h1').all();
    console.log('Found h1 elements on resources page:', h1s.length);
    for (let i = 0; i < Math.min(h1s.length, 3); i++) {
      const text = await h1s[i].textContent();
      console.log(`H1 ${i}:`, text);
    }
  });

  test('Check admin users page', async ({ page }) => {
    // Set admin role and navigate to users page
    await page.addInitScript(() => {
      localStorage.setItem('flood-prediction-role', 'Administrator');
    });

    await page.goto('/administrator/users');
    await page.waitForLoadState('networkidle');

    const bodyText = await page.locator('body').textContent();
    console.log('Users page contains "User":', bodyText?.includes('User'));
    console.log('Users page contains "Management":', bodyText?.includes('Management'));

    const h1s = await page.locator('h1').all();
    console.log('Found h1 elements on users page:', h1s.length);
    for (let i = 0; i < Math.min(h1s.length, 3); i++) {
      const text = await h1s[i].textContent();
      console.log(`H1 ${i}:`, text);
    }
  });
});
