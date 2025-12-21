import { chromium } from '@playwright/test';

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Enable console logging
  page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
  page.on('pageerror', err => console.log('BROWSER ERROR:', err));

  console.log('1. Navigating to app...');
  await page.goto('http://localhost:3001');

  console.log('2. Logging in...');
  await page.fill('input[type="email"]', 'admin@nqhub.com');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button:has-text("Sign In")');

  console.log('3. Waiting for dashboard...');
  await page.waitForURL('**/dashboard', { timeout: 10000 });

  console.log('4. Navigating to Data Module...');
  await page.click('a:has-text("Data Module")');
  await page.waitForURL('**/data', { timeout: 10000 });

  console.log('5. Clicking Market State tab...');
  await page.click('button:has-text("Market State")');
  await page.waitForTimeout(1000);

  console.log('6. Filling form...');
  await page.fill('#gen-symbol', 'NQZ5');
  await page.fill('#start-time', '09:00');
  await page.fill('#end-time', '09:30');

  console.log('7. Taking screenshot BEFORE clicking Generate...');
  await page.screenshot({ path: '/tmp/before-generate.png' });

  console.log('8. Clicking Generate Snapshots...');
  await page.click('button:has-text("Generate Snapshots")');

  console.log('9. Waiting 1 second...');
  await page.waitForTimeout(1000);

  console.log('10. Taking screenshot AFTER clicking Generate...');
  await page.screenshot({ path: '/tmp/after-generate.png' });

  // Check if progress card exists
  const progressCard = await page.locator('text=Generating Snapshots...').count();
  console.log('11. Progress card found:', progressCard > 0 ? 'YES' : 'NO');

  if (progressCard > 0) {
    console.log('    ✓ Progress card is visible!');
  } else {
    console.log('    ✗ Progress card NOT found!');

    // Check what IS visible
    const html = await page.content();
    const bodyText = await page.locator('body').innerText();
    console.log('\n=== VISIBLE TEXT ===');
    console.log(bodyText.substring(0, 500));
  }

  console.log('\n12. Waiting 5 more seconds to see if anything appears...');
  await page.waitForTimeout(5000);

  console.log('13. Taking final screenshot...');
  await page.screenshot({ path: '/tmp/final.png' });

  // Check for success message
  const success = await page.locator('text=Generated').count();
  console.log('14. Success message found:', success > 0 ? 'YES' : 'NO');

  // Check for error message
  const error = await page.locator('.border-destructive').count();
  console.log('15. Error message found:', error > 0 ? 'YES' : 'NO');

  if (error > 0) {
    const errorText = await page.locator('.border-destructive').innerText();
    console.log('    Error:', errorText);
  }

  console.log('\nScreenshots saved to:');
  console.log('  /tmp/before-generate.png');
  console.log('  /tmp/after-generate.png');
  console.log('  /tmp/final.png');

  console.log('\nPress Ctrl+C to close browser...');
  await page.waitForTimeout(60000); // Wait 1 minute before closing

  await browser.close();
})();
