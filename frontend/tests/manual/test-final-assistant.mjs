/**
 * Final test: Open AssistantPanel and send message
 */
import { chromium } from 'playwright';

const BASE_URL = 'http://localhost:3001';

async function testFinal() {
  console.log('🧪 Final AssistantPanel Test\n');

  const browser = await chromium.launch({ headless: false, slowMo: 800 });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // 1. Login
    console.log('🔐 Logging in...');
    await page.goto(BASE_URL);
    await page.fill('input[type="email"]', 'admin@nqhub.com');
    await page.fill('input[type="password"]', 'admin_inicial_2024');
    await page.click('button:has-text("Login")');
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    console.log('   ✅ Login successful\n');

    await page.waitForTimeout(2000);

    // 2. Click Globe button in TopNavbar
    console.log('🌐 Clicking Globe button...');
    const globeButton = page.locator('button[aria-label="Toggle LLM"]').first();
    await globeButton.click();
    console.log('   ✅ Globe button clicked\n');

    await page.waitForTimeout(2000);

    // 3. Take screenshot
    await page.screenshot({ path: '/tmp/assistant-panel-final.png', fullPage: true });
    console.log('   📸 Screenshot: /tmp/assistant-panel-final.png\n');

    // 4. Check if AssistantPanel is visible
    const panelVisible = await page.locator('text=AI Assistant').isVisible().catch(() => false);
    console.log(`   ${panelVisible ? '✅' : '❌'} AssistantPanel visible: ${panelVisible}\n`);

    if (panelVisible) {
      // 5. Send a message
      console.log('💬 Sending message...');
      const textarea = page.locator('textarea[placeholder="Ask me anything..."]');
      await textarea.fill('What is the system status?');
      await page.locator('button:has-text("Send")').click();
      console.log('   ✅ Message sent\n');

      // 6. Wait for response
      console.log('⏳ Waiting for Claude response...');
      await page.waitForTimeout(5000);

      // 7. Final screenshot
      await page.screenshot({ path: '/tmp/assistant-chat-final.png', fullPage: true });
      console.log('   📸 Screenshot: /tmp/assistant-chat-final.png\n');

      console.log('✅ TEST COMPLETE!');
    } else {
      console.log('❌ AssistantPanel not found - check if it\'s enabled');
    }

  } catch (error) {
    console.log(`\n❌ ERROR: ${error.message}`);
    await page.screenshot({ path: '/tmp/assistant-error-final.png', fullPage: true });
  }

  await browser.close();
}

testFinal().catch(console.error);
