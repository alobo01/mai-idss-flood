import { test, expect } from '@playwright/test';

test.describe('Administrator Page Debug Tests', () => {
  test('Debug what AdminResources actually renders', async ({ page }) => {
    // Set admin role
    await page.addInitScript(() => {
      localStorage.setItem('flood-prediction-role', 'Administrator');
    });

    // Navigate to resources page
    await page.goto('/administrator/resources');
    await page.waitForLoadState('networkidle');

    console.log('=== AdminResources Page Debug ===');

    // Check URL
    console.log('Current URL:', page.url());

    // Wait a bit for any async content
    await page.waitForTimeout(2000);

    // Check for ANY text content
    const bodyText = await page.locator('body').textContent();
    console.log('Body text length:', bodyText?.length);

    // Look for specific expected content
    const expectedTexts = [
      'Resource Management',
      'Resource Management',
      'Depots',
      'Equipment',
      'Crews',
      'Manage depots',
      'Manage equipment',
      'Manage crews'
    ];

    for (const text of expectedTexts) {
      const found = bodyText?.includes(text);
      console.log(`"${text}": ${found ? '✓' : '✗'}`);
    }

    // Check for ANY h1-h3 elements
    const headings = await page.locator('h1, h2, h3').all();
    console.log('Total headings found:', headings.length);

    for (let i = 0; i < headings.length; i++) {
      const text = await headings[i].textContent();
      const tag = await headings[i].evaluate(el => el.tagName);
      console.log(`${tag} ${i}: "${text}"`);
    }

    // Check for any error messages
    const errorElements = await page.locator('[data-testid="error"], .error, [role="alert"]').all();
    if (errorElements.length > 0) {
      console.log('Found error elements:');
      for (let i = 0; i < errorElements.length; i++) {
        const text = await errorElements[i].textContent();
        console.log(`Error ${i}: "${text}"`);
      }
    }

    // Check for loading states
    const loadingElements = await page.locator('[data-testid="loading"], .loading').all();
    console.log('Found loading elements:', loadingElements.length);

    // Check network requests
    const responses = [];
    page.on('response', response => {
      if (response.url().includes('/api/')) {
        responses.push({
          url: response.url(),
          status: response.status(),
          ok: response.ok()
        });
      }
    });

    await page.waitForTimeout(1000);

    console.log('API responses observed:', responses);
  });

  test('Debug what AdminUsers actually renders', async ({ page }) => {
    // Set admin role
    await page.addInitScript(() => {
      localStorage.setItem('flood-prediction-role', 'Administrator');
    });

    // Navigate to users page
    await page.goto('/administrator/users');
    await page.waitForLoadState('networkidle');

    console.log('=== AdminUsers Page Debug ===');

    // Wait for content
    await page.waitForTimeout(2000);

    // Look for specific expected content
    const bodyText = await page.locator('body').textContent();

    const expectedTexts = [
      'User Management',
      'Total Users',
      'Active Users',
      'Administrator',
      'Manage system users'
    ];

    for (const text of expectedTexts) {
      const found = bodyText?.includes(text);
      console.log(`"${text}": ${found ? '✓' : '✗'}`);
    }

    // Check headings
    const headings = await page.locator('h1').all();
    console.log('H1 headings found:', headings.length);
    for (let i = 0; i < headings.length; i++) {
      const text = await headings[i].textContent();
      console.log(`H1 ${i}: "${text}"`);
    }
  });
});