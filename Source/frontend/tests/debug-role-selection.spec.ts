import { test, expect } from '@playwright/test';

const PLANNER_ONLY = process.env.PLANNER_ONLY === 'true';
if (PLANNER_ONLY) {
  test.skip();
}

test('Debug role selection', async ({ page }) => {
  // Navigate to the application
  await page.goto('/');

  // Wait for role selector to load
  await expect(page.getByText('Select your role to continue')).toBeVisible({ timeout: 10000 });

  // Check what role buttons are available
  const plannerButton = page.locator('button:has-text("Select Planner")');
  await expect(plannerButton).toBeVisible();

  // Check localStorage before clicking
  const storageBefore = await page.evaluate(() => {
    return {
      role: localStorage.getItem('flood-prediction-role'),
      all: Object.keys(localStorage)
    };
  });
  console.log('Storage before:', storageBefore);

  // Click the Planner role button
  await plannerButton.click();

  // Wait a bit for state to update
  await page.waitForTimeout(1000);

  // Check localStorage after clicking
  const storageAfter = await page.evaluate(() => {
    return {
      role: localStorage.getItem('flood-prediction-role'),
      all: Object.keys(localStorage)
    };
  });
  console.log('Storage after:', storageAfter);

  // Check current URL
  console.log('Current URL:', page.url());

  // Check if we can find any role-related content
  const roleBadge = page.locator('div').filter({ hasText: 'Planner' }).first();
  console.log('Role badge visible:', await roleBadge.isVisible());
});
