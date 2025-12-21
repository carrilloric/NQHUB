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

    console.log('2. Logging in with CORRECT password...');
    await page.fill('input[type="email"]', 'admin@nqhub.com');
    await page.fill('input[type="password"]', 'admin_inicial_2024');
    await page.click('button:has-text("Sign In")');
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    console.log('✓ LOGIN SUCCESSFUL!');

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

    console.log('6. Taking screenshot BEFORE clicking Generate...');
    await page.screenshot({ path: '/tmp/before-generate.png', fullPage: true });

    console.log('7. Clicking Generate Snapshots...');
    await page.click('button:has-text("Generate Snapshots")');

    console.log('8. Waiting 500ms for progress card to appear...');
    await page.waitForTimeout(500);

    console.log('9. Taking screenshot AFTER clicking (should show progress card)...');
    await page.screenshot({ path: '/tmp/after-generate-500ms.png', fullPage: true });

    // Check if progress card exists
    const progressCard = page.locator('text=Generating Snapshots').or(page.locator('text=Processing'));
    const isVisible = await progressCard.isVisible();

    if (isVisible) {
      console.log('\n✓✓✓ SUCCESS: Progress card IS visible! ✓✓✓');

      // Get the card content
      const cardText = await page.locator('.bg-blue-50, .bg-blue-950').first().innerText();
      console.log('\n=== Progress card content ===');
      console.log(cardText);
      console.log('============================\n');
    } else {
      console.log('\n✗✗✗ FAIL: Progress card NOT visible ✗✗✗');

      // Check what's on screen
      const body = await page.locator('body').innerText();
      console.log('\n=== Visible text on page ===');
      console.log(body.substring(0, 1000));
      console.log('============================\n');
    }

    // Wait a bit more to see if it completes
    console.log('10. Waiting 3 more seconds to observe progress...');
    await page.waitForTimeout(3000);

    console.log('11. Taking final screenshot...');
    await page.screenshot({ path: '/tmp/final.png', fullPage: true });

    const success = await page.locator('text=Generated').isVisible();
    console.log(`\n12. Success message visible: ${success ? 'YES ✓' : 'NO ✗'}`);

    // Check for error message
    const error = await page.locator('.border-destructive').count();
    if (error > 0) {
      const errorText = await page.locator('.border-destructive').innerText();
      console.log('    Error:', errorText);
    }

    console.log('\n=== Screenshots saved ===');
    console.log('  /tmp/before-generate.png');
    console.log('  /tmp/after-generate-500ms.png');
    console.log('  /tmp/final.png');
    console.log('=========================\n');

    console.log('Press Ctrl+C to close browser...');
    await page.waitForTimeout(30000); // Wait 30s before closing

  } catch (err) {
    console.error('\n✗ Test failed:', err.message);
    await page.screenshot({ path: '/tmp/error.png', fullPage: true });
  } finally {
    await browser.close();
  }
})();
