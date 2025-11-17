
import { chromium } from 'playwright';
(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    // Navigate to the application
    await page.goto('http://localhost:5173');
    
    // Select Administrator role
    await page.waitForSelector('text=Select Administrator');
    await page.click('button:has-text(Select Administrator)');
    
    // Wait for navigation
    await page.waitForLoadState('networkidle');
    
    // Navigate to resources page
    await page.waitForSelector('text=Resources');
    await page.click('text=Resources');
    await page.waitForLoadState('networkidle');
    
    // Try to find the heading with multiple strategies
    const resourceHeading = await page.getByRole('heading', { name: 'Resource Management' });
    const resourceText = await page.getByText('Resource Management');
    const resourceLocator = await page.locator('h1:has-text(Resource Management)');
    
    console.log('Resource Management heading exists:', await resourceHeading.isVisible());
    console.log('Resource Management text exists:', await resourceText.isVisible());
    console.log('Resource Management locator exists:', await resourceLocator.isVisible());
    
    // Get page title and URL
    console.log('Page URL:', page.url());
    console.log('Page title:', await page.title());
    
    // Get page content for debugging
    const pageContent = await page.content();
    console.log('Page content length:', pageContent.length);
    
    if (pageContent.includes('Resource Management')) {
      console.log('✅ Found Resource Management in page content');
    } else {
      console.log('❌ Resource Management not found in page content');
    }
    
    await page.click('text=Users');
    await page.waitForLoadState('networkidle');
    
    const userHeading = await page.getByRole('heading', { name: 'User Management' });
    console.log('User Management heading exists:', await userHeading.isVisible());
    
    if (pageContent.includes('User Management')) {
      console.log('✅ Found User Management in page content');
    } else {
      console.log('❌ User Management not found in page content');
    }
    
    // Look for any error messages or loading indicators
    const errorMessages = await page.locator('.text-red-500, .error, .alert-danger').allTextContents();
    if (errorMessages.length > 0) {
      console.log('Error messages found:', errorMessages);
    }
    
  } catch (error) {
    console.error('Error:', error);
  } finally {
    await browser.close();
  }
})();

