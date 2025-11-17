
import { chromium } from 'playwright';
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Enable console logging
    page.on('console', msg => console.log('Console:', msg.type(), msg.text()));
    
    // Navigate to the application
    await page.goto('http://localhost:5173');
    
    // Select Administrator role
    await page.waitForSelector('button:has-text("Select Administrator")');
    await page.click('button:has-text("Select Administrator")');
    
    // Wait for navigation
    await page.waitForLoadState('networkidle');
    
    // Navigate to resources page
    await page.waitForSelector('text=Resources');
    await page.click('text=Resources');
    await page.waitForLoadState('networkidle');
    
    // Check what's actually on the page
    console.log('Page URL:', page.url());
    
    // Look for any error states
    const errorSelectors = [
      '.text-red-500',
      '.text-red-600',
      '.text-red-700',
      '.alert',
      '.error',
      '.error-message'
    ];
    
    for (const selector of errorSelectors) {
      const errors = await page.locator(selector).allTextContents();
      if (errors.length > 0) {
        console.log('Found errors with selector', selector, ':', errors);
      }
    }
    
    // Check for loading states
    const loadingSelectors = [
      '.animate-pulse',
      '.loading',
      '.spinner'
    ];
    
    for (const selector of loadingSelectors) {
      const loading = await page.locator(selector).count();
      if (loading > 0) {
        console.log('Found', loading, 'loading elements with selector', selector);
      }
    }
    
    // Check if any content is loading
    console.log('Page contains content:', await page.locator('.card').count());
    
    // Look for the specific h1
    const h1Text = await page.locator('h1').first().textContent();
    console.log('First h1 content:', h1Text);
    
    // Look for any h2 elements
    const h2Texts = await page.locator('h2').allTextContents();
    console.log('h2 contents:', h2Texts);
    
    // Look for any text content
    const bodyText = await page.locator('body').textContent();
    console.log('Body text contains Resource Management:', bodyText?.includes('Resource Management'));
    
    // Wait a bit more for content to load
    await page.waitForTimeout(2000);
    
    // Try again after waiting
    const h1TextAfterWait = await page.locator('h1').first().textContent();
    console.log('First h1 content after wait:', h1TextAfterWait);
    
    const bodyTextAfterWait = await page.locator('body').textContent();
    console.log('Body text contains Resource Management after wait:', bodyTextAfterWait?.includes('Resource Management'));
    
    if (bodyTextAfterWait?.includes('Resource Management')) {
      console.log('✅ Found Resource Management after waiting');
    } else {
      console.log('❌ Still no Resource Management found');
    }
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await browser.close();
  }
})();

