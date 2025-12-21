/**
 * Test AssistantPanel with authentication
 * 1. Login as admin
 * 2. Navigate to different pages
 * 3. Verify AssistantPanel exists
 * 4. Test chat functionality
 */
import { chromium } from 'playwright';

const BASE_URL = 'http://localhost:3001';

async function testAssistantWithAuth() {
  console.log('🧪 Testing AssistantPanel with Authentication...\n');

  const browser = await chromium.launch({ headless: false, slowMo: 500 });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Enable console logs
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log(`   ❌ Console Error: ${msg.text()}`);
    }
  });

  try {
    // Step 1: Login
    console.log('🔐 Step 1: Logging in...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });

    // Fill login form with correct credentials
    await page.fill('input[type="email"]', 'admin@nqhub.com');
    await page.fill('input[type="password"]', 'admin_inicial_2024');
    await page.click('button:has-text("Login")');  // Case-sensitive!

    // Wait for navigation to dashboard
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    console.log('   ✅ Login successful\n');

    // Step 2: Test Dashboard page
    console.log('📄 Step 2: Testing Dashboard...');
    await page.waitForTimeout(2000);

    // Look for AssistantPanel in DOM
    const assistantPanelExists = await page.locator('[class*="assistant"]').count() > 0;
    console.log(`   ${assistantPanelExists ? '✅' : '❌'} AssistantPanel in DOM: ${assistantPanelExists}`);

    // Look for Globe/Assistant button
    const globeButton = await page.locator('button[aria-label*="assistant"], button[aria-label*="LLM"], button:has-text("Assistant")').first();
    const globeVisible = await globeButton.isVisible().catch(() => false);
    console.log(`   ${globeVisible ? '✅' : '⚠️ '} Globe/Assistant button visible: ${globeVisible}`);

    if (globeVisible) {
      // Step 3: Open AssistantPanel
      console.log('\n🎯 Step 3: Opening AssistantPanel...');
      await globeButton.click();
      await page.waitForTimeout(1000);

      const panelOpen = await page.locator('[role="dialog"], [class*="sheet"]').isVisible().catch(() => false);
      console.log(`   ${panelOpen ? '✅' : '❌'} Panel opened: ${panelOpen}`);

      if (panelOpen) {
        // Step 4: Test chat
        console.log('\n💬 Step 4: Testing chat...');

        // Look for textarea/input
        const chatInput = await page.locator('textarea, input[placeholder*="message"], input[placeholder*="Message"]').first();
        const inputVisible = await chatInput.isVisible().catch(() => false);
        console.log(`   ${inputVisible ? '✅' : '❌'} Chat input visible: ${inputVisible}`);

        if (inputVisible) {
          await chatInput.fill('Hello, what is the ETL status?');
          await page.keyboard.press('Enter');

          console.log('   ⏳ Waiting for response...');
          await page.waitForTimeout(3000);

          const messages = await page.locator('[class*="message"]').count();
          console.log(`   ${messages > 0 ? '✅' : '❌'} Messages found: ${messages}`);
        }
      }
    }

    // Step 5: Take screenshots
    console.log('\n📸 Step 5: Taking screenshots...');
    await page.screenshot({ path: '/tmp/assistant-dashboard-authenticated.png', fullPage: true });
    console.log('   ✅ Screenshot saved: /tmp/assistant-dashboard-authenticated.png');

    // Step 6: Test other pages
    console.log('\n📄 Step 6: Testing other pages...');

    const testPages = [
      { name: 'Data Module', url: '/data' },
      { name: 'Statistical Analysis', url: '/statistical-analysis' },
    ];

    for (const testPage of testPages) {
      await page.goto(BASE_URL + testPage.url, { waitUntil: 'networkidle' });
      await page.waitForTimeout(1000);

      const panelExists = await page.locator('[class*="assistant"]').count() > 0;
      console.log(`   ${panelExists ? '✅' : '❌'} ${testPage.name}: Panel in DOM = ${panelExists}`);
    }

    console.log('\n' + '='.repeat(60));
    console.log('✅ TESTS COMPLETED!');
    console.log('='.repeat(60));

  } catch (error) {
    console.log(`\n❌ ERROR: ${error.message}`);
    await page.screenshot({ path: '/tmp/assistant-error.png', fullPage: true });
    console.log('   📸 Error screenshot saved: /tmp/assistant-error.png');
  }

  await browser.close();
}

testAssistantWithAuth().catch(console.error);
