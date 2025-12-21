import { chromium } from '@playwright/test';

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 500 });
  const page = await browser.newPage();

  // Capture console logs
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('[Market State]')) {
      console.log('✓ BROWSER:', text);
    }
  });

  page.on('pageerror', err => console.log('✗ ERROR:', err.message));

  try {
    console.log('\n1. Navigating to app...');
    await page.goto('http://localhost:3001', { waitUntil: 'networkidle' });

    console.log('2. Logging in...');
    await page.fill('input[type="email"]', 'admin@nqhub.com');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button:has-text("Sign In")');
    await page.waitForURL('**/dashboard', { timeout: 10000 });

    console.log('3. Going to Data Module...');
    await page.click('a:has-text("Data Module")');
    await page.waitForURL('**/data', { timeout: 10000 });

    console.log('4. Clicking Market State tab...');
    await page.click('button:has-text("Market State")');
    await page.waitForTimeout(1000);

    console.log('5. Filling form...');
    await page.fill('#gen-symbol', 'NQZ5');
    await page.fill('#start-time', '09:00');
    await page.fill('#end-time', '09:30');

    console.log('6. Clicking Generate Snapshots...');
    await page.click('button:has-text("Generate Snapshots")');

    console.log('7. Waiting for progress card...');
    await page.waitForTimeout(2000);

    // Check if progress card exists
    const progressCard = page.locator('text=Generating Snapshots').or(page.locator('text=Processing'));
    const isVisible = await progressCard.isVisible();

    if (isVisible) {
      console.log('✓ SUCCESS: Progress card IS visible!');

      // Get the card content
      const cardText = await page.locator('[class*="bg-blue"]').innerText();
      console.log('\nProgress card content:');
      console.log(cardText);
    } else {
      console.log('✗ FAIL: Progress card NOT visible');

      // Check what's on screen
      const body = await page.locator('body').innerText();
      console.log('\nVisible text on page:');
      console.log(body.substring(0, 1000));
    }

    // Wait for completion
    console.log('\n8. Waiting for completion...');
    await page.waitForTimeout(5000);

    const success = await page.locator('text=Generated').isVisible();
    console.log(`Success message visible: ${success}`);

  } catch (err) {
    console.error('Test failed:', err.message);
  } finally {
    await browser.close();
  }
})();
